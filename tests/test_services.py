"""Tests for the AI Hub services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.ai_hub.const import (
    CONF_API_KEY,
    CONF_CHAT_MODEL,
    CONF_CHAT_URL,
    CONF_CUSTOM_API_KEY,
    CONF_IMAGE_URL,
    CONF_PROMPT,
    RECOMMENDED_CHAT_MODEL,
    SERVICE_ANALYZE_IMAGE,
    SERVICE_GENERATE_IMAGE,
    SERVICE_STT_TRANSCRIBE,
    SERVICE_TRANSLATE_BLUEPRINTS,
    SERVICE_TRANSLATE_COMPONENTS,
)
from custom_components.ai_hub.services import (
    _get_conversation_config,
    _get_image_config,
    async_setup_services,
    async_unload_services,
)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = MagicMock()
    hass.services.async_register = MagicMock()
    hass.services.async_remove = MagicMock()
    hass.config.path = MagicMock(return_value="/config")
    return hass


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with subentries."""
    conversation_subentry = ConfigSubentry(
        subentry_type="conversation",
        title="AI Hub对话助手",
        data={
            "recommended": True,
            CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
            CONF_CHAT_URL: "https://api.siliconflow.cn/v1/chat/completions",
            CONF_CUSTOM_API_KEY: "",
            CONF_PROMPT: "You are a helpful AI assistant.",
        },
        unique_id=None,
    )

    ai_task_subentry = ConfigSubentry(
        subentry_type="ai_task_data",
        title="AI Hub AI任务",
        data={
            "recommended": True,
            CONF_IMAGE_URL: "https://api.siliconflow.cn/v1/images/generations",
            CONF_CUSTOM_API_KEY: "",
        },
        unique_id=None,
    )

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.runtime_data = "test_api_key_12345"
    entry.data = {
        CONF_API_KEY: "test_api_key_12345",
    }
    entry.subentries = {
        "conversation": conversation_subentry,
        "ai_task": ai_task_subentry,
    }

    return entry


class TestGetConversationConfig:
    """Tests for _get_conversation_config function."""

    def test_get_config_from_subentry(self, mock_config_entry):
        """Test getting config from conversation subentry."""
        chat_url, model, api_key = _get_conversation_config(mock_config_entry)

        assert chat_url == "https://api.siliconflow.cn/v1/chat/completions"
        assert model == RECOMMENDED_CHAT_MODEL
        assert api_key == "test_api_key_12345"

    def test_get_config_with_custom_api_key(self, mock_config_entry):
        """Test getting config with custom API key."""
        # Update subentry with custom API key
        subentry = mock_config_entry.subentries["conversation"]
        subentry.data[CONF_CUSTOM_API_KEY] = "custom_api_key_789"

        chat_url, model, api_key = _get_conversation_config(mock_config_entry)

        assert api_key == "custom_api_key_789"

    def test_get_config_no_subentry(self, mock_config_entry):
        """Test getting config when no conversation subentry exists."""
        mock_config_entry.subentries = {}

        chat_url, model, api_key = _get_conversation_config(mock_config_entry)

        # Should return defaults
        assert chat_url is not None
        assert model == RECOMMENDED_CHAT_MODEL
        assert api_key is None


class TestGetImageConfig:
    """Tests for _get_image_config function."""

    def test_get_config_from_subentry(self, mock_config_entry):
        """Test getting config from AI task subentry."""
        image_url, api_key = _get_image_config(mock_config_entry)

        assert image_url == "https://api.siliconflow.cn/v1/images/generations"
        assert api_key == "test_api_key_12345"

    def test_get_config_with_custom_api_key(self, mock_config_entry):
        """Test getting config with custom API key."""
        # Update subentry with custom API key
        subentry = mock_config_entry.subentries["ai_task"]
        subentry.data[CONF_CUSTOM_API_KEY] = "custom_image_api_key"

        image_url, api_key = _get_image_config(mock_config_entry)

        assert api_key == "custom_image_api_key"

    def test_get_config_no_subentry(self, mock_config_entry):
        """Test getting config when no AI task subentry exists."""
        mock_config_entry.subentries = {}

        image_url, api_key = _get_image_config(mock_config_entry)

        # Should return defaults
        assert image_url is not None
        assert api_key is None


