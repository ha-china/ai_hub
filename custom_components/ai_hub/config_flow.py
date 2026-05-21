"""Config flow for AI Hub integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_API_KEY
from .config_flow_schema import (
    SUBENTRY_TYPES,
    ai_hub_config_option_schema,
    get_default_subentry_name,
    get_default_subentry_options,
)
from .config_flow_validation import (
    FLOW_DESCRIPTION_PLACEHOLDERS,
    normalize_subentry_input,
    validate_input,
)
from .model_discovery import async_discover_chat_models
from .consts import (
    CONF_LLM_HASS_API,
    CONF_RECOMMENDED,
    DEFAULT_TITLE,
    DOMAIN,
    LLM_API_ASSIST,
    SUBENTRY_CONVERSATION,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Optional(CONF_API_KEY, default=""): str})


class AIHubConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Hub."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders=FLOW_DESCRIPTION_PLACEHOLDERS,
            )

        user_input = {**user_input}
        user_input[CONF_API_KEY] = user_input.get(CONF_API_KEY, "").strip()

        errors: dict[str, str] = {}

        try:
            await validate_input(self.hass, user_input)
        except ValueError as err:
            reason = str(err)
            if reason in {"invalid_auth", "cannot_connect"}:
                errors["base"] = reason
            else:
                _LOGGER.exception("Unexpected validation error: %s", err)
                errors["base"] = "unknown"
        except aiohttp.ClientError:
            _LOGGER.exception("Cannot connect")
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=DEFAULT_TITLE, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders=FLOW_DESCRIPTION_PLACEHOLDERS,
        )

    @classmethod
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        del config_entry
        return {
            subentry_type: AIHubSubentryFlowHandler
            for subentry_type in SUBENTRY_TYPES.values()
        }


class AIHubSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for AI Hub subentries."""

    options: dict[str, Any]
    last_rendered_recommended: bool = False
    chat_model_options: list[str] | None = None

    def _should_refresh_model_options(self, user_input: dict[str, Any]) -> bool:
        """Return whether the form should refresh model options before saving."""
        if self._subentry_type not in {SUBENTRY_CONVERSATION, SUBENTRY_TYPES["translation"]}:
            return False

        watched_keys = ("llm_provider", "chat_url", "custom_api_key")
        return any(self.options.get(key) != user_input.get(key) for key in watched_keys)

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle options for a subentry."""
        errors: dict[str, str] = {}

        if user_input is None:
            if self._is_new:
                self.options = get_default_subentry_options(self._subentry_type)
            else:
                self.options = self._get_reconfigure_subentry().data.copy()

            self.last_rendered_recommended = self.options.get(CONF_RECOMMENDED, True)
        else:
            if user_input[CONF_RECOMMENDED] == self.last_rendered_recommended:
                if self._should_refresh_model_options(user_input):
                    self.options.update(user_input)
                    self.chat_model_options = await async_discover_chat_models(self.options)
                    schema = await ai_hub_config_option_schema(
                        self._is_new,
                        self._subentry_type,
                        self.options,
                        chat_model_options=self.chat_model_options,
                    )
                    return self.async_show_form(
                        step_id="init",
                        data_schema=vol.Schema(schema),
                        errors=errors,
                        description_placeholders=FLOW_DESCRIPTION_PLACEHOLDERS,
                    )

                try:
                    # Merge existing options with user input to preserve values not shown in current form
                    # This is important when recommended mode hides advanced fields
                    processed_input = {**self.options, **user_input}

                    if self._subentry_type == SUBENTRY_CONVERSATION:
                        processed_input[CONF_LLM_HASS_API] = [LLM_API_ASSIST]

                    processed_input = await normalize_subentry_input(self.hass, processed_input)
                except ValueError as err:
                    reason = str(err)
                    if reason == "invalid_auth":
                        errors["base"] = "invalid_auth"
                    elif reason.startswith("cannot_connect"):
                        errors["base"] = "cannot_connect"
                    else:
                        _LOGGER.exception("Unexpected subentry validation error: %s", err)
                        errors["base"] = "unknown"
                else:
                    if self._is_new:
                        return self.async_create_entry(
                            title=get_default_subentry_name(
                                self._subentry_type,
                                processed_input,
                            ),
                            data=processed_input,
                        )

                    return self.async_update_and_abort(
                        self._get_entry(),
                        self._get_reconfigure_subentry(),
                        title=get_default_subentry_name(
                            self._subentry_type,
                            processed_input,
                        ),
                        data=processed_input,
                    )

            self.last_rendered_recommended = user_input[CONF_RECOMMENDED]
            # Preserve existing options when switching modes, only update fields present in user_input
            # This ensures previously configured values are not lost when toggling recommended mode
            for key, value in user_input.items():
                self.options[key] = value

        self.chat_model_options = await async_discover_chat_models(self.options)

        schema = await ai_hub_config_option_schema(
            self._is_new,
            self._subentry_type,
            self.options,
            chat_model_options=self.chat_model_options,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders=FLOW_DESCRIPTION_PLACEHOLDERS,
        )

    async_step_reconfigure = async_step_init
    async_step_user = async_step_init
