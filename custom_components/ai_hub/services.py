"""Services for AI Hub integration - 精简版，实际处理委托给 services_lib 模块."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .config_resolver import resolve_entry_config
from .consts import (
    AI_HUB_CHAT_URL,
    AI_HUB_IMAGE_GEN_URL,
    CONF_CHAT_MODEL,
    CONF_CHAT_URL,
    CONF_IMAGE_URL,
    CONF_STT_URL,
    DOMAIN,
    RECOMMENDED_CHAT_MODEL,
    SERVICE_ANALYZE_IMAGE,
    SERVICE_GENERATE_IMAGE,
    SERVICE_STT_TRANSCRIBE,
    SERVICE_TRANSLATE_BLUEPRINTS,
    SERVICE_TRANSLATE_COMPONENTS,
    SILICONFLOW_ASR_URL,
    SUBENTRY_AI_TASK,
    SUBENTRY_CONVERSATION,
    SUBENTRY_STT,
    SUBENTRY_TRANSLATION,
)
from .services_lib import (
    BLUEPRINTS_TRANSLATION_SCHEMA,
    # Schemas
    IMAGE_ANALYZER_SCHEMA,
    IMAGE_GENERATOR_SCHEMA,
    STT_SCHEMA,
    TRANSLATION_SCHEMA,
    async_translate_all_blueprints,
    async_translate_all_components,
    # Handlers
    handle_analyze_image,
    handle_generate_image,
    handle_stt_transcribe,
)
from .helpers import translation_placeholders

_LOGGER = logging.getLogger(__name__)

_REGISTERED_HASS: HomeAssistant | None = None
_REGISTERED_ENTRY = None
_SERVICE_CONTEXTS_KEY = f"{DOMAIN}_service_contexts"
_SERVICES_REGISTERED_KEY = f"{DOMAIN}_services_registered"


def _has_configured_api_key(api_key: Any) -> bool:
    """Return whether the resolved API key is a non-empty string."""
    return isinstance(api_key, str) and bool(api_key.strip())


def _register_service(
    hass: HomeAssistant,
    service_name: str,
    handler,
    schema: dict[str, Any],
) -> None:
    """Register a response-capable AI Hub service."""
    hass.services.async_register(
        DOMAIN,
        service_name,
        handler,
        schema=vol.Schema(schema),
        supports_response=True,
    )


def _get_service_contexts(hass: HomeAssistant) -> dict[str, object]:
    """Return the service context registry for this Home Assistant instance."""
    return hass.data.setdefault(_SERVICE_CONTEXTS_KEY, {})


def _entry_has_subentry_type(config_entry: Any, subentry_type: str) -> bool:
    """Return whether the config entry contains the requested subentry type."""
    return any(
        subentry.subentry_type == subentry_type
        for subentry in getattr(config_entry, "subentries", {}).values()
    )


def _resolve_service_entry(
    call: ServiceCall,
    subentry_type: str | None = None,
) -> tuple[HomeAssistant, Any]:
    """Resolve which config entry should handle a service call."""
    hass = _REGISTERED_HASS
    fallback_entry = _REGISTERED_ENTRY
    if hass is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="service_not_initialized",
        )

    contexts = _get_service_contexts(hass)
    explicit_entry_id = call.data.get("config_entry_id")

    if explicit_entry_id:
        config_entry = contexts.get(explicit_entry_id)
        if config_entry is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_entry_not_found",
                translation_placeholders=translation_placeholders(entry_id=explicit_entry_id),
            )
        if subentry_type and not _entry_has_subentry_type(config_entry, subentry_type):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_subentry_missing",
                translation_placeholders=translation_placeholders(subentry_type=subentry_type),
            )
        return hass, config_entry

    candidates = list(contexts.values())
    if subentry_type is not None:
        candidates = [
            config_entry
            for config_entry in candidates
            if _entry_has_subentry_type(config_entry, subentry_type)
        ]

    if not candidates:
        if fallback_entry is not None and (
            subentry_type is None or _entry_has_subentry_type(fallback_entry, subentry_type)
        ):
            return hass, fallback_entry
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="service_no_available_config",
        )

    if len(candidates) > 1:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="service_multiple_configs",
        )

    return hass, candidates[0]


def _resolve_service_config(
    call: ServiceCall,
    subentry_type: str,
    *values: tuple[str, Any],
) -> tuple[HomeAssistant, Any]:
    """Resolve the active config entry and derived runtime config for a service."""
    hass, config_entry = _resolve_service_entry(call, subentry_type)
    return hass, resolve_entry_config(config_entry, subentry_type, *values)


async def _handle_service_with_api_key(
    call: ServiceCall,
    subentry_type: str,
    *values: tuple[str, Any],
    config_mapper,
    handler,
) -> dict:
    """Resolve service config, validate API key, and call handler."""
    hass, config = _resolve_service_config(call, subentry_type, *values)

    handler_args = config_mapper(config)
    effective_key = handler_args[0]
    if not _has_configured_api_key(effective_key):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="service_api_key_not_configured",
        )
    return await handler(hass, call, *handler_args)


async def _handle_translation_service(
    call: ServiceCall,
    service_name: str,
    runner,
    build_runner_kwargs,
) -> dict:
    """Resolve translation config and invoke the requested batch runner."""
    _, config = _resolve_service_config(
        call,
        SUBENTRY_TRANSLATION,
        (CONF_CHAT_URL, AI_HUB_CHAT_URL),
        (CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
    )

    list_mode = bool(call.data.get("list_components") or call.data.get("list_blueprints"))
    chat_url, model, effective_key = config
    if not list_mode and not _has_configured_api_key(effective_key):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="service_api_key_not_configured",
        )

    try:
        runner_kwargs = build_runner_kwargs(call, chat_url, model, effective_key, list_mode)
        result = await runner(**runner_kwargs)
        return {"success": True, "result": result}
    except Exception as exc:
        _LOGGER.error("%s service error: %s", service_name, exc)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="service_execution_failed",
            translation_placeholders=translation_placeholders(
                service_name=service_name,
                error=exc,
            ),
        ) from exc


async def _handle_analyze_image(call: ServiceCall) -> dict:
    """Handle analyze image service calls."""
    return await _handle_service_with_api_key(
        call,
        SUBENTRY_CONVERSATION,
        (CONF_CHAT_URL, AI_HUB_CHAT_URL),
        (CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
        config_mapper=lambda config: (config[2], config[0]),
        handler=handle_analyze_image,
    )


async def _handle_generate_image(call: ServiceCall) -> dict:
    """Handle generate image service calls."""
    return await _handle_service_with_api_key(
        call,
        SUBENTRY_AI_TASK,
        (CONF_IMAGE_URL, AI_HUB_IMAGE_GEN_URL),
        config_mapper=lambda config: (config[1], config[0]),
        handler=handle_generate_image,
    )


async def _handle_stt_transcribe(call: ServiceCall) -> dict:
    """Handle STT transcription service calls."""
    return await _handle_service_with_api_key(
        call,
        SUBENTRY_STT,
        (CONF_STT_URL, SILICONFLOW_ASR_URL),
        config_mapper=lambda config: (config[1], config[0]),
        handler=handle_stt_transcribe,
    )


async def async_setup_services(hass: HomeAssistant, config_entry) -> None:
    """Set up services for AI Hub integration."""

    contexts = _get_service_contexts(hass)
    contexts[config_entry.entry_id] = config_entry
    global _REGISTERED_HASS, _REGISTERED_ENTRY
    _REGISTERED_HASS = hass
    _REGISTERED_ENTRY = next(reversed(contexts.values()), None)

    if hass.data.get(_SERVICES_REGISTERED_KEY):
        _LOGGER.debug("AI Hub services already registered; updated active context")
        return

    # ========== 图像分析服务 ==========
    # ========== STT 语音转文字服务 ==========
    # ========== 组件翻译服务 ==========
    async def _handle_translate_components(call: ServiceCall) -> dict:
        return await _handle_translation_service(
            call,
            "Translation",
            async_translate_all_components,
            lambda current_call, chat_url, model, effective_key, list_mode: {
                "custom_components_path": "custom_components",
                "api_key": effective_key if not list_mode else None,
                "force_translation": current_call.data.get("force_translation", False),
                "target_component": current_call.data.get("target_component", "").strip(),
                "list_components": current_call.data.get("list_components", False),
                "api_url": chat_url,
                "model": model,
            },
        )

    # ========== 蓝图翻译服务 ==========
    async def _handle_translate_blueprints(call: ServiceCall) -> dict:
        return await _handle_translation_service(
            call,
            "Blueprint translation",
            async_translate_all_blueprints,
            lambda current_call, chat_url, model, effective_key, list_mode: {
                "api_key": effective_key if not list_mode else None,
                "retranslate": current_call.data.get("retranslate", False),
                "target_blueprint": current_call.data.get("target_blueprint", "").strip(),
                "list_blueprints": current_call.data.get("list_blueprints", False),
                "blueprints_path": hass.config.path("blueprints"),
                "api_url": chat_url,
                "model": model,
            },
        )

    # ========== 注册所有服务 ==========
    _register_service(hass, SERVICE_ANALYZE_IMAGE, _handle_analyze_image, IMAGE_ANALYZER_SCHEMA)
    _register_service(hass, SERVICE_GENERATE_IMAGE, _handle_generate_image, IMAGE_GENERATOR_SCHEMA)
    _register_service(hass, SERVICE_STT_TRANSCRIBE, _handle_stt_transcribe, STT_SCHEMA)
    _register_service(hass, SERVICE_TRANSLATE_COMPONENTS, _handle_translate_components, TRANSLATION_SCHEMA)
    _register_service(
        hass,
        SERVICE_TRANSLATE_BLUEPRINTS,
        _handle_translate_blueprints,
        BLUEPRINTS_TRANSLATION_SCHEMA,
    )

    hass.data[_SERVICES_REGISTERED_KEY] = True
    _LOGGER.info("AI Hub services registered successfully")


async def async_unload_services(hass: HomeAssistant, entry_id: str | None = None) -> None:
    """Unload all services for AI Hub integration.

    Args:
        hass: Home Assistant instance
    """
    global _REGISTERED_HASS, _REGISTERED_ENTRY

    contexts = _get_service_contexts(hass)
    if entry_id is not None:
        contexts.pop(entry_id, None)
        _REGISTERED_ENTRY = next(reversed(contexts.values()), None) if contexts else None
        if contexts:
            _LOGGER.debug("Skipping AI Hub service unload; other entries still active")
            return

    if not hass.data.get(_SERVICES_REGISTERED_KEY):
        return

    hass.services.async_remove(DOMAIN, SERVICE_ANALYZE_IMAGE)
    hass.services.async_remove(DOMAIN, SERVICE_GENERATE_IMAGE)
    hass.services.async_remove(DOMAIN, SERVICE_STT_TRANSCRIBE)
    hass.services.async_remove(DOMAIN, SERVICE_TRANSLATE_COMPONENTS)
    hass.services.async_remove(DOMAIN, SERVICE_TRANSLATE_BLUEPRINTS)

    if _REGISTERED_HASS is hass:
        _REGISTERED_HASS = None
        _REGISTERED_ENTRY = None

    hass.data.pop(_SERVICES_REGISTERED_KEY, None)
    hass.data.pop(_SERVICE_CONTEXTS_KEY, None)

    _LOGGER.info("AI Hub services unloaded successfully")
