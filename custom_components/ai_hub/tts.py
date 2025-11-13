"""Text to speech support for AI Hub using Edge TTS."""

from __future__ import annotations

import logging
from typing import Any

from propcache.api import cached_property

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

try:
    import edge_tts
    import edge_tts.exceptions
except ImportError:
    try:
        import edgeTTS
        raise Exception('Please uninstall edgeTTS and install edge_tts instead.')
    except ImportError:
        raise Exception('edge_tts is required. Please install edge_tts.')

from .const import (
    CONF_TTS_VOICE,
    CONF_TTS_LANG,
    CONF_TTS_RATE,
    CONF_TTS_VOLUME,
    CONF_TTS_PITCH,
    TTS_DEFAULT_VOICE,
    TTS_DEFAULT_LANG,
    TTS_DEFAULT_RATE,
    TTS_DEFAULT_VOLUME,
    TTS_DEFAULT_PITCH,
    EDGE_TTS_VOICES,
    DOMAIN,
)

# Create supported languages dynamically like edge_tts
SUPPORTED_LANGUAGES = {
    **dict(zip(EDGE_TTS_VOICES.values(), EDGE_TTS_VOICES.keys())),
    'zh-CN': 'zh-CN-XiaoxiaoNeural',
}
from .entity import AIHubEntityBase
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TTS entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "tts":
            continue

        async_add_entities(
            [AIHubTextToSpeechEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class AIHubTextToSpeechEntity(TextToSpeechEntity, AIHubEntityBase):
    """AI Hub text-to-speech entity using Edge TTS."""

    _attr_has_entity_name = False
    _attr_supported_options = ['voice', 'rate', 'volume', 'pitch']

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the TTS entity."""
        super().__init__(config_entry, subentry, TTS_DEFAULT_VOICE)
        self._attr_available = True

        # Override device info for TTS
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="老王杂谈说",
            model="Edge TTS",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def options(self) -> dict[str, Any]:
        """Return the options for this entity."""
        return self.subentry.data

    @cached_property
    def default_options(self) -> dict[str, Any]:
        """Return default options."""
        return {
            ATTR_VOICE: TTS_DEFAULT_VOICE,
        }

    @property
    def default_language(self) -> str:
        """Return the default language from configured voice."""
        # First try to get language from legacy CONF_TTS_LANG for backward compatibility
        if CONF_TTS_LANG in self.subentry.data:
            return self.subentry.data[CONF_TTS_LANG]

        # Extract language from configured voice ID (e.g., "zh-CN-XiaoxiaoNeural" -> "zh-CN")
        voice = self.subentry.data.get(CONF_TTS_VOICE, TTS_DEFAULT_VOICE)
        return EDGE_TTS_VOICES.get(voice, TTS_DEFAULT_LANG)

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return list([*SUPPORTED_LANGUAGES.keys(), *EDGE_TTS_VOICES.keys()])

    @property
    def supported_formats(self) -> list[str]:
        """Return a list of supported audio formats."""
        return ["wav", "mp3", "ogg", "flac"]

    @property
    def supported_codecs(self) -> list[str]:
        """Return a list of supported audio codecs."""
        return ["pcm", "mp3", "wav", "flac", "aac", "ogg"]

    @property
    def supported_sample_rates(self) -> list[int]:
        """Return a list of supported sample rates."""
        return [8000, 11025, 16000, 22050, 44100, 48000]

    @property
    def supported_bit_rates(self) -> list[int]:
        """Return a list of supported bit rates."""
        return [8, 16, 24, 32, 64, 128, 256, 320]

    @property
    def supported_channels(self) -> list[int]:
        """Return a list of supported audio channels."""
        return [1, 2]

    @property
    def _supported_voices(self) -> list[Voice]:
        """Return supported voices."""
        voices = []
        for voice_id in EDGE_TTS_VOICES.keys():
            voices.append(Voice(voice_id, voice_id))
        return voices

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return a list of supported voices for a language."""
        if language is None:
            return self._supported_voices

        # Return voices for the specified language
        voices = []
        for voice_id, voice_lang in EDGE_TTS_VOICES.items():
            if voice_lang == language:
                voices.append(Voice(voice_id, voice_id))
        return voices

    def _get_default_voice_for_language(self, language: str) -> str:
        """Get default voice for a language."""
        # Default voices for each language
        default_voices = {
            "zh-CN": "zh-CN-XiaoxiaoNeural",    # 晓晓 - 中文简体女声
            "zh-TW": "zh-TW-HsiaochenNeural",   # 曉臻 - 中文繁体女声
            "zh-HK": "zh-HK-HiuMaanNeural",     # 曉嫻 - 中文香港女声
            "en-US": "en-US-JennyNeural",       # Jenny - 美式英语女声
            "en-GB": "en-GB-LibbyNeural",       # Libby - 英式英语女声
            "en-AU": "en-AU-NatashaNeural",     # Natasha - 澳式英语女声
            "en-CA": "en-CA-ClaraNeural",       # Clara - 加式英语女声
            "en-IN": "en-IN-NeerjaNeural",      # Neerja - 印式英语女声
            "ja-JP": "ja-JP-NanamiNeural",     # Nanami - 日语女声
            "ko-KR": "ko-KR-SunHiNeural",      # SunHi - 韩语女声
            "es-ES": "es-ES-ElviraNeural",     # Elvira - 西班牙女声
            "es-MX": "es-MX-DaliaNeural",      # Dalia - 墨西哥西班牙语女声
            "fr-FR": "fr-FR-DeniseNeural",     # Denise - 法语女声
            "fr-CA": "fr-CA-SylvieNeural",     # Sylvie - 加拿大法语女声
            "de-DE": "de-DE-KatjaNeural",      # Katja - 德语女声
            "it-IT": "it-IT-ElsaNeural",       # Elsa - 意大利语女声
            "pt-BR": "pt-BR-FranciscaNeural",  # Francisca - 巴西葡萄牙语女声
            "pt-PT": "pt-PT-RaquelNeural",     # Raquel - 葡萄牙葡萄牙语女声
            "ru-RU": "ru-RU-SvetlanaNeural",   # Svetlana - 俄语女声
            "ar-SA": "ar-SA-ZariyahNeural",    # Zariyah - 阿拉伯语女声
            "hi-IN": "hi-IN-SwaraNeural",      # Swara - 印地语女声
        }

        # Return language-specific default if available, otherwise fallback to Chinese
        return default_voices.get(language, TTS_DEFAULT_VOICE)

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any] | None = None
    ) -> TtsAudioType:
        """Load TTS audio."""
        config = self.subentry.data
        return await self._process_tts_audio(
            message,
            language,
            config,
            options or {}
        )

    async def _process_tts_audio(
        self,
        message: str,
        language: str,
        config: dict,
        options: dict[str, Any]
    ) -> TtsAudioType:
        """Shared TTS processing logic similar to edge_tts."""
        if not message or not message.strip():
            raise HomeAssistantError("文本内容不能为空")

        # Priority order for voice selection:
        # 1. Voice from options (Voice Assistant explicit choice)
        # 2. Configured voice from integration settings
        # 3. Default voice for the requested language
        # 4. Global default voice

        voice = None

        # Check if Voice Assistant specified a voice in options
        if 'voice' in options and options['voice']:
            voice = options['voice']
            _LOGGER.debug("Using Voice Assistant specified voice: %s", voice)
        else:
            # Use configured voice from integration
            voice = config.get(CONF_TTS_VOICE, TTS_DEFAULT_VOICE)
            _LOGGER.debug("Using integration configured voice: %s", voice)

        # Verify the voice exists in our supported voices
        if voice not in EDGE_TTS_VOICES:
            _LOGGER.warning("Voice '%s' not found in supported voices, using default for language %s", voice, language)
            # Try to get default voice for the language
            voice = self._get_default_voice_for_language(language)
            if voice not in EDGE_TTS_VOICES:
                voice = TTS_DEFAULT_VOICE

        # Extract the actual language from the selected voice
        actual_language = EDGE_TTS_VOICES.get(voice, TTS_DEFAULT_LANG)

        # Log language/voice mapping for debugging
        if language and actual_language and language != actual_language:
            _LOGGER.info("Language mapping: Voice Assistant requested '%s', using voice '%s' (language: %s)",
                        language, voice, actual_language)

        # Merge configuration options
        opt = {**config, **options}

        _LOGGER.debug('TTS: message="%s", voice="%s", requested_lang="%s", actual_lang="%s"',
                     message, voice, language, actual_language)

        try:
            communicate = edge_tts.Communicate(
                text=message,
                voice=voice,
                pitch=opt.get('pitch', TTS_DEFAULT_PITCH),
                rate=opt.get('rate', TTS_DEFAULT_RATE),
                volume=opt.get('volume', TTS_DEFAULT_VOLUME),
            )

            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]

            if not audio_bytes:
                raise HomeAssistantError("未生成音频数据")

            return "mp3", audio_bytes

        except Exception as exc:
            _LOGGER.error("Edge TTS 生成失败: %s", exc)
            raise HomeAssistantError(f"TTS 生成失败: {exc}") from exc