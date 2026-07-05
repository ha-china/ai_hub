"""The AI Hub integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, TypeAlias

import aiohttp

try:
    from homeassistant.config_entries import ConfigEntry, ConfigSubentry
    from homeassistant.const import CONF_API_KEY, Platform
    from homeassistant.core import HomeAssistant
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
    from homeassistant.helpers import device_registry as dr, entity_registry as er
except ModuleNotFoundError:  # pragma: no cover - used only in lightweight test environments
    ConfigEntry = Any  # type: ignore[assignment]
    ConfigSubentry = Any  # type: ignore[assignment]
    HomeAssistant = Any  # type: ignore[assignment]
    CONF_API_KEY = "api_key"
    dr = None  # type: ignore[assignment]
    er = None  # type: ignore[assignment]

    class ConfigEntryAuthFailed(Exception):
        """Fallback exception when Home Assistant is not installed."""

    class ConfigEntryNotReady(Exception):
        """Fallback exception when Home Assistant is not installed."""

    Platform = None  # type: ignore[assignment]

from .consts import DOMAIN

_LOGGER = logging.getLogger(__name__)

if Platform is None:
    PLATFORMS: list[Any] = []
else:
    PLATFORMS = [
        Platform.CONVERSATION,
        Platform.AI_TASK,
        Platform.TTS,
        Platform.STT,
        Platform.BUTTON,
    ]

AIHubConfigEntry: TypeAlias = ConfigEntry  # Store API key


@dataclass
class AIHubData:
    """Runtime data for AI Hub integration.

    This class holds all runtime state for the integration,
    avoiding global variables and ensuring proper cleanup on reload.
    """

    api_key: str | None = None
    tts_cache: Any = None
    provider_registry: Any = None
    stats: dict[str, Any] = field(default_factory=dict)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.tts_cache is not None:
            self.tts_cache.clear()
        self.provider_registry = None


def get_ai_hub_data(hass: HomeAssistant) -> AIHubData | None:
    """Get AI Hub runtime data."""
    return hass.data.get(DOMAIN)


def get_configured_api_key(entry: ConfigEntry) -> str:
    """Return the configured main API key from options or entry data."""
    api_key = entry.options.get(CONF_API_KEY) or entry.data.get(CONF_API_KEY) or ""
    return api_key.strip() if isinstance(api_key, str) else str(api_key).strip()


def get_or_create_ai_hub_data(hass: HomeAssistant) -> AIHubData:
    """Get or create AI Hub runtime data."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = AIHubData()
    return hass.data[DOMAIN]


def get_provider_registry(hass: HomeAssistant):
    """Get or create the provider registry for this Home Assistant instance.

    This ensures proper lifecycle management - the registry is cleaned up
    when the integration is unloaded.

    Args:
        hass: Home Assistant instance

    Returns:
        UnifiedProviderRegistry instance
    """
    from .providers import get_registry

    ai_hub_data = get_or_create_ai_hub_data(hass)
    if ai_hub_data.provider_registry is None:
        ai_hub_data.provider_registry = get_registry()
    return ai_hub_data.provider_registry


def _build_initial_subentries(api_key: str) -> list[ConfigSubentry]:
    """Build default subentries for a newly created integration entry."""
    from .config_flow_schema import get_default_subentry_options
    from .consts import (
        SUBENTRY_AI_TASK,
        SUBENTRY_CONVERSATION,
        SUBENTRY_STT,
        SUBENTRY_TRANSLATION,
        SUBENTRY_TTS,
        get_default_service_name,
    )

    if not api_key:
        return []

    conversation_options = get_default_subentry_options(SUBENTRY_CONVERSATION)
    ai_task_options = get_default_subentry_options(SUBENTRY_AI_TASK)
    tts_options = get_default_subentry_options(SUBENTRY_TTS)
    stt_options = get_default_subentry_options(SUBENTRY_STT)
    translation_options = get_default_subentry_options(SUBENTRY_TRANSLATION)

    subentries = [
        ConfigSubentry(
            data=conversation_options,
            subentry_type=SUBENTRY_CONVERSATION,
            title=get_default_service_name("conversation", conversation_options),
            unique_id=None,
        )
    ]

    subentries.extend(
        [
            ConfigSubentry(
                data=ai_task_options,
                subentry_type=SUBENTRY_AI_TASK,
                title=get_default_service_name("ai_task", ai_task_options),
                unique_id=None,
            ),
            ConfigSubentry(
                data=tts_options,
                subentry_type=SUBENTRY_TTS,
                title=get_default_service_name("tts", tts_options),
                unique_id=None,
            ),
            ConfigSubentry(
                data=stt_options,
                subentry_type=SUBENTRY_STT,
                title=get_default_service_name("stt", stt_options),
                unique_id=None,
            ),
            ConfigSubentry(
                data=translation_options,
                subentry_type=SUBENTRY_TRANSLATION,
                title=get_default_service_name("translation", translation_options),
                unique_id=None,
            ),
        ]
    )
    return subentries


