"""TTS cache utilities for AI Hub integration.

This module provides caching functionality for TTS responses
to improve performance and reduce API calls for repeated phrases.

Features:
- In-memory LRU cache
- Optional file-based persistence
- Cache statistics
- Automatic cleanup of expired entries
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Default cache settings
DEFAULT_MAX_CACHE_SIZE = 100  # Maximum number of entries
DEFAULT_TTL_SECONDS = 3600  # 1 hour TTL
DEFAULT_MAX_AUDIO_SIZE = 5 * 1024 * 1024  # 5MB max per audio file


@dataclass
class CacheEntry:
    """Represents a cached TTS entry.

    Attributes:
        audio_data: The cached audio bytes
        voice: Voice used for synthesis
        text_hash: Hash of the original text
        created_at: Timestamp when entry was created
        last_accessed: Timestamp of last access
        access_count: Number of times this entry was accessed
        size_bytes: Size of audio data in bytes
    """

    audio_data: bytes
    voice: str
    text_hash: str
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0

    def __post_init__(self) -> None:
        """Calculate size after initialization."""
        self.size_bytes = len(self.audio_data)

    def touch(self) -> None:
        """Update access time and count."""
        self.last_accessed = time.time()
        self.access_count += 1

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if this entry has expired."""
        return time.time() - self.created_at > ttl_seconds


