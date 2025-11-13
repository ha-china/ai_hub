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


def _build_edge_tts_languages() -> dict:
    """从EDGE_TTS_VOICES构建语言映射，避免重复维护."""
    languages = {}
    for voice_id, lang_code in EDGE_TTS_VOICES.items():
        # 提取语音名称（去掉语言代码后缀）
        voice_name = voice_id.replace(f"{lang_code}-", "")

        if lang_code not in languages:
            # 获取本地化语言名称
            if lang_code == "zh-CN":
                lang_name = "中文（简体）"
            elif lang_code == "en-US":
                lang_name = "English (US)"
            elif lang_code == "en-GB":
                lang_name = "English (UK)"
            elif lang_code == "ja-JP":
                lang_name = "日本語"
            elif lang_code == "ko-KR":
                lang_name = "한국어"
            elif lang_code == "fr-FR":
                lang_name = "Français"
            elif lang_code == "de-DE":
                lang_name = "Deutsch"
            elif lang_code == "es-ES":
                lang_name = "Español"
            elif lang_code == "it-IT":
                lang_name = "Italiano"
            elif lang_code == "pt-BR":
                lang_name = "Português (Brasil)"
            elif lang_code == "ru-RU":
                lang_name = "Русский"
            elif lang_code == "ar-SA":
                lang_name = "العربية"
            elif lang_code == "hi-IN":
                lang_name = "हिन्दी"
            elif lang_code == "th-TH":
                lang_name = "ไทย"
            elif lang_code == "vi-VN":
                lang_name = "Tiếng Việt"
            elif lang_code == "id-ID":
                lang_name = "Bahasa Indonesia"
            elif lang_code == "ms-MY":
                lang_name = "Bahasa Melayu"
            elif lang_code == "tr-TR":
                lang_name = "Türkçe"
            elif lang_code == "nl-NL":
                lang_name = "Nederlands"
            elif lang_code == "pl-PL":
                lang_name = "Polski"
            elif lang_code == "sv-SE":
                lang_name = "Svenska"
            elif lang_code == "nb-NO":
                lang_name = "Norsk"
            elif lang_code == "da-DK":
                lang_name = "Dansk"
            elif lang_code == "fi-FI":
                lang_name = "Suomi"
            elif lang_code == "el-GR":
                lang_name = "Ελληνικά"
            elif lang_code == "he-IL":
                lang_name = "עברית"
            else:
                lang_name = lang_code

            languages[lang_code] = {
                "name": lang_name,
                "voices": {}
            }

        languages[lang_code]["voices"][voice_id] = voice_name

    return languages



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

