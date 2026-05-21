"""Default and recommended values for AI Hub."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlparse

from .api import AI_HUB_CHAT_URL, AI_HUB_IMAGE_GEN_URL, SILICONFLOW_ASR_URL
from .base import DEFAULT_INSTRUCTIONS_PROMPT, LLM_API_ASSIST
from .config import (
    CONF_CHAT_MODEL,
    CONF_CHAT_URL,
    CONF_ENABLE_THINKING,
    CONF_FORCE_TRANSLATION,
    CONF_IMAGE_MODEL,
    CONF_IMAGE_URL,
    CONF_LIST_BLUEPRINTS,
    CONF_LIST_COMPONENTS,
    CONF_LLM_HASS_API,
    CONF_LLM_PROVIDER,
    CONF_MAX_HISTORY_MESSAGES,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_RECOMMENDED,
    CONF_STT_MODEL,
    CONF_STT_URL,
    CONF_TARGET_BLUEPRINT,
    CONF_TARGET_COMPONENT,
    CONF_TEMPERATURE,
    CONF_TOP_K,
    CONF_TOP_P,
    CONF_TTS_LANG,
    CONF_TTS_VOICE,
)

RECOMMENDED: Final[dict[str, Any]] = {
    "chat_model": "Qwen/Qwen3-8B",
    "temperature": 0.3,
    "top_p": 0.5,
    "top_k": 1,
    "max_tokens": 8192,
    "max_history_messages": 30,
    "ai_task_model": "Qwen/Qwen3-8B",
    "ai_task_temperature": 0.95,
    "ai_task_top_p": 0.7,
    "ai_task_max_tokens": 8192,
    "image_model": "Kwai-Kolors/Kolors",
    "image_analysis_model": "THUDM/GLM-4.1V-9B-Thinking",
    "tts_voice": "zh-CN-XiaoxiaoNeural",
    "stt_model": "FunAudioLLM/SenseVoiceSmall",
}

CONFIG_FLOW_TEST_MESSAGE: Final = "Hi"
CONFIG_FLOW_TEST_MAX_TOKENS: Final = 10

AUTOMATION_YAML_TEMPERATURE: Final = 0.1

TRANSLATION_SYSTEM_PROMPT: Final = "Translate English to Chinese. Return only the translation."
TRANSLATION_TEMPERATURE: Final = 0.3
TRANSLATION_MAX_TOKENS: Final = 2048

RECOMMENDED_CHAT_MODEL: Final = RECOMMENDED["chat_model"]
RECOMMENDED_LLM_PROVIDER: Final = "openai_compatible"
RECOMMENDED_TEMPERATURE: Final = RECOMMENDED["temperature"]
RECOMMENDED_TOP_P: Final = RECOMMENDED["top_p"]
RECOMMENDED_TOP_K: Final = RECOMMENDED["top_k"]
RECOMMENDED_MAX_TOKENS: Final = RECOMMENDED["max_tokens"]
RECOMMENDED_MAX_HISTORY_MESSAGES: Final = RECOMMENDED["max_history_messages"]
RECOMMENDED_AI_TASK_MODEL: Final = RECOMMENDED["ai_task_model"]
RECOMMENDED_AI_TASK_TEMPERATURE: Final = RECOMMENDED["ai_task_temperature"]
RECOMMENDED_AI_TASK_TOP_P: Final = RECOMMENDED["ai_task_top_p"]
RECOMMENDED_AI_TASK_MAX_TOKENS: Final = RECOMMENDED["ai_task_max_tokens"]
RECOMMENDED_IMAGE_MODEL: Final = RECOMMENDED["image_model"]
RECOMMENDED_IMAGE_ANALYSIS_MODEL: Final = RECOMMENDED["image_analysis_model"]
RECOMMENDED_TTS_MODEL: Final = RECOMMENDED["tts_voice"]
RECOMMENDED_STT_MODEL: Final = RECOMMENDED["stt_model"]
RECOMMENDED_ENABLE_THINKING: Final = False
RECOMMENDED_DEBUG_LOG: Final = False

DEFAULT_NAMES: Final = {
    "title": "AI Hub",
}


def _short_model_name(model: str | None) -> str:
    """Return the short display name for a model id."""
    if not model:
        return "Model"
    normalized = str(model).strip()
    if not normalized:
        return "Model"
    return normalized.rsplit("/", 1)[-1]


def _load_ai_providers() -> dict[str, Any]:
    """Load AI providers JSON."""
    json_path = Path(__file__).parent / "ai_providers.json"
    try:
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {"providers": {"default": "OpenAI"}, "url_to_provider": {}}


_AI_PROVIDERS: dict[str, Any] | None = None


def _get_ai_providers() -> dict[str, Any]:
    """Get cached AI providers data."""
    global _AI_PROVIDERS
    if _AI_PROVIDERS is None:
        _AI_PROVIDERS = _load_ai_providers()
    return _AI_PROVIDERS


def _fuzzy_match_provider(host: str, providers: dict[str, str]) -> str | None:
    """Fuzzy match provider by checking if provider id is a substring of host."""
    host_lower = host.lower().replace("-", "").replace(".", "")
    best_match = None
    best_len = 0
    for pid, name in providers.items():
        if pid == "default":
            continue
        pid_clean = pid.lower().replace("-", "")
        if pid_clean in host_lower and len(pid_clean) > best_len:
            best_match = name
            best_len = len(pid_clean)
    return best_match


def _resolve_provider_from_url(url: str | None) -> str:
    """Resolve provider display name from URL using ai_providers.json."""
    if not url:
        return "OpenAI"
    data = _get_ai_providers()
    url_map = data.get("url_to_provider", {})
    providers = data.get("providers", {})
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""
    if not host:
        return providers.get(url_map.get("default", ""), "OpenAI")
    if host in url_map:
        provider_id = url_map[host]
        return providers.get(provider_id, provider_id)
    fuzzy = _fuzzy_match_provider(host, providers)
    if fuzzy:
        return fuzzy
    default_id = url_map.get("default", "openai-compatible")
    return providers.get(default_id, "OpenAI")


def _provider_display_name(provider: str | None, url: str | None = None) -> str:
    """Return a concise provider display name from URL matching."""
    if url:
        return _resolve_provider_from_url(url)
    provider_map = {
        "openai_compatible": "OpenAI",
        "anthropic_compatible": "Anthropic",
        "ollama_compatible": "Ollama",
        "edge_tts": "EdgeTTS",
        "siliconflow_stt": "SiliconFlow",
    }
    if provider and provider in provider_map:
        return provider_map[provider]
    if provider:
        return str(provider).replace("_", " ").title().replace(" ", "")
    return "AIHub"


def get_default_service_name(name_type: str, options: dict[str, Any] | None = None) -> str:
    """Return the auto-created default service name."""
    if name_type == "title":
        return DEFAULT_NAMES["title"]

    options = options or {}
    chat_url = options.get(CONF_CHAT_URL)
    if name_type == "conversation":
        return f"{_provider_display_name(options.get(CONF_LLM_PROVIDER), chat_url)}/{_short_model_name(options.get(CONF_CHAT_MODEL))}"
    if name_type == "ai_task":
        return f"{_provider_display_name(options.get(CONF_LLM_PROVIDER), chat_url)}/{_short_model_name(options.get(CONF_CHAT_MODEL))}"
    if name_type == "translation":
        return f"{_provider_display_name(options.get(CONF_LLM_PROVIDER), chat_url)}/{_short_model_name(options.get(CONF_CHAT_MODEL))}"
    if name_type == "stt":
        stt_url = options.get(CONF_STT_URL)
        return f"{_provider_display_name(None, stt_url)}/{_short_model_name(options.get(CONF_STT_MODEL))}"
    if name_type == "tts":
        return f"EdgeTTS/{_short_model_name(options.get(CONF_TTS_VOICE))}"
    return "AI Hub"

DEFAULT_TITLE: Final = DEFAULT_NAMES["title"]
DEFAULT_CONVERSATION_NAME: Final = "AI Hub"
DEFAULT_AI_TASK_NAME: Final = "AI Hub"
DEFAULT_TTS_NAME: Final = "AI Hub"
DEFAULT_STT_NAME: Final = "AI Hub"
DEFAULT_TRANSLATION_NAME: Final = "AI Hub"

TTS_DEFAULT_VOICE: Final = "zh-CN-XiaoxiaoNeural"
TTS_DEFAULT_LANG: Final = "zh-CN"
STT_DEFAULT_MODEL: Final = "FunAudioLLM/SenseVoiceSmall"

TTS_DEFAULT_VOICES: Final = {
    "zh-CN": "zh-CN-XiaoxiaoNeural",
    "zh-TW": "zh-TW-HsiaoChenNeural",
    "zh-HK": "zh-HK-HiuMaanNeural",
    "en-US": "en-US-JennyNeural",
    "en-GB": "en-GB-LibbyNeural",
    "en-AU": "en-AU-NatashaNeural",
    "ja-JP": "ja-JP-NanamiNeural",
    "ko-KR": "ko-KR-SunHiNeural",
    "fr-FR": "fr-FR-DeniseNeural",
    "de-DE": "de-DE-KatjaNeural",
    "es-ES": "es-ES-ElviraNeural",
    "it-IT": "it-IT-ElsaNeural",
    "pt-BR": "pt-BR-FranciscaNeural",
    "ru-RU": "ru-RU-SvetlanaNeural",
}

RECOMMENDED_CONVERSATION_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: [LLM_API_ASSIST],
    CONF_PROMPT: DEFAULT_INSTRUCTIONS_PROMPT,
    CONF_LLM_PROVIDER: RECOMMENDED_LLM_PROVIDER,
    CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
    CONF_CHAT_URL: AI_HUB_CHAT_URL,
    CONF_ENABLE_THINKING: RECOMMENDED_ENABLE_THINKING,
    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
    CONF_TOP_P: RECOMMENDED_TOP_P,
    CONF_TOP_K: RECOMMENDED_TOP_K,
    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
    CONF_MAX_HISTORY_MESSAGES: RECOMMENDED_MAX_HISTORY_MESSAGES,
}

RECOMMENDED_AI_TASK_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_URL: AI_HUB_CHAT_URL,
    CONF_CHAT_MODEL: RECOMMENDED_AI_TASK_MODEL,
    CONF_IMAGE_MODEL: RECOMMENDED_IMAGE_MODEL,
    CONF_IMAGE_URL: AI_HUB_IMAGE_GEN_URL,
    CONF_TEMPERATURE: RECOMMENDED_AI_TASK_TEMPERATURE,
    CONF_TOP_P: RECOMMENDED_AI_TASK_TOP_P,
    CONF_MAX_TOKENS: RECOMMENDED_AI_TASK_MAX_TOKENS,
}

RECOMMENDED_TTS_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_TTS_VOICE: TTS_DEFAULT_VOICE,
    CONF_TTS_LANG: TTS_DEFAULT_LANG,
}

RECOMMENDED_STT_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_STT_MODEL: STT_DEFAULT_MODEL,
    CONF_STT_URL: SILICONFLOW_ASR_URL,
}

RECOMMENDED_TRANSLATION_OPTIONS: Final = {
    CONF_RECOMMENDED: True,
    CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
    CONF_CHAT_URL: AI_HUB_CHAT_URL,
    CONF_FORCE_TRANSLATION: False,
    CONF_TARGET_COMPONENT: "",
    CONF_LIST_COMPONENTS: False,
    CONF_TARGET_BLUEPRINT: "",
    CONF_LIST_BLUEPRINTS: False,
}