def _ensure_initial_subentries(hass: HomeAssistant, entry: ConfigEntry, api_key: str) -> None:
    """Create the initial service subentries when the entry has none."""
    if getattr(entry, "subentries", None):
        return

    for subentry in _build_initial_subentries(api_key):
        hass.config_entries.async_add_subentry(entry, subentry)


async def _async_remove_legacy_diagnostic_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Remove legacy AI Hub Diagnostic entities and device for existing users."""
    if er is None or dr is None:
        return

    entity_registry = er.async_get(hass)
    legacy_unique_ids = {
        f"{DOMAIN}_{entry.entry_id}_health_sensor",
        f"{DOMAIN}_{entry.entry_id}_siliconflow_latency",
        f"{DOMAIN}_{entry.entry_id}_edge_tts_latency",
    }

    for entity_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity_entry.unique_id in legacy_unique_ids:
            entity_registry.async_remove(entity_entry.entity_id)

    device_registry = dr.async_get(hass)
    legacy_device = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{entry.entry_id}_diagnostic")}
    )
    if legacy_device is not None:
        device_registry.async_remove_device(legacy_device.id)


async def async_setup_entry(hass: HomeAssistant, entry: AIHubConfigEntry) -> bool:
    """Set up AI Hub from a config entry."""

    # Get API key (may be None if not provided)
    # No startup validation - each entity validates on actual use
    api_key = get_configured_api_key(entry)

    # Initialize runtime data in hass.data
    ai_hub_data = get_or_create_ai_hub_data(hass)
    ai_hub_data.api_key = api_key

    # Store in entry.runtime_data
    entry.runtime_data = api_key

    _ensure_initial_subentries(hass, entry, api_key)
    await _async_remove_legacy_diagnostic_entities(hass, entry)

    # Each step is independent - one failure does not block others
    try:
        from .intents.loader import async_sync_intent_lists
        await async_sync_intent_lists(hass)
    except Exception as err:
        _LOGGER.warning("Intent list sync failed (non-fatal): %s", err)

    try:
        from .intents import async_setup_intents
        await async_setup_intents(hass)
    except Exception as err:
        _LOGGER.warning("Intent handlers setup failed (non-fatal): %s", err)

    try:
        from .services import async_setup_services
        await async_setup_services(hass, entry)
    except Exception as err:
        _LOGGER.warning("Services setup failed (non-fatal): %s", err)

    # Forward setup to platforms individually - one failure should not block others
    for platform in PLATFORMS:
        try:
            await hass.config_entries.async_forward_entry_setups(entry, [platform])
        except Exception as err:
            _LOGGER.warning("Platform %s setup failed (others continue): %s", platform, err)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AIHubConfigEntry) -> bool:
    """Unload a config entry."""
    remaining_entries = [
        config_entry
        for config_entry in hass.config_entries.async_entries(DOMAIN)
        if config_entry.entry_id != entry.entry_id
    ]

    all_ok = True
    for platform in PLATFORMS:
        try:
            if not await hass.config_entries.async_unload_platforms(entry, [platform]):
                _LOGGER.warning("Failed to unload platform %s", platform)
                all_ok = False
        except Exception as err:
            _LOGGER.warning("Error unloading platform %s: %s", platform, err)
            all_ok = False

    from .services import async_unload_services
    await async_unload_services(hass, entry.entry_id)

    if not remaining_entries:
        ai_hub_data = get_ai_hub_data(hass)
        if ai_hub_data is not None:
            ai_hub_data.cleanup()
            hass.data.pop(DOMAIN, None)

    return all_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from version %s.%s", entry.version, entry.minor_version)

    if entry.version == 1:
        # Migrate from version 1 to version 2
        # Version 2 uses subentries for conversation and ai_task
        new_data = {**entry.data}
        new_options = {**entry.options}

        # Create default subentries
        from homeassistant.helpers import llm

        from .consts import (
            CONF_CHAT_MODEL,
            CONF_LLM_HASS_API,
            CONF_MAX_TOKENS,
            CONF_PROMPT,
            CONF_RECOMMENDED,
            CONF_TEMPERATURE,
            CONF_TOP_P,
            LEGACY_AI_TASK_TITLES,
            LEGACY_CONVERSATION_TITLES,
            LLM_API_ASSIST,
            RECOMMENDED_AI_TASK_MAX_TOKENS,
            RECOMMENDED_AI_TASK_MODEL,
            RECOMMENDED_AI_TASK_TEMPERATURE,
            RECOMMENDED_AI_TASK_TOP_P,
            RECOMMENDED_CHAT_MODEL,
            RECOMMENDED_MAX_TOKENS,
            RECOMMENDED_TEMPERATURE,
            RECOMMENDED_TOP_P,
            SUBENTRY_AI_TASK,
            SUBENTRY_CONVERSATION,
            get_default_service_name,
        )

        # Create conversation subentry from old options
        conversation_data = {
            CONF_RECOMMENDED: new_options.get(CONF_RECOMMENDED, True),
            CONF_CHAT_MODEL: new_options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            CONF_TEMPERATURE: new_options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
            CONF_TOP_P: new_options.get(CONF_TOP_P, RECOMMENDED_TOP_P),
            CONF_MAX_TOKENS: new_options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
            CONF_PROMPT: new_options.get(CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT),
            CONF_LLM_HASS_API: new_options.get(CONF_LLM_HASS_API, [LLM_API_ASSIST]),
        }

        # Create AI task subentry with defaults
        ai_task_data = {
            CONF_RECOMMENDED: True,
            CONF_CHAT_URL: AI_HUB_CHAT_URL,
            CONF_CHAT_MODEL: RECOMMENDED_AI_TASK_MODEL,
            CONF_TEMPERATURE: RECOMMENDED_AI_TASK_TEMPERATURE,
            CONF_TOP_P: RECOMMENDED_AI_TASK_TOP_P,
            CONF_MAX_TOKENS: RECOMMENDED_AI_TASK_MAX_TOKENS,
        }

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            options={},
            version=2,
            minor_version=2,
        )

        # Add subentries
        conversation_subentry = ConfigSubentry(
            data=conversation_data,
            subentry_type=SUBENTRY_CONVERSATION,
            title=get_default_service_name("conversation", conversation_data),
            unique_id=None,
        )
        hass.config_entries.async_add_subentry(entry, conversation_subentry)

        ai_task_subentry = ConfigSubentry(
            data=ai_task_data,
            subentry_type=SUBENTRY_AI_TASK,
            title=get_default_service_name("ai_task", ai_task_data),
            unique_id=None,
        )
        hass.config_entries.async_add_subentry(entry, ai_task_subentry)

        _LOGGER.debug("Migration to version %s.%s successful", entry.version, entry.minor_version)

    if entry.version == 2 and entry.minor_version == 1:
        # Migrate from version 2.1 to 2.2
        # Update subentry titles
        from .consts import get_default_service_name

        for subentry in entry.subentries.values():
            # Update old titles to new format
            if subentry.subentry_type == SUBENTRY_CONVERSATION:
                if subentry.title in LEGACY_CONVERSATION_TITLES:
                    hass.config_entries.async_update_subentry(
                        entry,
                        subentry.subentry_id,
                        title=get_default_service_name("conversation", subentry.data),
                    )
            elif subentry.subentry_type == SUBENTRY_AI_TASK:
                if subentry.title in LEGACY_AI_TASK_TITLES:
                    hass.config_entries.async_update_subentry(
                        entry,
                        subentry.subentry_id,
                        title=get_default_service_name("ai_task", subentry.data),
                    )

        hass.config_entries.async_update_entry(
            entry,
            minor_version=2,
        )

        _LOGGER.debug("Migration to version %s.%s successful", entry.version, entry.minor_version)

    if entry.version == 2 and entry.minor_version == 2:
        # Migrate from version 2.2 to version 2.3
        # Force the AI Task subentry title to the fixed name "AI Task" and
        # rename the existing AI Task entity_registry entry to the fixed
        # entity_id `ai_task.ai_task`. Previously the entity_id was derived
        # from the provider/model (e.g. `ai_task.siliconflow_qwen3_8b`) and
        # changed whenever the model or provider changed, breaking automations
        # that referenced the entity by entity_id.
        from .consts import SUBENTRY_AI_TASK

        fixed_ai_task_title = "AI Task"
        for subentry in entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_AI_TASK:
                continue
            if subentry.title != fixed_ai_task_title:
                hass.config_entries.async_update_subentry(
                    entry,
                    subentry.subentry_id,
                    title=fixed_ai_task_title,
                )

        # Rename the existing AI Task entity_registry entry to the fixed
        # entity_id `ai_task.ai_task` (domain must stay the same; the public
        # `async_update_entity(new_entity_id=...)` enforces this and is the
        # supported way to rename an entity_id in-place, preserving state).
        target_ai_task_entity_id = "ai_task.ai_task"
        registry = er.async_get(hass)
        for entity_entry in er.async_entries_for_config_entry(
            registry, entry.entry_id
        ):
            if entity_entry.domain != "ai_task":
                continue
            if entity_entry.entity_id == target_ai_task_entity_id:
                continue  # Already the fixed entity_id; keep it.
            try:
                registry.async_update_entity(
                    entity_entry.entity_id,
                    new_entity_id=target_ai_task_entity_id,
                )
                _LOGGER.info(
                    "Pinned AI Task entity_id: %s -> %s",
                    entity_entry.entity_id,
                    target_ai_task_entity_id,
                )
            except ValueError as err:
                # The target entity_id may already be taken by another (e.g.
                # a freshly-set-up) AI Task entity, or another entry on the
                # same domain. Log and continue rather than failing migration.
                _LOGGER.warning(
                    "Failed to pin AI Task entity_id %s -> %s: %s",
                    entity_entry.entity_id,
                    target_ai_task_entity_id,
                    err,
                )

        hass.config_entries.async_update_entry(
            entry,
            minor_version=3,
        )

        _LOGGER.debug("Migration to version %s.%s successful", entry.version, entry.minor_version)

    return True