# Silicon Flow STT Models (官方完整列表)
SILICONFLOW_STT_MODELS: Final = [
    "TeleAI/TeleSpeechASR",          # TeleSpeechASR - 免费
    "FunAudioLLM/SenseVoiceSmall",   # SenseVoiceSmall - 免费（推荐）
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

# Edge TTS Voices (完整官方列表)
EDGE_TTS_VOICES: Final = {
    'zh-CN-XiaoxiaoNeural': 'zh-CN',
    'zh-CN-XiaoyiNeural': 'zh-CN',
    'zh-CN-YunjianNeural': 'zh-CN',
    'zh-CN-YunxiNeural': 'zh-CN',
    'zh-CN-YunxiaNeural': 'zh-CN',
    'zh-CN-YunyangNeural': 'zh-CN',
    'zh-HK-HiuGaaiNeural': 'zh-HK',
    'zh-HK-HiuMaanNeural': 'zh-HK',
    'zh-HK-WanLungNeural': 'zh-HK',
    'zh-TW-HsiaoChenNeural': 'zh-TW',
    'zh-TW-YunJheNeural': 'zh-TW',
    'zh-TW-HsiaoYuNeural': 'zh-TW',
    'af-ZA-AdriNeural': 'af-ZA',
    'af-ZA-WillemNeural': 'af-ZA',
    'am-ET-AmehaNeural': 'am-ET',
    'am-ET-MekdesNeural': 'am-ET',
    'ar-AE-FatimaNeural': 'ar-AE',
    'ar-AE-HamdanNeural': 'ar-AE',
    'ar-BH-AliNeural': 'ar-BH',
    'ar-BH-LailaNeural': 'ar-BH',
    'ar-DZ-AminaNeural': 'ar-DZ',
    'ar-DZ-IsmaelNeural': 'ar-DZ',
    'ar-EG-SalmaNeural': 'ar-EG',
    'ar-EG-ShakirNeural': 'ar-EG',
    'ar-IQ-BasselNeural': 'ar-IQ',
    'ar-IQ-RanaNeural': 'ar-IQ',
    'ar-JO-SanaNeural': 'ar-JO',
    'ar-JO-TaimNeural': 'ar-JO',
    'ar-KW-FahedNeural': 'ar-KW',
    'ar-KW-NouraNeural': 'ar-KW',
    'ar-LB-LaylaNeural': 'ar-LB',
    'ar-LB-RamiNeural': 'ar-LB',
    'ar-LY-ImanNeural': 'ar-LY',
    'ar-LY-OmarNeural': 'ar-LY',
    'ar-MA-JamalNeural': 'ar-MA',
    'ar-MA-MounaNeural': 'ar-MA',
    'ar-OM-AbdullahNeural': 'ar-OM',
    'ar-OM-AyshaNeural': 'ar-OM',
    'ar-QA-AmalNeural': 'ar-QA',
    'ar-QA-MoazNeural': 'ar-QA',
    'ar-SA-HamedNeural': 'ar-SA',
    'ar-SA-ZariyahNeural': 'ar-SA',
    'ar-SY-AmanyNeural': 'ar-SY',
    'ar-SY-LaithNeural': 'ar-SY',
    'ar-TN-HediNeural': 'ar-TN',
    'ar-TN-ReemNeural': 'ar-TN',
    'ar-YE-MaryamNeural': 'ar-YE',
    'ar-YE-SalehNeural': 'ar-YE',
    'az-AZ-BabekNeural': 'az-AZ',
    'az-AZ-BanuNeural': 'az-AZ',
    'bg-BG-BorislavNeural': 'bg-BG',
    'bg-BG-KalinaNeural': 'bg-BG',
    'bn-BD-NabanitaNeural': 'bn-BD',
    'bn-BD-PradeepNeural': 'bn-BD',
    'bn-IN-BashkarNeural': 'bn-IN',
    'bn-IN-TanishaaNeural': 'bn-IN',
    'bs-BA-GoranNeural': 'bs-BA',
    'bs-BA-VesnaNeural': 'bs-BA',
    'ca-ES-EnricNeural': 'ca-ES',
    'ca-ES-JoanaNeural': 'ca-ES',
    'cs-CZ-AntoninNeural': 'cs-CZ',
    'cs-CZ-VlastaNeural': 'cs-CZ',
    'cy-GB-AledNeural': 'cy-GB',
    'cy-GB-NiaNeural': 'cy-GB',
    'da-DK-ChristelNeural': 'da-DK',
    'da-DK-JeppeNeural': 'da-DK',
    'de-AT-IngridNeural': 'de-AT',
    'de-AT-JonasNeural': 'de-AT',
    'de-CH-JanNeural': 'de-CH',
    'de-CH-LeniNeural': 'de-CH',
    'de-DE-AmalaNeural': 'de-DE',
    'de-DE-ConradNeural': 'de-DE',
    'de-DE-KatjaNeural': 'de-DE',
    'de-DE-SeraphinaMultilingualNeural': 'de-DE',
    'de-DE-KillianNeural': 'de-DE',
    'el-GR-AthinaNeural': 'el-GR',
    'el-GR-NestorasNeural': 'el-GR',
    'en-AU-NatashaNeural': 'en-AU',
    'en-AU-WilliamNeural': 'en-AU',
    'en-CA-ClaraNeural': 'en-CA',
    'en-CA-LiamNeural': 'en-CA',
    'en-GB-LibbyNeural': 'en-GB',
    'en-GB-MaisieNeural': 'en-GB',
    'en-GB-RyanNeural': 'en-GB',
    'en-GB-SoniaNeural': 'en-GB',
    'en-GB-ThomasNeural': 'en-GB',
    'en-HK-SamNeural': 'en-HK',
    'en-HK-YanNeural': 'en-HK',
    'en-IE-ConnorNeural': 'en-IE',
    'en-IE-EmilyNeural': 'en-IE',
    'en-IN-NeerjaNeural': 'en-IN',
    'en-IN-PrabhatNeural': 'en-IN',
    'en-KE-AsiliaNeural': 'en-KE',
    'en-KE-ChilembaNeural': 'en-KE',
    'en-NG-AbeoNeural': 'en-NG',
    'en-NG-EzinneNeural': 'en-NG',
    'en-NZ-MitchellNeural': 'en-NZ',
    'en-NZ-MollyNeural': 'en-NZ',
    'en-PH-JamesNeural': 'en-PH',
    'en-PH-RosaNeural': 'en-PH',
    'en-SG-LunaNeural': 'en-SG',
    'en-SG-WayneNeural': 'en-SG',
    'en-TZ-ElimuNeural': 'en-TZ',
    'en-TZ-ImaniNeural': 'en-TZ',
    'en-US-AvaNeural': 'en-US',
    'en-US-AndrewNeural': 'en-US',
    'en-US-EmmaNeural': 'en-US',
    'en-US-BrianNeural': 'en-US',
    'en-US-AnaNeural': 'en-US',
    'en-US-AndrewMultilingualNeural': 'en-US',
    'en-US-AriaNeural': 'en-US',
    'en-US-AvaMultilingualNeural': 'en-US',
    'en-US-BrianMultilingualNeural': 'en-US',
    'en-US-ChristopherNeural': 'en-US',
    'en-US-EmmaMultilingualNeural': 'en-US',
    'en-US-EricNeural': 'en-US',
    'en-US-GuyNeural': 'en-US',
    'en-US-JennyNeural': 'en-US',
    'en-US-MichelleNeural': 'en-US',
    'en-US-RogerNeural': 'en-US',
    'en-US-SteffanNeural': 'en-US',
    'en-ZA-LeahNeural': 'en-ZA',
    'en-ZA-LukeNeural': 'en-ZA',
    'es-AR-ElenaNeural': 'es-AR',
    'es-AR-TomasNeural': 'es-AR',
    'es-BO-MarceloNeural': 'es-BO',
    'es-BO-SofiaNeural': 'es-BO',
    'es-CL-CatalinaNeural': 'es-CL',
    'es-CL-LorenzoNeural': 'es-CL',
    'es-CO-GonzaloNeural': 'es-CO',
    'es-CO-SalomeNeural': 'es-CO',
    'es-CR-JuanNeural': 'es-CR',
    'es-CR-MariaNeural': 'es-CR',
    'es-CU-BelkysNeural': 'es-CU',
    'es-CU-ManuelNeural': 'es-CU',
    'es-DO-EmilioNeural': 'es-DO',
    'es-DO-RamonaNeural': 'es-DO',
    'es-EC-AndreaNeural': 'es-EC',
    'es-EC-LuisNeural': 'es-EC',
    'es-ES-AlvaroNeural': 'es-ES',
    'es-ES-ElviraNeural': 'es-ES',
    'es-ES-ManuelEsCUNeural': 'es-ES',
    'es-GQ-JavierNeural': 'es-GQ',
    'es-GQ-TeresaNeural': 'es-GQ',
    'es-GT-AndresNeural': 'es-GT',
    'es-GT-MartaNeural': 'es-GT',
    'es-HN-CarlosNeural': 'es-HN',
    'es-HN-KarlaNeural': 'es-HN',
    'es-MX-DaliaNeural': 'es-MX',
    'es-MX-JorgeNeural': 'es-MX',
    'es-MX-LorenzoEsCLNeural': 'es-MX',
    'es-NI-FedericoNeural': 'es-NI',
    'es-NI-YolandaNeural': 'es-NI',
    'es-PA-MargaritaNeural': 'es-PA',
    'es-PA-RobertoNeural': 'es-PA',
    'es-PE-AlexNeural': 'es-PE',
    'es-PE-CamilaNeural': 'es-PE',
    'es-PR-KarinaNeural': 'es-PR',
    'es-PR-VictorNeural': 'es-PR',
    'es-PY-MarioNeural': 'es-PY',
    'es-PY-TaniaNeural': 'es-PY',
    'es-SV-LorenaNeural': 'es-SV',
    'es-SV-RodrigoNeural': 'es-SV',
    'es-US-AlonsoNeural': 'es-US',
    'es-US-PalomaNeural': 'es-US',
    'es-UY-MateoNeural': 'es-UY',
    'es-UY-ValentinaNeural': 'es-UY',
    'es-VE-PaolaNeural': 'es-VE',
    'es-VE-SebastianNeural': 'es-VE',
    'et-EE-AnuNeural': 'et-EE',
    'et-EE-KertNeural': 'et-EE',
    'fa-IR-DilaraNeural': 'fa-IR',
    'fa-IR-FaridNeural': 'fa-IR',
    'fi-FI-HarriNeural': 'fi-FI',
    'fi-FI-NooraNeural': 'fi-FI',
    'fil-PH-AngeloNeural': 'fil-PH',
    'fil-PH-BlessicaNeural': 'fil-PH',
    'fr-BE-CharlineNeural': 'fr-BE',
    'fr-BE-GerardNeural': 'fr-BE',
    'fr-CA-AntoineNeural': 'fr-CA',
    'fr-CA-JeanNeural': 'fr-CA',
    'fr-CA-SylvieNeural': 'fr-CA',
    'fr-CH-ArianeNeural': 'fr-CH',
    'fr-CH-FabriceNeural': 'fr-CH',
    'fr-FR-DeniseNeural': 'fr-FR',
    'fr-FR-EloiseNeural': 'fr-FR',
    'fr-FR-HenriNeural': 'fr-FR',
    'ga-IE-ColmNeural': 'ga-IE',
    'ga-IE-OrlaNeural': 'ga-IE',
    'gl-ES-RoiNeural': 'gl-ES',
    'gl-ES-SabelaNeural': 'gl-ES',
    'gu-IN-DhwaniNeural': 'gu-IN',
    'gu-IN-NiranjanNeural': 'gu-IN',
    'he-IL-AvriNeural': 'he-IL',
    'he-IL-HilaNeural': 'he-IL',
    'hi-IN-MadhurNeural': 'hi-IN',
    'hi-IN-SwaraNeural': 'hi-IN',
    'hr-HR-GabrijelaNeural': 'hr-HR',
    'hr-HR-SreckoNeural': 'hr-HR',
    'hu-HU-NoemiNeural': 'hu-HU',
    'hu-HU-TamasNeural': 'hu-HU',
    'id-ID-ArdiNeural': 'id-ID',
    'id-ID-GadisNeural': 'id-ID',
    'is-IS-GudrunNeural': 'is-IS',
    'is-IS-GunnarNeural': 'is-IS',
    'it-IT-DiegoNeural': 'it-IT',
    'it-IT-ElsaNeural': 'it-IT',
    'it-IT-IsabellaNeural': 'it-IT',
    'ja-JP-KeitaNeural': 'ja-JP',
    'ja-JP-NanamiNeural': 'ja-JP',
    'jv-ID-DimasNeural': 'jv-ID',
    'jv-ID-SitiNeural': 'jv-ID',
    'ka-GE-EkaNeural': 'ka-GE',
    'ka-GE-GiorgiNeural': 'ka-GE',
    'kk-KZ-AigulNeural': 'kk-KZ',
    'kk-KZ-DauletNeural': 'kk-KZ',
    'km-KH-PisethNeural': 'km-KH',
    'km-KH-SreymomNeural': 'km-KH',
    'kn-IN-GaganNeural': 'kn-IN',
    'kn-IN-SapnaNeural': 'kn-IN',
    'ko-KR-InJoonNeural': 'ko-KR',
    'ko-KR-SunHiNeural': 'ko-KR',
    'lo-LA-ChanthavongNeural': 'lo-LA',
    'lo-LA-KeomanyNeural': 'lo-LA',
    'lt-LT-LeonasNeural': 'lt-LT',
    'lt-LT-OnaNeural': 'lt-LT',
    'lv-LV-EveritaNeural': 'lv-LV',
    'lv-LV-NilsNeural': 'lv-LV',
    'mk-MK-AleksandarNeural': 'mk-MK',
    'mk-MK-MarijaNeural': 'mk-MK',
    'ml-IN-MidhunNeural': 'ml-IN',
    'ml-IN-SobhanaNeural': 'ml-IN',
    'mn-MN-BataaNeural': 'mn-MN',
    'mn-MN-YesuiNeural': 'mn-MN',
    'mr-IN-AarohiNeural': 'mr-IN',
    'mr-IN-ManoharNeural': 'mr-IN',
    'ms-MY-OsmanNeural': 'ms-MY',
    'ms-MY-YasminNeural': 'ms-MY',
    'mt-MT-GraceNeural': 'mt-MT',
    'mt-MT-JosephNeural': 'mt-MT',
    'my-MM-NilarNeural': 'my-MM',
    'my-MM-ThihaNeural': 'my-MM',
    'nb-NO-FinnNeural': 'nb-NO',
    'nb-NO-PernilleNeural': 'nb-NO',
    'ne-NP-HemkalaNeural': 'ne-NP',
    'ne-NP-SagarNeural': 'ne-NP',
    'nl-BE-ArnaudNeural': 'nl-BE',
    'nl-BE-DenaNeural': 'nl-BE',
    'nl-NL-ColetteNeural': 'nl-NL',
    'nl-NL-FennaNeural': 'nl-NL',
    'nl-NL-MaartenNeural': 'nl-NL',
    'pl-PL-MarekNeural': 'pl-PL',
    'pl-PL-ZofiaNeural': 'pl-PL',
    'ps-AF-GulNawazNeural': 'ps-AF',
    'ps-AF-LatifaNeural': 'ps-AF',
    'pt-BR-AntonioNeural': 'pt-BR',
    'pt-BR-FranciscaNeural': 'pt-BR',
    'pt-PT-DuarteNeural': 'pt-PT',
    'pt-PT-RaquelNeural': 'pt-PT',
    'ro-RO-AlinaNeural': 'ro-RO',
    'ro-RO-EmilNeural': 'ro-RO',
    'ru-RU-DmitryNeural': 'ru-RU',
    'ru-RU-SvetlanaNeural': 'ru-RU',
    'si-LK-SameeraNeural': 'si-LK',
    'si-LK-ThiliniNeural': 'si-LK',
    'sk-SK-LukasNeural': 'sk-SK',
    'sk-SK-ViktoriaNeural': 'sk-SK',
    'sl-SI-PetraNeural': 'sl-SI',
    'sl-SI-RokNeural': 'sl-SI',
    'so-SO-MuuseNeural': 'so-SO',
    'so-SO-UbaxNeural': 'so-SO',
    'sq-AL-AnilaNeural': 'sq-AL',
    'sq-AL-IlirNeural': 'sq-AL',
    'sr-RS-NicholasNeural': 'sr-RS',
    'sr-RS-SophieNeural': 'sr-RS',
    'su-ID-JajangNeural': 'su-ID',
    'su-ID-TutiNeural': 'su-ID',
    'sv-SE-MattiasNeural': 'sv-SE',
    'sv-SE-SofieNeural': 'sv-SE',
    'sw-KE-RafikiNeural': 'sw-KE',
    'sw-KE-ZuriNeural': 'sw-KE',
    'sw-TZ-DaudiNeural': 'sw-TZ',
    'sw-TZ-RehemaNeural': 'sw-TZ',
    'ta-IN-PallaviNeural': 'ta-IN',
    'ta-IN-ValluvarNeural': 'ta-IN',
    'ta-LK-KumarNeural': 'ta-LK',
    'ta-LK-SaranyaNeural': 'ta-LK',
    'ta-MY-KaniNeural': 'ta-MY',
    'ta-MY-SuryaNeural': 'ta-MY',
    'ta-SG-AnbuNeural': 'ta-SG',
    'ta-SG-VenbaNeural': 'ta-SG',
    'te-IN-MohanNeural': 'te-IN',
    'te-IN-ShrutiNeural': 'te-IN',
    'th-TH-NiwatNeural': 'th-TH',
    'th-TH-PremwadeeNeural': 'th-TH',
    'tr-TR-AhmetNeural': 'tr-TR',
    'tr-TR-EmelNeural': 'tr-TR',
    'uk-UA-OstapNeural': 'uk-UA',
    'uk-UA-PolinaNeural': 'uk-UA',
    'ur-IN-GulNeural': 'ur-IN',
    'ur-IN-SalmanNeural': 'ur-IN',
    'ur-PK-AsadNeural': 'ur-PK',
    'ur-PK-UzmaNeural': 'ur-PK',
    'uz-UZ-MadinaNeural': 'uz-UZ',
    'uz-UZ-SardorNeural': 'uz-UZ',
    'vi-VN-HoaiMyNeural': 'vi-VN',
    'vi-VN-NamMinhNeural': 'vi-VN',
    'zu-ZA-ThandoNeural': 'zu-ZA',
    'zu-ZA-ThembaNeural': 'zu-ZA',
}

# Edge TTS Language to Voices Mapping (自动生成，避免重复维护)
EDGE_TTS_LANGUAGES: Final = _build_edge_tts_languages()

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

# Available Models (智谱AI官方完整列表)
AI_HUB_CHAT_MODELS: Final = [
    # 免费模型
    "GLM-4-Flash",          # GLM-4-Flash - 免费通用，128K/16K，免费
    "glm-4.5-flash",        # GLM-4.5-Flash - 免费通用模型，128K/16K，免费使用，解码速度20-25tokens/秒
    "GLM-4-Flash-250414",   # GLM-4-Flash-250414 - 免费通用，128K/16K，免费
    "GLM-Z1-Flash",         # GLM-Z1-Flash - 免费推理，128K/32K，免费

    # GLM-4系列（高性价比收费模型）
    "GLM-4-FlashX-250414",  # GLM-4-FlashX-250414 - 高速低价，128K/4K，0.1元/百万tokens
    "GLM-4-Long",           # GLM-4-Long - 超长输入，1M/4K，1元/百万tokens
    "GLM-4-Air",            # GLM-4-Air - 高性价比，128K/16K，0.5元/百万tokens
    "GLM-4-Air-250414",     # GLM-4-Air-250414 - 高性价比，128K/16K，0.5元/百万tokens
    "GLM-4-AirX",           # GLM-4-AirX - 极速推理，8K/4K，10元/百万tokens
    "GLM-Z1-Air",           # GLM-Z1-Air - 轻量推理，128K/32K，0.5元/百万tokens
    "GLM-Z1-AirX",          # GLM-Z1-AirX - 极速推理，32K/30K，5元/百万tokens
    "GLM-Z1-FlashX-250414", # GLM-Z1-FlashX-250414 - 低价推理，128K/32K，0.5元/百万tokens

    # GLM-4.5系列（主流收费模型）
    "glm-4.5",              # GLM-4.5 - 通用最强大模型，输入长度[0,32]/输出[0,0.2]：1元
    "glm-4.5-x",            # GLM-4.5-X - 高性能大模型，输入长度[0,32]/输出[0,0.2]：4元
    "glm-4.5-air",          # GLM-4.5-Air - 轻量级模型，输入长度[0,32]/输出[0,0.2]：0.4元
    "glm-4.5-airx",         # GLM-4.5-AirX - 快速推理模型，输入长度[0,32]/输出[0,0.2]：2元

    # GLM-4系列（专业收费模型）
    "GLM-4-Plus",           # GLM-4-Plus - 旧智能旗舰，128K/4K，5元/百万tokens
    "GLM-4-0520",           # GLM-4-0520 - 稳定版本，128K/4K，100元/百万tokens
    "GLM-4-AllTools",       # GLM-4-AllTools - 全能工具，128K/32K，1元/百万tokens
    "GLM-4-Assistant",      # GLM-4-Assistant - 全智能体，128K/4K，5元/百万tokens
    "GLM-4-CodeGeex-4",     # GLM-4-CodeGeex - 代码生成，128K/32K，0.1元/百万Tokens

    # 特殊模型
    "CharGLM-4",            # CharGLM-4 - 拟人对话，8K/4K，1元/百万tokens
    "glm-zero-preview",     # glm-zero-preview - （无官方定价说明/暂未公开）
]

# Image generation models (智谱AI官方列表)
AI_HUB_IMAGE_MODELS: Final = [
    "cogview-3-flash",      # CogView-3 Flash (免费)
    "cogview-3-plus",       # CogView-3 Plus (收费)
    "cogview-3",            # CogView-3 (收费)
]

# Vision models (支持图像分析) - 智谱AI官方列表
VISION_MODELS: Final = [
    "glm-4v-flash",       # GLM-4V-Flash - 免费视觉模型（推荐）
    "glm-4v",            # GLM-4V - 收费视觉模型
    "glm-4v-plus",        # GLM-4V-Plus - 收费视觉模型
]

# Default Names
DEFAULT_TITLE: Final = "AI Hub"
DEFAULT_CONVERSATION_NAME: Final = "AI Hub对话助手"
DEFAULT_AI_TASK_NAME: Final = "AI Hub AI任务"
DEFAULT_TTS_NAME: Final = "AI Hub TTS语音"
DEFAULT_TTS_NAME_EN: Final = "AI Hub TTS"
DEFAULT_STT_NAME: Final = "AI Hub STT语音"
DEFAULT_STT_NAME_EN: Final = "AI Hub STT"
DEFAULT_WECHAT_NAME: Final = "AI Hub 微信通知"
DEFAULT_WECHAT_NAME_EN: Final = "AI Hub WeChat"
DEFAULT_TRANSLATION_NAME: Final = "AI Hub 集成汉化"
DEFAULT_TRANSLATION_NAME_EN: Final = "AI Hub Integration Localization"
DEFAULT_CONVERSATION_NAME_EN: Final = "AI Hub Assistant"
DEFAULT_AI_TASK_NAME_EN: Final = "AI Hub Task"

# Configuration Keys
CONF_API_KEY: Final = "api_key"
CONF_SILICONFLOW_API_KEY: Final = "siliconflow_api_key"
CONF_BEMFA_UID: Final = "bemfa_uid"
CONF_CUSTOM_COMPONENTS_PATH: Final = "custom_components_path"
CONF_FORCE_TRANSLATION: Final = "force_translation"
CONF_TARGET_COMPONENT: Final = "target_component"
CONF_LIST_COMPONENTS: Final = "list_components"

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


# Recommended Options for WeChat (simplified)
RECOMMENDED_WECHAT_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_BEMFA_UID: "",
}

# Recommended Options for STT (simplified)
RECOMMENDED_STT_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_STT_MODEL: STT_DEFAULT_MODEL,
}

# Recommended Options for Translation (simplified)
RECOMMENDED_TRANSLATION_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_FORCE_TRANSLATION: False,
    CONF_TARGET_COMPONENT: "",
    CONF_LIST_COMPONENTS: False,
}

# Services
SERVICE_GENERATE_IMAGE: Final = "generate_image"
SERVICE_ANALYZE_IMAGE: Final = "analyze_image"
SERVICE_TTS_SPEECH: Final = "tts_speech"
SERVICE_STT_TRANSCRIBE: Final = "stt_transcribe"
SERVICE_SEND_WECHAT_MESSAGE: Final = "send_wechat_message"
SERVICE_TRANSLATE_COMPONENTS: Final = "translate_components"

# Bemfa WeChat Configuration
BEMFA_API_URL: Final = "https://apis.bemfa.com/vb/wechat/v1/wechatAlertJson"
