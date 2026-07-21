"""Base entity for AI Hub integration."""

from __future__ import annotations

import json
import logging
import re
import asyncio

import aiohttp
from collections.abc import AsyncGenerator, Callable
from typing import Any

from homeassistant.components import conversation
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_entry_flow, llm
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.util import ulid
from .providers import LLMMessage, create_provider
from .http import FirstChunkTimeoutError
from .consts import (
    CONF_CHAT_MODEL,
    CONF_CHAT_URL,
    CONF_LLM_PROVIDER,
    CONF_CUSTOM_API_KEY,
    CONF_DEBUG_LOG,
    CONF_ENABLE_THINKING,
    CONF_MAX_HISTORY_MESSAGES,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    DOMAIN,
    ERROR_GETTING_RESPONSE,
    RECOMMENDED_IMAGE_ANALYSIS_MODEL,
    RECOMMENDED_DEBUG_LOG,
    RECOMMENDED_ENABLE_THINKING,
    RECOMMENDED_MAX_HISTORY_MESSAGES,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    TIMEOUT_CHAT_API,
)
from .http import resolve_provider_name
from .helpers import translation_placeholders
from .llm_attachment_processor import AttachmentProcessor
from .llm_message_builder import ChatMessageBuilder
from .llm_model_utils import chat_log_has_media_attachments, select_media_model

_LOGGER = logging.getLogger(__name__)


def _format_request_exception(
    err: Exception,
    *,
    provider_name: str,
    api_url: str,
    timeout_seconds: float | int | None = None,
) -> str:
    """Build a non-empty, actionable error message for LLM request failures."""
    err_type = type(err).__name__
    err_text = str(err).strip()

    if isinstance(err, asyncio.TimeoutError):
        timeout_hint = f" after {timeout_seconds}s" if timeout_seconds else ""
        return (
            f"{ERROR_GETTING_RESPONSE}: {err_type}: request to {provider_name} "
            f"endpoint {api_url} timed out{timeout_hint}"
        )

    if err_text:
        return f"{ERROR_GETTING_RESPONSE}: {err_type}: {err_text}"

    return f"{ERROR_GETTING_RESPONSE}: {err_type}: request to {provider_name} endpoint {api_url} failed"


class _AIHubEntityMixin:
    """Mixin class providing common initialization logic for AI Hub entities.

    This mixin provides shared initialization behavior for all AI Hub entity types:
    - LLM conversation entities
    - TTS entities
    - STT entities

    Attributes:
        entry: The config entry
        subentry: The subentry for this entity instance
        default_model: The default model to use
        _api_key: The API key for this entity
    """

    _attr_has_entity_name = False
    _attr_should_poll = False

    def _initialize_aihub_entity(
        self,
        entry: config_entry_flow.ConfigEntry,
        subentry: config_entry_flow.ConfigSubentry,
        default_model: str,
        *,
        warn_on_missing_api_key: bool = True,
    ) -> None:
        """Initialize common AI Hub entity attributes.

        This method should be called from the entity's __init__ method.

        Args:
            entry: The config entry
            subentry: The subentry for this entity instance
            default_model: The default model to use
        """
        self.entry = entry
        self.subentry = subentry
        self.default_model = default_model
        self._attr_unique_id = subentry.subentry_id
        self._attr_name = subentry.title

        # Get API key: use custom key if provided, otherwise use main key
        custom_key_raw = subentry.data.get(CONF_CUSTOM_API_KEY, "")
        custom_key = str(custom_key_raw).strip() if custom_key_raw else ""
        main_key = entry.runtime_data if entry.runtime_data else ""
        # Ensure API key is always a string
        if custom_key:
            self._api_key = custom_key
        elif isinstance(main_key, str) and main_key.strip():
            self._api_key = main_key
        else:
            self._api_key = ""
            if warn_on_missing_api_key:
                _LOGGER.warning("No valid API key found for entity %s", subentry.title)

    def _get_device_model(self, default_model: str) -> str:
        """Get the device model for device info.

        Can be overridden by subclasses to provide custom model validation.

        Args:
            default_model: The default model to use if no model is configured

        Returns:
            The model name to use for device info
        """
        return self.subentry.data.get(CONF_CHAT_MODEL, default_model)

    def _create_device_info(self, domain: str) -> dr.DeviceInfo:
        """Create device info for this entity.

        Args:
            domain: The domain for this integration

        Returns:
            DeviceInfo object
        """
        return dr.DeviceInfo(
            identifiers={(domain, self.subentry.subentry_id)},
            name=self.subentry.title,
            manufacturer="Home Assistant China (unofficial)",
            model=self._get_device_model(self.default_model),
            entry_type=dr.DeviceEntryType.SERVICE,
        )


