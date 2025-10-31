"""Constants for the AI Hub integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.core import HomeAssistant

# Import llm for API constants
try:
    from homeassistant.helpers import llm
    LLM_API_ASSIST = llm.LLM_API_ASSIST
    DEFAULT_INSTRUCTIONS_PROMPT = llm.DEFAULT_INSTRUCTIONS_PROMPT
except ImportError:
    # Fallback values if llm module is not available
    LLM_API_ASSIST = "assist"
    DEFAULT_INSTRUCTIONS_PROMPT = "你是一个有用的AI助手，请根据用户的问题提供准确、有帮助的回答。"

_LOGGER = logging.getLogger(__name__)
LOGGER = _LOGGER  # 为了向后兼容，提供不带下划线的版本


def get_localized_name(hass: HomeAssistant, zh_name: str, en_name: str) -> str:
    """根据Home Assistant语言设置返回本地化名称."""
    language = hass.config.language

    # 中文语言代码列表
    chinese_languages = ["zh", "zh-cn", "zh-hans", "zh-hant", "zh-tw", "zh-hk"]

    if language and language.lower() in chinese_languages:
        return zh_name
    else:
        return en_name

# Domain
DOMAIN: Final = "ai_hub"

# API Configuration
AI_HUB_API_BASE: Final = "https://open.bigmodel.cn/api/paas/v4"
AI_HUB_CHAT_URL: Final = f"{AI_HUB_API_BASE}/chat/completions"
AI_HUB_IMAGE_GEN_URL: Final = f"{AI_HUB_API_BASE}/images/generations"
AI_HUB_WEB_SEARCH_URL: Final = f"{AI_HUB_API_BASE}/web_search"
AI_HUB_TTS_URL: Final = f"{AI_HUB_API_BASE}/audio/speech"
AI_HUB_STT_URL: Final = f"{AI_HUB_API_BASE}/audio/transcriptions"

# Timeout
DEFAULT_REQUEST_TIMEOUT: Final = 30000  # milliseconds
TIMEOUT_SECONDS: Final = 30

# Configuration Keys
CONF_API_KEY: Final = "api_key"
CONF_SILICONFLOW_API_KEY: Final = "siliconflow_api_key"
CONF_CHAT_MODEL: Final = "chat_model"
CONF_IMAGE_MODEL: Final = "image_model"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_PROMPT: Final = "prompt"
CONF_TEMPERATURE: Final = "temperature"
CONF_TOP_P: Final = "top_p"
CONF_TOP_K: Final = "top_k"
CONF_LLM_HASS_API: Final = "llm_hass_api"
CONF_RECOMMENDED: Final = "recommended"
CONF_WEB_SEARCH: Final = "web_search"
CONF_MAX_HISTORY_MESSAGES: Final = "max_history_messages"

# Recommended Values for Conversation
RECOMMENDED_CHAT_MODEL: Final = "GLM-4-Flash-250414"
RECOMMENDED_TEMPERATURE: Final = 0.3
RECOMMENDED_TOP_P: Final = 0.5
RECOMMENDED_TOP_K: Final = 1
RECOMMENDED_MAX_TOKENS: Final = 250
RECOMMENDED_MAX_HISTORY_MESSAGES: Final = 30  # Keep last 30 messages for continuous conversation

# Recommended Values for AI Task
RECOMMENDED_AI_TASK_MODEL: Final = "GLM-4-Flash-250414"
RECOMMENDED_AI_TASK_TEMPERATURE: Final = 0.95
RECOMMENDED_AI_TASK_TOP_P: Final = 0.7
RECOMMENDED_AI_TASK_MAX_TOKENS: Final = 2000

# Image Analysis
RECOMMENDED_IMAGE_ANALYSIS_MODEL: Final = "glm-4.1v-thinking-flash"

# Image Generation
RECOMMENDED_IMAGE_MODEL: Final = "cogview-3-flash"

# Edge TTS Configuration
EDGE_TTS_VERSION: Final = "7.2.0"
DEFAULT_TTS_LANG: Final = "zh-CN"
RECOMMENDED_TTS_MODEL: Final = "zh-CN-XiaoxiaoNeural"

# Silicon Flow ASR Configuration
SILICONFLOW_API_BASE: Final = "https://api.siliconflow.cn/v1"
SILICONFLOW_ASR_URL: Final = f"{SILICONFLOW_API_BASE}/audio/transcriptions"
RECOMMENDED_STT_MODEL: Final = "FunAudioLLM/SenseVoiceSmall"
SILICONFLOW_STT_MODELS: Final = [
    "FunAudioLLM/SenseVoiceSmall",  # SenseVoiceSmall模型（推荐）
    "TeleAI/TeleSpeechASR",          # TeleSpeechASR模型
]

# Silicon Flow STT Language Options
SILICONFLOW_STT_LANGUAGES: Final = {
    "zh": "Chinese (Simplified)",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
}

# Silicon Flow STT Audio Formats
SILICONFLOW_STT_AUDIO_FORMATS: Final = [
    "mp3",    # MP3格式
    "wav",    # WAV格式
    "flac",   # FLAC格式
    "m4a",    # M4A格式
    "ogg",    # OGG格式
    "webm",   # WebM格式
]

# Edge TTS Voice Options - Complete voice list by language
EDGE_TTS_VOICES: Final = {
    # Chinese (Simplified) - Mainland China
    "zh-CN-XiaoxiaoNeural": "zh-CN",
    "zh-CN-XiaoyiNeural": "zh-CN",
    "zh-CN-YunjianNeural": "zh-CN",
    "zh-CN-YunxiNeural": "zh-CN",
    "zh-CN-YunxiaNeural": "zh-CN",
    "zh-CN-YunyangNeural": "zh-CN",

    # Chinese (Traditional) - Hong Kong
    "zh-HK-HiuGaaiNeural": "zh-HK",
    "zh-HK-HiuMaanNeural": "zh-HK",
    "zh-HK-WanLungNeural": "zh-HK",

    # Chinese (Traditional) - Taiwan
    "zh-TW-HsiaoChenNeural": "zh-TW",
    "zh-TW-YunJheNeural": "zh-TW",
    "zh-TW-HsiaoYuNeural": "zh-TW",

    # English - US
    "en-US-JennyNeural": "en-US",
    "en-US-GuyNeural": "en-US",
    "en-US-AriaNeural": "en-US",
    "en-US-DavisNeural": "en-US",
    "en-US-JaneNeural": "en-US",
    "en-US-JasonNeural": "en-US",
    "en-US-SaraNeural": "en-US",
    "en-US-TonyNeural": "en-US",
    "en-US-NancyNeural": "en-US",
    "en-US-AmberNeural": "en-US",
    "en-US-AnaNeural": "en-US",
    "en-US-AshleyNeural": "en-US",
    "en-US-BrandonNeural": "en-US",
    "en-US-ChristopherNeural": "en-US",
    "en-US-CoraNeural": "en-US",
    "en-US-ElizabethNeural": "en-US",
    "en-US-EricNeural": "en-US",
    "en-US-JacobNeural": "en-US",
    "en-US-JenniferNeural": "en-US",
    "en-US-MichelleNeural": "en-US",
    "en-US-MonicaNeural": "en-US",
    "en-US-RogerNeural": "en-US",

    # English - UK
    "en-GB-LibbyNeural": "en-GB",
    "en-GB-MaisieNeural": "en-GB",
    "en-GB-RyanNeural": "en-GB",
    "en-GB-SoniaNeural": "en-GB",
    "en-GB-ThomasNeural": "en-GB",
    "en-GB-AvaNeural": "en-GB",
    "en-GB-GeorgeNeural": "en-GB",
    "en-GB-HazelNeural": "en-GB",

    # English - Australia
    "en-AU-NatashaNeural": "en-AU",
    "en-AU-WilliamNeural": "en-AU",

    # English - Canada
    "en-CA-ClaraNeural": "en-CA",
    "en-CA-LiamNeural": "en-CA",

    # English - India
    "en-IN-NeerjaNeural": "en-IN",
    "en-IN-PrabhatNeural": "en-IN",

    # Japanese
    "ja-JP-NanamiNeural": "ja-JP",
    "ja-JP-KeitaNeural": "ja-JP",

    # Korean
    "ko-KR-SunHiNeural": "ko-KR",
    "ko-KR-InJoonNeural": "ko-KR",
    "ko-KR-HyunsuNeural": "ko-KR",
    "ko-KR-BongJinNeural": "ko-KR",
    "ko-KR-GooUnNeural": "ko-KR",
    "ko-KR-JiMinNeural": "ko-KR",
    "ko-KR-SeoHyeonNeural": "ko-KR",
    "ko-KR-YuJinNeural": "ko-KR",

    # French
    "fr-FR-DeniseNeural": "fr-FR",
    "fr-FR-EloiseNeural": "fr-FR",
    "fr-FR-HenriNeural": "fr-FR",

    # German
    "de-DE-KatjaNeural": "de-DE",
    "de-DE-ConradNeural": "de-DE",

    # Spanish
    "es-ES-ElviraNeural": "es-ES",
    "es-ES-AlvaroNeural": "es-ES",

    # Italian
    "it-IT-ElsaNeural": "it-IT",
    "it-IT-IsabellaNeural": "it-IT",

    # Portuguese - Brazil
    "pt-BR-FranciscaNeural": "pt-BR",
    "pt-BR-AntonioNeural": "pt-BR",

    # Russian
    "ru-RU-SvetlanaNeural": "ru-RU",
    "ru-RU-DmitryNeural": "ru-RU",

    # Arabic
    "ar-SA-ZariyahNeural": "ar-SA",
    "ar-SA-HamedNeural": "ar-SA",

    # Hindi
    "hi-IN-SwaraNeural": "hi-IN",
    "hi-IN-MadhurNeural": "hi-IN",

    # Thai
    "th-TH-AcharaNeural": "th-TH",
    "th-TH-NiwatNeural": "th-TH",

    # Vietnamese
    "vi-VN-HoaiMyNeural": "vi-VN",
    "vi-VN-NamMinhNeural": "vi-VN",

    # Indonesian
    "id-ID-GadisNeural": "id-ID",
    "id-ID-ArdiNeural": "id-ID",

    # Malay
    "ms-MY-YasminNeural": "ms-MY",

    # Turkish
    "tr-TR-EmelNeural": "tr-TR",
    "tr-TR-AhmetNeural": "tr-TR",

    # Dutch
    "nl-NL-FennaNeural": "nl-NL",
    "nl-NL-CoenNeural": "nl-NL",

    # Polish
    "pl-PL-ZofiaNeural": "pl-PL",
    "pl-PL-JacekNeural": "pl-PL",

    # Swedish
    "sv-SE-SofieNeural": "sv-SE",
    "sv-SE-MattiasNeural": "sv-SE",

    # Norwegian
    "nb-NO-PernilleNeural": "nb-NO",
    "nb-NO-FinnNeural": "nb-NO",

    # Danish
    "da-DK-ChristelNeural": "da-DK",
    "da-DK-JeppeNeural": "da-DK",

    # Finnish
    "fi-FI-SelmaNeural": "fi-FI",
    "fi-FI-HarriNeural": "fi-FI",

    # Greek
    "el-GR-AthinaNeural": "el-GR",
    "el-GR-NestorasNeural": "el-GR",

    # Hebrew
    "he-IL-AvriNeural": "he-IL",
    "he-IL-HilaNeural": "he-IL",

    # Romanian
    "ro-RO-AlinaNeural": "ro-RO",
    "ro-RO-EmilNeural": "ro-RO",

    # Ukrainian
    "uk-UA-PolinaNeural": "uk-UA",
    "uk-UA-OstapNeural": "uk-UA",

    # Bulgarian
    "bg-BG-KalinaNeural": "bg-BG",
    "bg-BG-BorislavNeural": "bg-BG",

    # Croatian
    "hr-HR-GabrijelaNeural": "hr-HR",
    "hr-HR-SreckoNeural": "hr-HR",

    # Slovak
    "sk-SK-ViktoriaNeural": "sk-SK",
    "sk-SK-LukasNeural": "sk-SK",

    # Slovenian
    "sl-SI-PetraNeural": "sl-SI",
    "sl-SI-LadoNeural": "sl-SI",

    # Estonian
    "et-EE-AnuNeural": "et-EE",
    "et-EE-KertNeural": "et-EE",

    # Latvian
    "lv-LV-EveritaNeural": "lv-LV",
    "lv-LV-OskarsNeural": "lv-LV",

    # Lithuanian
    "lt-LT-OnaNeural": "lt-LT",
    "lt-LT-LeonasNeural": "lt-LT",

    # Hungarian
    "hu-HU-NoemiNeural": "hu-HU",
    "hu-HU-TamasNeural": "hu-HU",

    # Czech
    "cs-CZ-VlastaNeural": "cs-CZ",
    "cs-CZ-AntoninNeural": "cs-CZ",

    # Catalan
    "ca-ES-JoanaNeural": "ca-ES",
    "ca-ES-EnricNeural": "ca-ES",

    # Basque
    "eu-ES-AroaNeural": "eu-ES",
    "eu-ES-AnderNeural": "eu-ES",

    # Galician
    "gl-ES-RoiNeural": "gl-ES",
    "gl-ES-SabelaNeural": "gl-ES",

    # Serbian (Cyrillic)
    "sr-RS-SophieNeural": "sr-RS",
    "sr-RS-NicholasNeural": "sr-RS",

    # Serbian (Latin)
    "sr-RS-SophieNeural": "sr-RS",
    "sr-RS-NicholasNeural": "sr-RS",

    # Icelandic
    "is-IS-GudrunNeural": "is-IS",
    "is-IS-GunnarNeural": "is-IS",
}

# Edge TTS Language to Voices Mapping
EDGE_TTS_LANGUAGES: Final = {
    "zh-CN": {
        "name": "中文（简体）",
        "voices": {
            "zh-CN-XiaoxiaoNeural": "晓晓",
            "zh-CN-XiaoyiNeural": "晓伊",
            "zh-CN-YunjianNeural": "云健",
            "zh-CN-YunxiNeural": "云希",
            "zh-CN-YunxiaNeural": "云霞",
            "zh-CN-YunyangNeural": "云扬",
        }
    },
    "zh-HK": {
        "name": "中文（香港）",
        "voices": {
            "zh-HK-HiuGaaiNeural": "晓佳",
            "zh-HK-HiuMaanNeural": "晓雯",
            "zh-HK-WanLungNeural": "云龙",
        }
    },
    "zh-TW": {
        "name": "中文（台湾）",
        "voices": {
            "zh-TW-HsiaoChenNeural": "晓臻",
            "zh-TW-YunJheNeural": "云哲",
            "zh-TW-HsiaoYuNeural": "晓雨",
        }
    },
    "en-US": {
        "name": "English (US)",
        "voices": {
            "en-US-JennyNeural": "Jenny",
            "en-US-GuyNeural": "Guy",
            "en-US-AriaNeural": "Aria",
            "en-US-DavisNeural": "Davis",
            "en-US-JaneNeural": "Jane",
            "en-US-JasonNeural": "Jason",
            "en-US-SaraNeural": "Sara",
            "en-US-TonyNeural": "Tony",
            "en-US-NancyNeural": "Nancy",
            "en-US-AmberNeural": "Amber",
            "en-US-AnaNeural": "Ana",
            "en-US-AshleyNeural": "Ashley",
            "en-US-BrandonNeural": "Brandon",
            "en-US-ChristopherNeural": "Christopher",
            "en-US-CoraNeural": "Cora",
            "en-US-ElizabethNeural": "Elizabeth",
            "en-US-EricNeural": "Eric",
            "en-US-JacobNeural": "Jacob",
            "en-US-JenniferNeural": "Jennifer",
            "en-US-MichelleNeural": "Michelle",
            "en-US-MonicaNeural": "Monica",
            "en-US-RogerNeural": "Roger",
        }
    },
    "en-GB": {
        "name": "English (UK)",
        "voices": {
            "en-GB-LibbyNeural": "Libby",
            "en-GB-MaisieNeural": "Maisie",
            "en-GB-RyanNeural": "Ryan",
            "en-GB-SoniaNeural": "Sonia",
            "en-GB-ThomasNeural": "Thomas",
            "en-GB-AvaNeural": "Ava",
            "en-GB-GeorgeNeural": "George",
            "en-GB-HazelNeural": "Hazel",
        }
    },
    "en-AU": {
        "name": "English (Australia)",
        "voices": {
            "en-AU-NatashaNeural": "Natasha",
            "en-AU-WilliamNeural": "William",
        }
    },
    "en-CA": {
        "name": "English (Canada)",
        "voices": {
            "en-CA-ClaraNeural": "Clara",
            "en-CA-LiamNeural": "Liam",
        }
    },
    "en-IN": {
        "name": "English (India)",
        "voices": {
            "en-IN-NeerjaNeural": "Neerja",
            "en-IN-PrabhatNeural": "Prabhat",
        }
    },
    "ja-JP": {
        "name": "日本語",
        "voices": {
            "ja-JP-NanamiNeural": "Nanami",
            "ja-JP-KeitaNeural": "Keita",
        }
    },
    "ko-KR": {
        "name": "한국어",
        "voices": {
            "ko-KR-SunHiNeural": "SunHi",
            "ko-KR-InJoonNeural": "InJoon",
            "ko-KR-HyunsuNeural": "Hyunsu",
            "ko-KR-BongJinNeural": "BongJin",
            "ko-KR-GooUnNeural": "GooUn",
            "ko-KR-JiMinNeural": "JiMin",
            "ko-KR-SeoHyeonNeural": "SeoHyeon",
            "ko-KR-YuJinNeural": "YuJin",
        }
    },
    "fr-FR": {
        "name": "Français",
        "voices": {
            "fr-FR-DeniseNeural": "Denise",
            "fr-FR-EloiseNeural": "Eloise",
            "fr-FR-HenriNeural": "Henri",
        }
    },
    "de-DE": {
        "name": "Deutsch",
        "voices": {
            "de-DE-KatjaNeural": "Katja",
            "de-DE-ConradNeural": "Conrad",
        }
    },
    "es-ES": {
        "name": "Español",
        "voices": {
            "es-ES-ElviraNeural": "Elvira",
            "es-ES-AlvaroNeural": "Alvaro",
        }
    },
    "it-IT": {
        "name": "Italiano",
        "voices": {
            "it-IT-ElsaNeural": "Elsa",
            "it-IT-IsabellaNeural": "Isabella",
        }
    },
    "pt-BR": {
        "name": "Português (Brasil)",
        "voices": {
            "pt-BR-FranciscaNeural": "Francisca",
            "pt-BR-AntonioNeural": "Antonio",
        }
    },
    "ru-RU": {
        "name": "Русский",
        "voices": {
            "ru-RU-SvetlanaNeural": "Svetlana",
            "ru-RU-DmitryNeural": "Dmitry",
        }
    },
    "ar-SA": {
        "name": "العربية",
        "voices": {
            "ar-SA-ZariyahNeural": "Zariyah",
            "ar-SA-HamedNeural": "Hamed",
        }
    },
    "hi-IN": {
        "name": "हिन्दी",
        "voices": {
            "hi-IN-SwaraNeural": "Swara",
            "hi-IN-MadhurNeural": "Madhur",
        }
    },
    "th-TH": {
        "name": "ไทย",
        "voices": {
            "th-TH-AcharaNeural": "Achara",
            "th-TH-NiwatNeural": "Niwat",
        }
    },
    "vi-VN": {
        "name": "Tiếng Việt",
        "voices": {
            "vi-VN-HoaiMyNeural": "HoaiMy",
            "vi-VN-NamMinhNeural": "NamMinh",
        }
    },
    "id-ID": {
        "name": "Bahasa Indonesia",
        "voices": {
            "id-ID-GadisNeural": "Gadis",
            "id-ID-ArdiNeural": "Ardi",
        }
    },
    "ms-MY": {
        "name": "Bahasa Melayu",
        "voices": {
            "ms-MY-YasminNeural": "Yasmin",
        }
    },
    "tr-TR": {
        "name": "Türkçe",
        "voices": {
            "tr-TR-EmelNeural": "Emel",
            "tr-TR-AhmetNeural": "Ahmet",
        }
    },
    "nl-NL": {
        "name": "Nederlands",
        "voices": {
            "nl-NL-FennaNeural": "Fenna",
            "nl-NL-CoenNeural": "Coen",
        }
    },
    "pl-PL": {
        "name": "Polski",
        "voices": {
            "pl-PL-ZofiaNeural": "Zofia",
            "pl-PL-JacekNeural": "Jacek",
        }
    },
    "sv-SE": {
        "name": "Svenska",
        "voices": {
            "sv-SE-SofieNeural": "Sofie",
            "sv-SE-MattiasNeural": "Mattias",
        }
    },
    "nb-NO": {
        "name": "Norsk",
        "voices": {
            "nb-NO-PernilleNeural": "Pernille",
            "nb-NO-FinnNeural": "Finn",
        }
    },
    "da-DK": {
        "name": "Dansk",
        "voices": {
            "da-DK-ChristelNeural": "Christel",
            "da-DK-JeppeNeural": "Jeppe",
        }
    },
    "fi-FI": {
        "name": "Suomi",
        "voices": {
            "fi-FI-SelmaNeural": "Selma",
            "fi-FI-HarriNeural": "Harri",
        }
    },
    "el-GR": {
        "name": "Ελληνικά",
        "voices": {
            "el-GR-AthinaNeural": "Athina",
            "el-GR-NestorasNeural": "Nestoras",
        }
    },
    "he-IL": {
        "name": "עברית",
        "voices": {
            "he-IL-AvriNeural": "Avri",
            "he-IL-HilaNeural": "Hila",
        }
    },
}

# Edge TTS Configuration Keys
CONF_TTS_VOICE: Final = "voice"
CONF_TTS_LANG: Final = "lang"
CONF_TTS_RATE: Final = "rate"
CONF_TTS_VOLUME: Final = "volume"
CONF_TTS_PITCH: Final = "pitch"

# Edge TTS Default Parameters
TTS_DEFAULT_VOICE: Final = "zh-CN-XiaoxiaoNeural"  # 默认使用晓晓女声
TTS_DEFAULT_LANG: Final = "zh-CN"
TTS_DEFAULT_RATE: Final = "+0%"
TTS_DEFAULT_VOLUME: Final = "+0%"
TTS_DEFAULT_PITCH: Final = "+0Hz"

# Silicon Flow STT Configuration
# STT Configuration Keys
CONF_STT_FILE: Final = "file"
CONF_STT_MODEL: Final = "model"

# STT Default Parameters
STT_DEFAULT_MODEL: Final = "FunAudioLLM/SenseVoiceSmall"

# STT File Size Limits
STT_MAX_FILE_SIZE_MB: Final = 25  # 最大文件大小 25MB

# Update old references
AI_HUB_STT_AUDIO_FORMATS: Final = SILICONFLOW_STT_AUDIO_FORMATS
AI_HUB_STT_MODELS: Final = SILICONFLOW_STT_MODELS
IMAGE_SIZES: Final = [
    "1024x1024",
    "768x1344",
    "864x1152",
    "1344x768",
    "1152x864",
    "1440x720",
    "720x1440",
]

# Available Models (Only Free Models)
AI_HUB_CHAT_MODELS: Final = [
    "GLM-4-Flash",          # GLM-4-Flash - 免费通用，128K/16K，免费
    "glm-4.5-flash",        # GLM-4.5-Flash - 免费通用模型，128K/16K，免费使用，解码速度20-25tokens/秒
    "GLM-4-Flash-250414",   # GLM-4-Flash-250414 - 免费通用，128K/16K，免费
    "GLM-Z1-Flash",         # GLM-Z1-Flash - 免费推理，128K/32K，免费
]

AI_HUB_IMAGE_MODELS: Final = [
    "cogview-3-flash",      # CogView-3 Flash (免费)
]

# Vision Models (支持图像分析) - 仅免费模型
VISION_MODELS: Final = [
    "glm-4.1v-thinking-flash",  # glm-4.1v-thinking-flash - 更强的免费视觉模型（推荐）
    "glm-4v-flash",       # GLM-4V-Flash - 免费视觉模型
]

# Default Names
DEFAULT_TITLE: Final = "AI Hub"
DEFAULT_CONVERSATION_NAME: Final = "AI Hub对话助手"
DEFAULT_AI_TASK_NAME: Final = "AI Hub AI任务"
DEFAULT_TTS_NAME: Final = "AI Hub TTS语音"
DEFAULT_TTS_NAME_EN: Final = "AI Hub TTS"
DEFAULT_STT_NAME: Final = "AI Hub STT语音"
DEFAULT_STT_NAME_EN: Final = "AI Hub STT"
DEFAULT_CONVERSATION_NAME_EN: Final = "AI Hub Assistant"
DEFAULT_AI_TASK_NAME_EN: Final = "AI Hub Task"

# Services
SERVICE_GENERATE_IMAGE: Final = "generate_image"
SERVICE_ANALYZE_IMAGE: Final = "analyze_image"
SERVICE_TTS_SPEECH: Final = "tts_speech"
SERVICE_STT_TRANSCRIBE: Final = "stt_transcribe"

# Error Messages
ERROR_GETTING_RESPONSE: Final = "获取响应时出错"
ERROR_INVALID_API_KEY: Final = "API密钥无效"
ERROR_CANNOT_CONNECT: Final = "无法连接到AI Hub服务"

# Web Search Tool
WEB_SEARCH_TOOL: Final = {
    "type": "web_search",
    "web_search": {
        "enable": False,
        "search_query": ""
    }
}

# Recommended Options
RECOMMENDED_CONVERSATION_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: LLM_API_ASSIST,
    CONF_PROMPT: DEFAULT_INSTRUCTIONS_PROMPT,
    CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_TOP_P: RECOMMENDED_TOP_P,
    CONF_TOP_K: RECOMMENDED_TOP_K,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
    CONF_MAX_HISTORY_MESSAGES: RECOMMENDED_MAX_HISTORY_MESSAGES,
    CONF_WEB_SEARCH: False,
}

RECOMMENDED_AI_TASK_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_MODEL: RECOMMENDED_AI_TASK_MODEL,
    CONF_TEMPERATURE: RECOMMENDED_AI_TASK_TEMPERATURE,
    CONF_TOP_P: RECOMMENDED_AI_TASK_TOP_P,
    CONF_MAX_TOKENS: RECOMMENDED_AI_TASK_MAX_TOKENS,
    CONF_IMAGE_MODEL: RECOMMENDED_IMAGE_MODEL,
}

RECOMMENDED_TTS_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_TTS_VOICE: TTS_DEFAULT_VOICE,
    CONF_TTS_LANG: TTS_DEFAULT_LANG,
    CONF_TTS_RATE: TTS_DEFAULT_RATE,
    CONF_TTS_VOLUME: TTS_DEFAULT_VOLUME,
    CONF_TTS_PITCH: TTS_DEFAULT_PITCH,
}

RECOMMENDED_STT_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_STT_MODEL: STT_DEFAULT_MODEL,
}
