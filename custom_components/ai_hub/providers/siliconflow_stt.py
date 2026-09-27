"""SiliconFlow STT provider implementation.

This module provides STT using SiliconFlow's free ASR service.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from ..consts import (
    SILICONFLOW_ASR_URL,
    SILICONFLOW_ROOT_URL,
    STT_DYNAMIC_TIMEOUT_BASE,
    STT_DYNAMIC_TIMEOUT_CONNECT,
    STT_DYNAMIC_TIMEOUT_MAX,
    STT_DYNAMIC_TIMEOUT_MIN_READ,
    STT_DYNAMIC_TIMEOUT_PER_100KB,
    STT_MAX_AUDIO_SIZE,
    STT_MIN_AUDIO_SIZE,
    TIMEOUT_HEALTH_CHECK,
)
from .base import ProviderType
from .stt_base import AudioMetadata, STTConfig, STTProvider, STTResult

_LOGGER = logging.getLogger(__name__)

# Supported models (verified stable with Chinese and English audio)
SILICONFLOW_STT_MODELS = [
    "Qwen/Qwen3-ASR-1.7B",
    "TeleAI/TeleSpeechASR",
    "XingChenAGI/XingChenASR-V3.2",
    "XingChenAGI/XingChenASR-V3.2-Ultra",
]

# Default model
DEFAULT_MODEL = "Qwen/Qwen3-ASR-1.7B"


def _create_wav_header(audio_data: bytes, metadata: AudioMetadata) -> bytes:
    """Create WAV header for raw PCM audio data."""
    sample_rate = metadata.sample_rate
    channels = metadata.channels
    bits_per_sample = metadata.bit_rate
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    wav_header = bytearray()
    # RIFF header
    wav_header.extend(b"RIFF")
    wav_header.extend((36 + len(audio_data)).to_bytes(4, "little"))
    wav_header.extend(b"WAVE")
    # fmt chunk
    wav_header.extend(b"fmt ")
    wav_header.extend((16).to_bytes(4, "little"))
    wav_header.extend((1).to_bytes(2, "little"))  # PCM format
    wav_header.extend(channels.to_bytes(2, "little"))
    wav_header.extend(sample_rate.to_bytes(4, "little"))
    wav_header.extend(byte_rate.to_bytes(4, "little"))
    wav_header.extend(block_align.to_bytes(2, "little"))
    wav_header.extend(bits_per_sample.to_bytes(2, "little"))
    # data chunk
    wav_header.extend(b"data")
    wav_header.extend(len(audio_data).to_bytes(4, "little"))

    return bytes(wav_header) + audio_data


def _calculate_timeout(audio_size_bytes: int) -> aiohttp.ClientTimeout:
    """Calculate dynamic timeout based on audio size."""
    audio_size_kb = audio_size_bytes / 1024
    calculated_timeout = STT_DYNAMIC_TIMEOUT_BASE + (audio_size_kb / 100) * STT_DYNAMIC_TIMEOUT_PER_100KB
    total_timeout = min(max(calculated_timeout, STT_DYNAMIC_TIMEOUT_BASE), STT_DYNAMIC_TIMEOUT_MAX)

    return aiohttp.ClientTimeout(
        total=total_timeout,
        connect=STT_DYNAMIC_TIMEOUT_CONNECT,
        sock_read=max(total_timeout * 0.8, STT_DYNAMIC_TIMEOUT_MIN_READ),
    )


def _extract_transcription(response_data: dict[str, Any]) -> str | None:
    """Extract transcription text from API response."""
    # OpenAI-style response
    if "text" in response_data:
        return response_data["text"]
    if "transcription" in response_data:
        return response_data["transcription"]

    # SiliconFlow API format
    if "code" in response_data:
        code = response_data.get("code")
        if code != 20000:
            return None
        data = response_data.get("data")
        if data:
            return data.get("text") or data.get("transcription")

    # Result field format
    if "result" in response_data:
        result = response_data["result"]
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        if isinstance(result, str):
            return result

    return None


class SiliconFlowSTTProvider(STTProvider):
    """SiliconFlow STT provider using their free ASR service.

    Features:
    - Free tier available
    - High accuracy for Chinese
    - Support for multiple languages
    - Multiple audio formats

    Example:
        config = STTConfig(
            api_key="your-api-key",
            model="FunAudioLLM/SenseVoiceSmall",
        )
        provider = SiliconFlowSTTProvider(config)

        result = await provider.transcribe(audio_data, metadata)
    """

    # Class-level attributes for registration
    _name = "siliconflow_stt"
    _provider_type = ProviderType.STT

    def __init__(self, config: STTConfig) -> None:
        """Initialize the provider."""
        super().__init__(config)
        self._session: aiohttp.ClientSession | None = None

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "siliconflow_stt"

    @property
    def display_name(self) -> str:
        """Return a human-readable display name."""
        return "SiliconFlow ASR"

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported language codes."""
        return [
            "zh-CN",
            "zh-TW",
            "zh-HK",
            "en-US",
            "ja-JP",
            "ko-KR",
            "fr-FR",
            "de-DE",
            "es-ES",
            "it-IT",
            "pt-BR",
            "ru-RU",
        ]

    @property
    def supported_formats(self) -> list[str]:
        """Return list of supported audio formats."""
        return ["wav", "mp3", "pcm", "opus", "webm"]

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported model identifiers."""
        return SILICONFLOW_STT_MODELS

    def _get_model(self) -> str:
        """Get the model to use."""
        model = self.config.model
        if model and model in SILICONFLOW_STT_MODELS:
            return model
        return DEFAULT_MODEL

    def _prepare_audio(
        self, audio_data: bytes, metadata: AudioMetadata
    ) -> bytes:
        """Prepare audio data for API request."""
        # Convert to WAV if needed
        if len(audio_data) < 12 or audio_data[:4] != b"RIFF":
            _LOGGER.debug("Converting raw PCM data to WAV format")
            return _create_wav_header(audio_data, metadata)
        return audio_data

    async def transcribe(
        self,
        audio_data: bytes,
        metadata: AudioMetadata,
        **kwargs: Any,
    ) -> STTResult:
        """Transcribe audio to text.

        Args:
            audio_data: Audio bytes to transcribe
            metadata: Audio metadata
            **kwargs: Additional parameters

        Returns:
            STTResult containing the transcribed text
        """
        # Validate API key
        if not self.config.api_key:
            raise ValueError("SiliconFlow API key not configured")

        # Validate audio
        is_valid, error = self.validate_audio(audio_data, metadata)
        if not is_valid:
            raise ValueError(error)

        # Check for very small audio (likely empty)
        if len(audio_data) < STT_MIN_AUDIO_SIZE:
            _LOGGER.debug("Audio too small, returning empty result")
            return STTResult(text="")

        # Check max size
        if len(audio_data) > STT_MAX_AUDIO_SIZE:
            raise ValueError("Audio file too large (max 10MB)")

        # Prepare audio
        prepared_audio = self._prepare_audio(audio_data, metadata)
        model = self._get_model()
        timeout = _calculate_timeout(len(prepared_audio))

        _LOGGER.debug(
            "SiliconFlow STT: model=%s, size=%d bytes",
            model,
            len(prepared_audio),
        )

        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        form_data = aiohttp.FormData()
        form_data.add_field("model", model)
        form_data.add_field(
            "file",
            prepared_audio,
            filename="recording.wav",
            content_type="audio/wav",
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    SILICONFLOW_ASR_URL,
                    headers=headers,
                    data=form_data,
                    timeout=timeout,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error("SiliconFlow API error: %s", error_text)
                        raise RuntimeError(f"API error: {response.status}")

                    response_data = await response.json()

            # Extract transcription
            text = _extract_transcription(response_data)
            if text is None:
                _LOGGER.error("Cannot extract transcription: %s", response_data)
                raise RuntimeError("API response format error")

            _LOGGER.debug("STT result: %s", text[:100] if text else "(empty)")

            return STTResult(
                text=text.strip() if text else "",
                language=self.config.language,
            )

        except asyncio.TimeoutError as exc:
            _LOGGER.error("SiliconFlow STT timeout")
            raise RuntimeError("Speech recognition timeout") from exc
        except aiohttp.ClientConnectorError as exc:
            _LOGGER.error("SiliconFlow STT connection error: %s", exc)
            raise RuntimeError("Cannot connect to STT service") from exc

    async def health_check(self) -> bool:
        """Check if the SiliconFlow API is reachable."""
        try:
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_HEALTH_CHECK)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(SILICONFLOW_ROOT_URL) as response:
                    return response.status < 500
        except Exception as e:
            _LOGGER.debug("SiliconFlow health check failed: %s", e)
            return False

    @classmethod
    def get_default_config(cls) -> dict[str, Any]:
        """Get default configuration for recommended mode."""
        return {
            "model": DEFAULT_MODEL,
            "language": "zh-CN",
        }