class TestAsyncSetupServices:
    """Tests for async_setup_services function."""

    @pytest.mark.asyncio
    async def test_setup_all_services(self, mock_hass, mock_config_entry):
        """Test setting up all services."""
        with patch("custom_components.ai_hub.services.handle_analyze_image") as mock_analyze, \
             patch("custom_components.ai_hub.services.handle_generate_image") as mock_generate, \
             patch("custom_components.ai_hub.services.handle_stt_transcribe") as mock_stt, \
             patch("custom_components.ai_hub.services.async_translate_all_components") as mock_translate, \
             patch("custom_components.ai_hub.services.async_translate_all_blueprints") as mock_blueprints:

            mock_analyze.return_value = AsyncMock(return_value={"success": True})
            mock_generate.return_value = AsyncMock(return_value={"success": True})
            mock_stt.return_value = AsyncMock(return_value={"success": True})
            mock_translate.return_value = AsyncMock(return_value={"success": True, "result": {}})
            mock_blueprints.return_value = AsyncMock(return_value={"success": True, "result": {}})

            await async_setup_services(mock_hass, mock_config_entry)

            # Verify all services were registered
            service_calls = [
                call[0] for call in mock_hass.services.async_register.call_args_list
            ]
            registered_services = [call[1] for call in service_calls]

            assert SERVICE_ANALYZE_IMAGE in registered_services
            assert SERVICE_GENERATE_IMAGE in registered_services
            assert SERVICE_STT_TRANSCRIBE in registered_services
            assert SERVICE_TRANSLATE_COMPONENTS in registered_services
            assert SERVICE_TRANSLATE_BLUEPRINTS in registered_services

    @pytest.mark.asyncio
    async def test_translate_components_service_list_only(self, mock_hass, mock_config_entry):
        """Test translation service in list-only mode."""
        with patch("custom_components.ai_hub.services.async_translate_all_components") as mock_translate:
            mock_translate.return_value = AsyncMock(return_value={
                "components": [
                    {"name": "test_component", "has_translation": False}
                ]
            })

            await async_setup_services(mock_hass, mock_config_entry)

            # Get the translation service handler
            translate_handlers = [
                call for call in mock_hass.services.async_register.call_args_list
                if len(call) > 1 and call[1] == SERVICE_TRANSLATE_COMPONENTS
            ]

            if translate_handlers:
                handler = translate_handlers[0][2]
                mock_call = MagicMock(spec=ServiceCall)
                mock_call.data = {"list_components": True}

                result = await handler(mock_call)

                assert result["success"] is True
                mock_translate.assert_called_once()


class TestAsyncUnloadServices:
    """Tests for async_unload_services function."""

    @pytest.mark.asyncio
    async def test_unload_all_services(self, mock_hass):
        """Test unloading all services."""
        await async_unload_services(mock_hass)

        # Verify all services were removed
        service_calls = [
            call[0] for call in mock_hass.services.async_remove.call_args_list
        ]
        removed_services = [call[1] for call in service_calls]

        assert SERVICE_ANALYZE_IMAGE in removed_services
        assert SERVICE_GENERATE_IMAGE in removed_services
        assert SERVICE_STT_TRANSCRIBE in removed_services
        assert SERVICE_TRANSLATE_COMPONENTS in removed_services
        assert SERVICE_TRANSLATE_BLUEPRINTS in removed_services

    @pytest.mark.asyncio
    async def test_unload_services_no_old_services(self, mock_hass):
        """Test that old TTS services are not removed (they don't exist anymore)."""
        await async_unload_services(mock_hass)

        # Verify we don't try to remove old services
        all_removed = [
            call[1] for call in mock_hass.services.async_remove.call_args_list
        ]

        # Old services should not be in the removal list
        assert "tts_speech" not in all_removed
        assert "tts_stream" not in all_removed


class TestServiceHandlers:
    """Tests for individual service handlers."""

    @pytest.mark.asyncio
    async def test_analyze_image_no_api_key(self, mock_hass):
        """Test analyze image service with no API key."""
        from custom_components.ai_hub.services import _handle_analyze_image

        entry = MagicMock(spec=ConfigEntry)
        entry.runtime_data = None
        entry.subentries = {}

        mock_call = MagicMock(spec=ServiceCall)
        mock_call.data = {"image_file": "/path/to/image.jpg", "message": "Describe this"}

        with patch("custom_components.ai_hub.services._get_conversation_config") as mock_config:
            mock_config.return_value = ("url", "model", None)

            result = await _handle_analyze_image(mock_call)

            assert result["success"] is False
            assert "API密钥未配置" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_image_no_api_key(self, mock_hass):
        """Test generate image service with no API key."""
        from custom_components.ai_hub.services import _handle_generate_image

        entry = MagicMock(spec=ConfigEntry)
        entry.runtime_data = None
        entry.subentries = {}

        mock_call = MagicMock(spec=ServiceCall)
        mock_call.data = {"prompt": "A beautiful sunset"}

        with patch("custom_components.ai_hub.services._get_image_config") as mock_config:
            mock_config.return_value = ("url", None)

            result = await _handle_generate_image(mock_call)

            assert result["success"] is False
            assert "API密钥未配置" in result["error"]

    @pytest.mark.asyncio
    async def test_stt_transcribe_no_api_key(self, mock_hass):
        """Test STT service with no API key."""
        from custom_components.ai_hub.services import _handle_stt_transcribe

        entry = MagicMock(spec=ConfigEntry)
        entry.data = {CONF_API_KEY: ""}

        mock_call = MagicMock(spec=ServiceCall)
        mock_call.data = {"file": "/path/to/audio.wav"}

        result = await _handle_stt_transcribe(mock_call)

        assert result["success"] is False
        assert "API密钥未配置" in result["error"]