@dataclass
class CacheStats:
    """Statistics for the TTS cache.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of evicted entries
        current_size: Current number of entries
        total_bytes: Total size of cached audio in bytes
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size: int = 0
    total_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate the cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "current_size": self.current_size,
            "total_bytes": self.total_bytes,
            "hit_rate": round(self.hit_rate * 100, 2),
        }


class TTSCache:
    """LRU cache for TTS audio responses.

    This cache stores synthesized audio to avoid repeated API calls
    for the same text with the same voice settings.

    Example:
        cache = TTSCache(max_size=100, ttl_seconds=3600)

        # Try to get from cache
        audio = cache.get("Hello world", "zh-CN-XiaoxiaoNeural")
        if audio is None:
            # Generate audio and store in cache
            audio = await generate_tts("Hello world", "zh-CN-XiaoxiaoNeural")
            cache.put("Hello world", "zh-CN-XiaoxiaoNeural", audio)
    """

    def __init__(
        self,
        max_size: int = DEFAULT_MAX_CACHE_SIZE,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_audio_size: int = DEFAULT_MAX_AUDIO_SIZE,
    ) -> None:
        """Initialize the TTS cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
            max_audio_size: Maximum size of a single audio file to cache
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._max_audio_size = max_audio_size
        self._stats = CacheStats()
        self._lock = asyncio.Lock()

    def _make_key(self, text: str, voice: str) -> str:
        """Create a cache key from text and voice.

        Args:
            text: The text to synthesize
            voice: The voice to use

        Returns:
            A unique cache key
        """
        # Use hash for the text to handle long strings
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"{voice}:{text_hash}"

    def get(self, text: str, voice: str) -> bytes | None:
        """Get cached audio for the given text and voice.

        Args:
            text: The text that was synthesized
            voice: The voice that was used

        Returns:
            Cached audio bytes or None if not found/expired
        """
        key = self._make_key(text, voice)

        if key not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key]

        # Check if expired
        if entry.is_expired(self._ttl_seconds):
            self._remove(key)
            self._stats.misses += 1
            return None

        # Update access and move to end (most recently used)
        entry.touch()
        self._cache.move_to_end(key)
        self._stats.hits += 1

        _LOGGER.debug(
            "TTS cache hit for voice=%s, text_len=%d",
            voice,
            len(text),
        )

        return entry.audio_data

    def put(
        self,
        text: str,
        voice: str,
        audio_data: bytes,
    ) -> bool:
        """Store audio in the cache.

        Args:
            text: The text that was synthesized
            voice: The voice that was used
            audio_data: The synthesized audio bytes

        Returns:
            True if stored successfully, False if skipped
        """
        # Skip if audio is too large
        if len(audio_data) > self._max_audio_size:
            _LOGGER.debug(
                "Skipping cache for large audio: %d bytes",
                len(audio_data),
            )
            return False

        key = self._make_key(text, voice)

        # Remove oldest entries if at capacity
        while len(self._cache) >= self._max_size:
            self._evict_oldest()

        # Create and store entry
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        entry = CacheEntry(
            audio_data=audio_data,
            voice=voice,
            text_hash=text_hash,
        )

        self._cache[key] = entry
        self._update_stats()

        _LOGGER.debug(
            "TTS cached: voice=%s, text_len=%d, audio_size=%d",
            voice,
            len(text),
            len(audio_data),
        )

        return True

    def _remove(self, key: str) -> None:
        """Remove an entry from the cache."""
        if key in self._cache:
            del self._cache[key]
            self._update_stats()

    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) entry."""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1
            _LOGGER.debug("TTS cache evicted oldest entry")

    def _update_stats(self) -> None:
        """Update cache statistics."""
        self._stats.current_size = len(self._cache)
        self._stats.total_bytes = sum(
            entry.size_bytes for entry in self._cache.values()
        )

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._update_stats()
        _LOGGER.debug("TTS cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if entry.is_expired(self._ttl_seconds)
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._update_stats()
            _LOGGER.debug("TTS cache cleaned up %d expired entries", len(expired_keys))

        return len(expired_keys)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        self._update_stats()
        return self._stats

    @property
    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)


class PersistentTTSCache(TTSCache):
    """TTS cache with file-based persistence.

    This cache can save and load entries from disk for persistence
    across restarts.
    """

    def __init__(
        self,
        cache_dir: str | Path,
        **kwargs: Any,
    ) -> None:
        """Initialize the persistent cache.

        Args:
            cache_dir: Directory to store cached audio files
            **kwargs: Arguments for TTSCache
        """
        super().__init__(**kwargs)
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._cache_dir / "cache_index.json"

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a cache entry."""
        # Use a safe filename
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{safe_key}.mp3"

    async def async_save_to_disk(self, text: str, voice: str) -> bool:
        """Save a specific entry to disk.

        Args:
            text: The text that was synthesized
            voice: The voice that was used

        Returns:
            True if saved successfully
        """
        key = self._make_key(text, voice)

        if key not in self._cache:
            return False

        entry = self._cache[key]
        file_path = self._get_file_path(key)

        try:
            async with self._lock:
                await asyncio.to_thread(
                    file_path.write_bytes,
                    entry.audio_data,
                )
            _LOGGER.debug("TTS cache saved to disk: %s", file_path)
            return True
        except Exception as e:
            _LOGGER.warning("Failed to save TTS cache to disk: %s", e)
            return False

    async def async_load_from_disk(self, text: str, voice: str) -> bytes | None:
        """Load a specific entry from disk.

        Args:
            text: The text to look up
            voice: The voice to look up

        Returns:
            Audio bytes if found, None otherwise
        """
        key = self._make_key(text, voice)
        file_path = self._get_file_path(key)

        if not await asyncio.to_thread(file_path.exists):
            return None

        try:
            async with self._lock:
                audio_data = await asyncio.to_thread(file_path.read_bytes)

            # Also add to in-memory cache
            self.put(text, voice, audio_data)

            _LOGGER.debug("TTS cache loaded from disk: %s", file_path)
            return audio_data
        except Exception as e:
            _LOGGER.warning("Failed to load TTS cache from disk: %s", e)
            return None

    async def async_cleanup_disk(self, max_age_seconds: float = 86400) -> int:
        """Clean up old cache files from disk.

        Args:
            max_age_seconds: Maximum age of files to keep (default: 24 hours)

        Returns:
            Number of files removed
        """
        removed = 0
        current_time = time.time()

        try:
            for file_path in await asyncio.to_thread(_list_cache_files, self._cache_dir):
                try:
                    file_age = current_time - await asyncio.to_thread(
                        _get_file_mtime, file_path
                    )
                    if file_age > max_age_seconds:
                        await asyncio.to_thread(file_path.unlink)
                        removed += 1
                except Exception as e:
                    _LOGGER.debug("Failed to remove cache file %s: %s", file_path, e)

            if removed > 0:
                _LOGGER.debug("TTS disk cache cleaned up %d files", removed)

        except Exception as e:
            _LOGGER.warning("Failed to cleanup disk cache: %s", e)

        return removed


def _list_cache_files(cache_dir: Path) -> list[Path]:
    """List cache files synchronously."""
    return list(cache_dir.glob("*.mp3"))


def _get_file_mtime(file_path: Path) -> float:
    """Get file modification time synchronously."""
    return file_path.stat().st_mtime


# Global cache instance
_tts_cache: TTSCache | None = None


def get_tts_cache(
    max_size: int = DEFAULT_MAX_CACHE_SIZE,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> TTSCache:
    """Get or create the global TTS cache instance.

    Args:
        max_size: Maximum cache size
        ttl_seconds: TTL for cache entries

    Returns:
        TTSCache instance
    """
    global _tts_cache

    if _tts_cache is None:
        _tts_cache = TTSCache(max_size=max_size, ttl_seconds=ttl_seconds)
        _LOGGER.debug(
            "Created TTS cache: max_size=%d, ttl=%ds",
            max_size,
            ttl_seconds,
        )

    return _tts_cache