class AIHubBaseLLMEntity(Entity, _AIHubEntityMixin):
    """Base entity for AI Hub LLM."""

    def __init__(
        self,
        entry: config_entry_flow.ConfigEntry,
        subentry: config_entry_flow.ConfigSubentry,
        default_model: str,
        *,
        warn_on_missing_api_key: bool = True,
    ) -> None:
        """Initialize the entity."""
        # Use mixin initialization
        self._initialize_aihub_entity(
            entry,
            subentry,
            default_model,
            warn_on_missing_api_key=warn_on_missing_api_key,
        )
        # Create device info using mixin method
        self._attr_device_info = self._create_device_info(DOMAIN)

    def _get_device_model(self, default_model: str) -> str:
        """Get the device model with validation for LLM entities.

        Args:
            default_model: The default model to use if no model is configured

        Returns:
            The validated model name to use for device info
        """
        device_model = self.subentry.data.get(CONF_CHAT_MODEL) or default_model
        if not isinstance(device_model, str) or not device_model.strip():
            device_model = default_model
        return device_model

    def _get_model_config(self, chat_log: conversation.ChatLog | None = None) -> dict[str, Any]:
        """Get model configuration from options."""
        options = self.subentry.data
        configured_model = options.get(CONF_CHAT_MODEL) or self.default_model
        # Ensure configured_model is a valid string
        if not isinstance(configured_model, str) or not configured_model.strip():
            configured_model = self.default_model

        # Check if we need to switch to vision model
        final_model = configured_model
        if chat_log and chat_log_has_media_attachments(chat_log):
            vision_models = [RECOMMENDED_IMAGE_ANALYSIS_MODEL]
            final_model = select_media_model(
                configured_model,
                vision_models,
                RECOMMENDED_IMAGE_ANALYSIS_MODEL,
            )
            if final_model != configured_model:
                _LOGGER.debug(
                    "Auto-switching to vision model %s for media attachments (original: %s)",
                    final_model,
                    configured_model,
                )

        # Only use parameters that the working service uses (top_p causes API error!)
        # Ensure model is always a valid string
        model_value = final_model or self.default_model
        if not isinstance(model_value, str) or not model_value.strip():
            model_value = self.default_model

        return {
            "model": model_value,
            "temperature": options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
            "enable_thinking": bool(
                options.get(CONF_ENABLE_THINKING, RECOMMENDED_ENABLE_THINKING)
            ),
            "max_tokens": options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
            "debug_log": bool(options.get(CONF_DEBUG_LOG, RECOMMENDED_DEBUG_LOG)),
        }

    async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure: dict[str, Any] | None = None,
    ) -> None:
        """Generate an answer for the chat log."""
        options = self.subentry.data
        model_config = self._get_model_config(chat_log)

        # Build messages from chat log (attachment processing will be done during conversion)
        messages = await self._async_convert_chat_log_to_messages(chat_log)

        # Add JSON format instruction to system message if structure is requested
        if structure and messages:
            for i, message in enumerate(messages):
                if message.get("role") == "system":
                    # Add JSON format requirement to system message
                    original_content = message.get("content", "")
                    if "JSON" not in original_content:
                        message["content"] = (
                            original_content +
                            "\n\nWhen providing structured data like automation names/"
                            "descriptions, respond ONLY with valid JSON. Use the exact "
                            "JSON structure requested in the prompt. Do not include any "
                            "markdown formatting, explanations, or additional text."
                        )
                    break

        # Add tools if available
        tools = []
        if chat_log.llm_api:
            for tool in chat_log.llm_api.tools:
                if isinstance(tool, dict):
                    tools.append(tool)
                else:
                    tools.append(
                        self._format_tool(tool, chat_log.llm_api.custom_serializer)
                    )

        # Build minimal request parameters using only essential parameters
        # Ensure model is a valid non-empty string
        model_name = model_config.get("model", "")
        if not model_name or not isinstance(model_name, str):
            model_name = self.default_model
            _LOGGER.warning("Model name was invalid, using default: %s", model_name)

        # Validate all message contents before sending
        for i, msg in enumerate(messages):
            msg_content = msg.get("content")
            if msg_content is None:
                msg["content"] = ""
                _LOGGER.warning("Message %d had None content, replaced with empty string", i)
            elif isinstance(msg_content, list):
                # Validate each part in content list
                for j, part in enumerate(msg_content):
                    if part.get("type") == "text" and not isinstance(part.get("text"), str):
                        part["text"] = str(part.get("text", ""))
                        _LOGGER.warning("Message %d part %d had non-string text, converted", i, j)

        api_url = model_config.get(CONF_CHAT_URL, options.get(CONF_CHAT_URL))
        if not isinstance(api_url, str) or not api_url.strip():
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="entity_api_url_not_configured",
            )

        provider_name = resolve_provider_name(api_url, options.get(CONF_LLM_PROVIDER))

        try:
            # Validate API key before making request
            if not self._api_key:
                _LOGGER.error("Cannot make API request: API key is empty or not configured")
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="entity_api_key_not_configured",
                )

            # Ensure API key is a string
            if not isinstance(self._api_key, str):
                self._api_key = str(self._api_key)

            _LOGGER.debug(
                "API Request: provider=%s, model=%s, messages_count=%d",
                provider_name,
                model_name,
                len(messages)
            )

            llm_messages = [
                LLMMessage(
                    role=msg["role"],
                    content=msg.get("content", ""),
                    tool_calls=msg.get("tool_calls"),
                    tool_call_id=msg.get("tool_call_id"),
                    tool_name=msg.get("tool_name"),
                    reasoning_content=msg.get("reasoning_content"),
                )
                for msg in messages
            ]

            provider = create_provider(
                provider_name,
                {
                    "api_key": self._api_key,
                    "model": model_name,
                    "base_url": api_url,
                    "temperature": model_config.get("temperature", RECOMMENDED_TEMPERATURE),
                    "max_tokens": model_config.get("max_tokens", RECOMMENDED_MAX_TOKENS),
                    "enable_thinking": model_config.get("enable_thinking", RECOMMENDED_ENABLE_THINKING),
                    "debug_log": model_config.get("debug_log", RECOMMENDED_DEBUG_LOG),
                    "timeout": TIMEOUT_CHAT_API * 2,
                },
            )
            if provider is None:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="entity_unsupported_provider",
                    translation_placeholders=translation_placeholders(provider_name=provider_name),
                )

            if not provider.supports_tools():
                tools = []

            provider_timeout = getattr(getattr(provider, "config", None), "timeout", 60)

            if provider_name in {"openai_compatible", "anthropic_compatible", "ollama_compatible"}:
                await self._async_run_provider_stream(
                    chat_log,
                    provider_name,
                    provider,
                    llm_messages,
                    tools,
                )
            elif tools:
                await self._async_run_provider_completion(
                    chat_log,
                    provider_name,
                    provider,
                    llm_messages,
                    tools,
                )
            else:
                await self._async_run_provider_stream(
                    chat_log,
                    provider_name,
                    provider,
                    llm_messages,
                )

        except Exception as err:
            _LOGGER.error(
                "Error calling LLM provider: %s (%s)",
                err,
                type(err).__name__,
            )
            raise HomeAssistantError(
                _format_request_exception(
                    err,
                    provider_name=provider_name,
                    api_url=api_url,
                    timeout_seconds=provider_timeout if 'provider_timeout' in locals() else 60,
                )
            ) from err

    async def _async_run_provider_stream(
        self,
        chat_log: conversation.ChatLog,
        provider_name: str,
        provider: Any,
        llm_messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        _retry_count: int = 0,
    ) -> None:
        """Run a provider in streaming mode for text-only turns."""
        _LOGGER.debug(
            "Invoking provider=%s stream=%s tools=%d retry=%d",
            provider_name,
            True,
            len(tools or []),
            _retry_count,
        )
        has_output = False
        try:
            async for _ in chat_log.async_add_delta_content_stream(
                self.entity_id,
                self._transform_provider_stream(provider.complete_stream(llm_messages, tools=tools)),
            ):
                has_output = True
        except FirstChunkTimeoutError:
            if _retry_count < 1:
                _LOGGER.warning(
                    "Provider %s first chunk timeout, retrying...",
                    provider_name,
                )
                return await self._async_run_provider_stream(
                    chat_log, provider_name, provider, llm_messages, tools, _retry_count + 1
                )
            raise
        except (
            aiohttp.ServerDisconnectedError,
            aiohttp.ClientPayloadError,
            aiohttp.ClientOSError,
        ) as err:
            if _retry_count < 1:
                import asyncio as _aio
                wait = 3.0
                _LOGGER.warning(
                    "Provider %s stream disconnected (%s), waiting %.1fs before retry...",
                    provider_name, type(err).__name__, wait,
                )
                await _aio.sleep(wait)
                return await self._async_run_provider_stream(
                    chat_log, provider_name, provider, llm_messages, tools, _retry_count + 1
                )
            raise

        if not has_output:
            _LOGGER.warning(
                "Provider %s returned an empty streaming response; appending empty assistant message",
                provider_name,
            )
            async for _ in chat_log.async_add_assistant_content(
                conversation.AssistantContent(
                    agent_id=self.entity_id,
                    content="",
                )
            ):
                pass

    async def _async_run_provider_completion(
        self,
        chat_log: conversation.ChatLog,
        provider_name: str,
        provider: Any,
        llm_messages: list[LLMMessage],
        tools: list[dict[str, Any]],
    ) -> None:
        """Run a provider completion and append assistant content/tool calls."""
        _LOGGER.debug(
            "Invoking provider=%s stream=%s tools=%d",
            provider_name,
            False,
            len(tools),
        )
        response = await provider.complete(llm_messages, tools=tools)
        tool_calls = self._convert_provider_tool_calls(response.tool_calls)
        content_text = response.content or ""
        if "<think>" in content_text:
            content_text = re.sub(r"<think>.*?</think>", "", content_text, flags=re.DOTALL).strip()
        assistant_content = conversation.AssistantContent(
            agent_id=self.entity_id,
            content=content_text or None,
            tool_calls=tool_calls or None,
            thinking_content=response.reasoning_content or None,
            native=response.raw_response,
        )
        async for _ in chat_log.async_add_assistant_content(assistant_content):
            pass

    async def _transform_provider_stream(
        self,
        stream: AsyncGenerator[Any, None],
    ) -> AsyncGenerator[conversation.AssistantContentDeltaDict, None]:
        """Convert provider chunks into Home Assistant streaming deltas."""
        has_started = False
        in_think_tag = False
        text_buffer = ""
        async for chunk in stream:
            if not chunk:
                continue
            if isinstance(chunk, dict):
                if "thinking_content" in chunk:
                    if not has_started:
                        yield {"role": "assistant"}
                        has_started = True
                    yield {"thinking_content": chunk["thinking_content"]}
                    continue
                if "role" not in chunk and not has_started:
                    yield {"role": "assistant"}
                    has_started = True
                elif chunk.get("role") == "assistant":
                    has_started = True
                if "tool_calls" in chunk:
                    raw = chunk["tool_calls"]
                    if raw and isinstance(raw[0], llm.ToolInput):
                        yield {"tool_calls": raw}
                    else:
                        converted = self._convert_provider_tool_calls(raw)
                        if converted:
                            yield {"tool_calls": converted}
                else:
                    yield chunk
                continue
            if not has_started:
                yield {"role": "assistant"}
                has_started = True

            text_buffer += chunk
            while text_buffer:
                if in_think_tag:
                    end_pos = text_buffer.find("</think>")
                    if end_pos == -1:
                        text_buffer = ""
                        break
                    text_buffer = text_buffer[end_pos + len("</think>"):]
                    in_think_tag = False
                else:
                    start_pos = text_buffer.find("<think>")
                    if start_pos == -1:
                        if text_buffer:
                            yield {"content": text_buffer}
                        text_buffer = ""
                        break
                    before = text_buffer[:start_pos]
                    if before:
                        yield {"content": before}
                    text_buffer = text_buffer[start_pos + len("<think>"):]
                    in_think_tag = True

        if text_buffer and not in_think_tag:
            yield {"content": text_buffer}

    def _convert_provider_tool_calls(
        self,
        tool_calls: list[dict[str, Any]] | None,
    ) -> list[llm.ToolInput]:
        """Convert provider tool calls to Home Assistant ToolInput objects."""
        if not tool_calls:
            return []

        converted: list[llm.ToolInput] = []
        for tool_call in tool_calls:
            try:
                function_data = tool_call.get("function", {})
                arguments = function_data.get("arguments", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments) if arguments else {}
                if not isinstance(arguments, dict):
                    arguments = {"value": arguments}

                tool_id = tool_call.get("id") or ulid.ulid_now()
                converted.append(
                    llm.ToolInput(
                        id=tool_id,
                        tool_name=function_data.get("name", "tool"),
                        tool_args=arguments,
                    )
                )
            except Exception as err:
                _LOGGER.warning("Failed to convert provider tool call: %s", err)

        return converted

    async def _async_convert_chat_log_to_messages(
        self, chat_log: conversation.ChatLog
    ) -> list[dict[str, Any]]:
        """Convert chat log to AI Hub message format."""
        attachment_processor = AttachmentProcessor(self.hass, self.entity_id)
        builder = ChatMessageBuilder(
            attachment_processor,
            self.subentry.data.get(CONF_MAX_HISTORY_MESSAGES, RECOMMENDED_MAX_HISTORY_MESSAGES),
            tool_message_converter=self._convert_tool_message,
        )
        return await builder.async_convert_chat_log_to_messages(chat_log)

    def _convert_tool_message(
        self, content: conversation.Content
    ) -> list[dict[str, Any]]:
        """Convert tool result to AI Hub format.

        Returns a list: normally one ``role: tool`` message; when the tool result
        carries an ``image_base64`` field, the base64 is stripped from the tool
        content and a follow-up ``role: user`` multimodal message is appended so
        the vision model can actually see the image.
        """
        # Ensure tool_call_id is always a valid string
        # API requires a non-empty tool_call_id
        tool_call_id = content.tool_call_id
        if not tool_call_id or not isinstance(tool_call_id, str) or not tool_call_id.strip():
            # Generate a valid ID if missing - this maintains API compatibility
            tool_call_id = ulid.ulid_now()
            _LOGGER.debug("Generated tool_call_id for tool result: %s", tool_call_id)

        tool_result = content.tool_result
        image_b64: str | None = None
        image_mime = "image/jpeg"
        tool_name = ""

        # Strip image_base64 from the tool payload so we don't ship the raw
        # base64 twice (once as text, once as image_url).
        if isinstance(tool_result, dict) and isinstance(
            tool_result.get("image_base64"), str
        ):
            sanitized = {k: v for k, v in tool_result.items() if k != "image_base64"}
            image_b64 = tool_result["image_base64"]
            image_mime = str(sanitized.get("content_type") or "image/jpeg")
            tool_name = str(sanitized.get("camera_entity") or sanitized.get("tool") or "")
            sanitized["image_base64"] = (
                f"<image attached as image_url follow-up, {len(image_b64)} base64 chars>"
            )
            tool_result_payload: Any = sanitized
        else:
            tool_result_payload = tool_result

        tool_message: dict[str, Any] = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "tool_name": content.tool_name,
            "content": (
                json.dumps(tool_result_payload, ensure_ascii=False, default=str)
                if tool_result_payload is not None
                else "{}"
            ),
        }

        if not image_b64:
            return [tool_message]

        follow_up: dict[str, Any] = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"Image from tool result ({tool_name}). "
                        "Analyze this picture and continue the task."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                },
            ],
        }
        return [tool_message, follow_up]

    def _format_tool(
        self, tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
    ) -> dict[str, Any]:
        """Format tool for AI Hub API."""
        return ChatMessageBuilder.format_tool(tool, custom_serializer)

    def _convert_schema(
        self, schema: dict[str, Any], custom_serializer: Callable[[Any], Any] | None
    ) -> dict[str, Any]:
        """Convert schema to AI Hub format."""
        return ChatMessageBuilder.convert_schema(schema, custom_serializer)


class AIHubEntityBase(Entity, _AIHubEntityMixin):
    """Base entity for AI Hub integration.

    This class is used by TTS and STT entities which don't need the full
    LLM functionality but require the same initialization logic.
    """

    def __init__(
        self,
        entry: config_entry_flow.ConfigEntry,
        subentry: config_entry_flow.ConfigSubentry,
        default_model: str,
        *,
        warn_on_missing_api_key: bool = True,
    ) -> None:
        """Initialize the entity."""
        # Use mixin initialization
        self._initialize_aihub_entity(
            entry,
            subentry,
            default_model,
            warn_on_missing_api_key=warn_on_missing_api_key,
        )
        # Create device info using mixin method
        self._attr_device_info = self._create_device_info(DOMAIN)
