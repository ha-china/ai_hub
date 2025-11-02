"""Button platform for AI Hub WeChat notifications."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_entry_flow
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr
from datetime import datetime

# Import constants
try:
    from ..const import DOMAIN
except ImportError:
    # Fallback for testing
    DOMAIN = "ai_hub"


_LOGGER = logging.getLogger(__name__)


class AIHubWeChatButton(ButtonEntity):
    """AI Hub WeChat test button."""

    _attr_has_entity_name = False
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wechat"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, subentry: config_entry_flow.ConfigSubentry) -> None:
        """Initialize the button."""
        super().__init__()

        self._hass = hass
        self._subentry = subentry

        # Use subentry ID as base unique_id
        self._attr_unique_id = f"{subentry.subentry_id}_wechat_test"
        self._attr_name = "微信消息测试"

        # Set device info to match existing device exactly
        # This should make the button associate with the existing WeChat device
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="老王杂谈说",  # Match existing device
            model="WeChat Notification",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Press the button - send a test message."""
        try:
            _LOGGER.info("WeChat test button pressed, sending test message")
            result = await self._hass.services.async_call(
                "ai_hub",
                "send_wechat_message",
                {
                    "device_entity": "sun.sun",
                    "message": f"🤖 AI Hub 微信测试 - 时间: {datetime.now().strftime('%H:%M:%S')}",
                    "group": "test",
                    "url": ""
                },
                blocking=True,
                return_response=True,
            )
            _LOGGER.info("WeChat test message sent successfully: %s", result)
        except Exception as e:
            _LOGGER.error("Failed to send test WeChat message: %s", e)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AI Hub WeChat button platform."""
    _LOGGER.info("=== WECHAT BUTTON SETUP START ===")
    _LOGGER.info("Setting up WeChat button platform for entry: %s", entry.entry_id)
    buttons = []

    # Only proceed if we have subentries
    if not hasattr(entry, 'subentries') or not entry.subentries:
        _LOGGER.warning("No subentries found for WeChat button setup")
        _LOGGER.info("=== WECHAT BUTTON SETUP END - NO SUBENTRIES ===")
        return

    _LOGGER.info("Found %d subentries for WeChat button setup", len(entry.subentries))

    # List all subentries for debugging
    for subentry in entry.subentries.values():
        _LOGGER.info("Subentry: %s, type: %s, title: %s", subentry.subentry_id, subentry.subentry_type, subentry.title)

    # Create buttons for each WeChat subentry
    wechat_found = False
    for subentry in entry.subentries.values():
        _LOGGER.debug("Checking subentry: %s, type: %s", subentry.subentry_id, subentry.subentry_type)
        if subentry.subentry_type == "wechat":
            wechat_found = True
            _LOGGER.info("Found WeChat subentry: %s, creating button", subentry.subentry_id)
            button = AIHubWeChatButton(hass, entry, subentry)
            buttons.append(button)
            _LOGGER.info("Created WeChat test button for subentry: %s", subentry.subentry_id)
            _LOGGER.info("Button unique_id: %s", button._attr_unique_id)
            _LOGGER.info("Button device_info: %s", button._attr_device_info)
        else:
            _LOGGER.debug("Skipping non-wechat subentry: %s", subentry.subentry_type)

    if buttons:
        _LOGGER.info("Adding %d WeChat test button(s) to Home Assistant", len(buttons))
        # Add buttons with subentry_id to ensure proper subentry association
        for button in buttons:
            _LOGGER.info("Adding button with subentry_id: %s", button._subentry.subentry_id)
            async_add_entities([button], config_subentry_id=button._subentry.subentry_id)
        _LOGGER.info("Successfully added %d WeChat test button(s)", len(buttons))
    else:
        if not wechat_found:
            _LOGGER.info("No WeChat subentries found, no test buttons created")
        else:
            _LOGGER.warning("WeChat subentries found but no buttons were created!")

    _LOGGER.info("=== WECHAT BUTTON SETUP END ===")