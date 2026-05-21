"""API endpoints, timeouts, and retry configuration."""

from __future__ import annotations

from typing import Final

API_URLS: Final = {
    "chat": "https://api.siliconflow.cn/v1/chat/completions",
    "image": "https://api.siliconflow.cn/v1/images/generations",
    "siliconflow_base": "https://api.siliconflow.cn/v1",
    "siliconflow_root": "https://api.siliconflow.cn",
    "siliconflow_asr": "https://api.siliconflow.cn/v1/audio/transcriptions",
    "edge_tts_base": "https://speech.platform.bing.com",
    "siliconflow_register": "https://cloud.siliconflow.cn/i/U3e0rmsr",
    "siliconflow_api_key": "https://cloud.siliconflow.cn/account/ak",
}

AI_HUB_CHAT_URL: Final = API_URLS["chat"]
AI_HUB_IMAGE_GEN_URL: Final = API_URLS["image"]
SILICONFLOW_API_BASE: Final = API_URLS["siliconflow_base"]
SILICONFLOW_ROOT_URL: Final = API_URLS["siliconflow_root"]
SILICONFLOW_ASR_URL: Final = API_URLS["siliconflow_asr"]
EDGE_TTS_BASE_URL: Final = API_URLS["edge_tts_base"]
SILICONFLOW_REGISTER_URL: Final = API_URLS["siliconflow_register"]
SILICONFLOW_API_KEY_URL: Final = API_URLS["siliconflow_api_key"]

TIMEOUTS: Final = {
    "default": 30.0,
    "chat_api": 60.0,
    "image_api": 120.0,
    "stt_api": 30.0,
    "tts_api": 30.0,
    "translation_api": 60.0,
    "media_download": 30.0,
    "health_check": 10.0,
    "config_flow_validation": 30.0,
    "camera_image": 10.0,
    "automation_api": 30.0,
}

DEFAULT_REQUEST_TIMEOUT: Final = 30000
TIMEOUT_DEFAULT: Final = TIMEOUTS["default"]
TIMEOUT_CHAT_API: Final = TIMEOUTS["chat_api"]
TIMEOUT_IMAGE_API: Final = TIMEOUTS["image_api"]
TIMEOUT_STT_API: Final = TIMEOUTS["stt_api"]
TIMEOUT_TTS_API: Final = TIMEOUTS["tts_api"]
TIMEOUT_TRANSLATION_API: Final = TIMEOUTS["translation_api"]
TIMEOUT_MEDIA_DOWNLOAD: Final = TIMEOUTS["media_download"]
TIMEOUT_HEALTH_CHECK: Final = TIMEOUTS["health_check"]
TIMEOUT_CONFIG_FLOW_VALIDATION: Final = TIMEOUTS["config_flow_validation"]
TIMEOUT_CAMERA_IMAGE: Final = TIMEOUTS["camera_image"]
TIMEOUT_AUTOMATION_API: Final = TIMEOUTS["automation_api"]

RETRY_CONFIG: Final = {
    "max_attempts": 3,
    "base_delay": 1.0,
    "max_delay": 30.0,
    "exponential_base": 2.0,
}

RETRY_MAX_ATTEMPTS: Final = RETRY_CONFIG["max_attempts"]
RETRY_BASE_DELAY: Final = RETRY_CONFIG["base_delay"]
RETRY_MAX_DELAY: Final = RETRY_CONFIG["max_delay"]
RETRY_EXPONENTIAL_BASE: Final = RETRY_CONFIG["exponential_base"]

CACHE_CONFIG: Final = {
    "tts_max_size": 100,
    "tts_ttl": 3600,
}

TTS_CACHE_MAX_SIZE: Final = CACHE_CONFIG["tts_max_size"]
TTS_CACHE_TTL: Final = CACHE_CONFIG["tts_ttl"]

AUDIO_LIMITS: Final = {
    "stt_min_size": 1000,
    "stt_max_size": 10 * 1024 * 1024,
    "stt_warning_size": 500 * 1024,
    "stt_max_file_size_mb": 25,
}

STT_MIN_AUDIO_SIZE: Final = AUDIO_LIMITS["stt_min_size"]
STT_MAX_AUDIO_SIZE: Final = AUDIO_LIMITS["stt_max_size"]
STT_WARNING_AUDIO_SIZE: Final = AUDIO_LIMITS["stt_warning_size"]
STT_MAX_FILE_SIZE_MB: Final = AUDIO_LIMITS["stt_max_file_size_mb"]

DEFAULT_IMAGE_SIZE: Final = "1024x1024"
IMAGE_PROCESS_MAX_SIZE: Final = 1024
IMAGE_PROCESS_QUALITY: Final = 85

STT_DYNAMIC_TIMEOUT_BASE: Final = 15
STT_DYNAMIC_TIMEOUT_PER_100KB: Final = 3
STT_DYNAMIC_TIMEOUT_CONNECT: Final = 5
STT_DYNAMIC_TIMEOUT_MIN_READ: Final = 10
STT_DYNAMIC_TIMEOUT_MAX: Final = 60
