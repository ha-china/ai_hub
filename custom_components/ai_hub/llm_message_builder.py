"""Message conversion helpers for AI Hub LLM entities."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components import conversation
from homeassistant.helpers import llm
from homeassistant.util import ulid

try:
    from probatio import to_openapi
except ImportError:  # Home Assistant < 2026.9 bundles voluptuous_openapi instead
    from voluptuous_openapi import convert as to_openapi  # type: ignore[assignment]

from .llm_attachment_processor import AttachmentProcessor
from .utils.serialization import ensure_string

_LOGGER = logging.getLogger(__name__)


class ChatMessageBuilder:
    """Convert Home Assistant chat logs into provider messages."""

    def __init__(
        self,
        attachment_processor: AttachmentProcessor,
        max_history: int,
        tool_message_converter: Callable[[conversation.Content], list[dict[str, Any]]] | None = None,
    ) -> None:
        self._attachment_processor = attachment_processor
        self._max_history = max_history
        self._tool_message_converter = tool_message_converter or self._convert_tool_message_list

    async def async_convert_chat_log_to_messages(self, chat_log: conversation.ChatLog) -> list[dict[str, Any]]:
        """Convert chat log to AI Hub message format."""
        messages: list[dict[str, Any]] = []
        if not chat_log.content:
            return messages

        last_content = chat_log.content[-1]

        tool_call_id_map: dict[str, str] = {}
        last_tool_call_ids: list[str] = []

        for content in chat_log.content:
            if content.role == "system":
                messages.append({"role": "system", "content": ensure_string(content.content)})

        history_content = chat_log.content[1:-1] if len(chat_log.content) > 1 else []
        history_messages: list[dict[str, Any]] = []
        for content in history_content:
            if content.role == "user":
                history_messages.append(await self._convert_user_message(content))
            elif content.role == "assistant":
                msg, generated_ids = self._convert_assistant_message_with_id_tracking(content, tool_call_id_map)
                history_messages.append(msg)
                last_tool_call_ids = generated_ids
            elif content.role == "tool_result":
                history_messages.extend(
                    self._convert_tool_message_with_id_matching(content, tool_call_id_map, last_tool_call_ids)
                )

        if self._max_history > 0:
            user_message_count = sum(1 for msg in history_messages if msg.get("role") == "user")
            if user_message_count > self._max_history:
                user_count = 0
                start_index = len(history_messages)
                for i in range(len(history_messages) - 1, -1, -1):
                    if history_messages[i].get("role") == "user":
                        user_count += 1
                        if user_count > self._max_history:
                            start_index = i
                            break
                history_messages = history_messages[start_index:]

        messages.extend(history_messages)

        if last_content.role == "user":
            messages.append(await self._convert_user_message(last_content))
        elif last_content.role == "assistant":
            msg, _ = self._convert_assistant_message_with_id_tracking(last_content, tool_call_id_map)
            messages.append(msg)
        elif last_content.role == "tool_result":
            messages.extend(
                self._convert_tool_message_with_id_matching(
                    last_content,
                    tool_call_id_map,
                    last_tool_call_ids,
                )
            )

        return messages

    async def _convert_user_message(self, content: conversation.Content) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "user"}
        if not content.attachments:
            message["content"] = ensure_string(content.content)
            return message

        successful_images = await self._attachment_processor.process_attachments(content.attachments)
        if successful_images:
            message["content"] = successful_images + [{"type": "text", "text": ensure_string(content.content)}]
        else:
            message["content"] = ensure_string(content.content)
        return message

    def _convert_assistant_message_with_id_tracking(
        self,
        content: conversation.Content,
        id_map: dict[str, str],
    ) -> tuple[dict[str, Any], list[str]]:
        generated_ids: list[str] = []
        message = self._convert_assistant_message(content)
        if content.tool_calls and "tool_calls" in message:
            for i, tool_call in enumerate(message["tool_calls"]):
                tool_id = tool_call["id"]
                generated_ids.append(tool_id)
                original_id = content.tool_calls[i].id if content.tool_calls[i].id else None
                if original_id:
                    id_map[original_id] = tool_id
                else:
                    id_map[f"_index_{i}"] = tool_id
        return message, generated_ids

    def _convert_tool_message_with_id_matching(
        self,
        content: conversation.Content,
        id_map: dict[str, str],
        last_tool_call_ids: list[str],
    ) -> list[dict[str, Any]]:
        original_id = content.tool_call_id
        messages = self._tool_message_converter(content)
        if not messages:
            return messages

        tool_message = messages[0]
        if original_id and isinstance(original_id, str) and original_id.strip():
            if original_id in id_map:
                tool_message["tool_call_id"] = id_map[original_id]
        elif last_tool_call_ids:
            tool_message["tool_call_id"] = last_tool_call_ids[0]
            if len(last_tool_call_ids) > 1:
                last_tool_call_ids.pop(0)
        return messages

    @staticmethod
    def _convert_assistant_message(content: conversation.Content) -> dict[str, Any]:
        message: dict[str, Any] = {"role": "assistant"}
        if content.tool_calls:
            tool_calls_list = []
            for tool_call in content.tool_calls:
                tool_id = tool_call.id if tool_call.id else None
                if not tool_id or not isinstance(tool_id, str) or not tool_id.strip():
                    tool_id = ulid.ulid_now()
                tool_calls_list.append(
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": str(tool_call.tool_name) if tool_call.tool_name else "",
                            "arguments": (
                                json.dumps(tool_call.tool_args, ensure_ascii=False)
                                if tool_call.tool_args
                                else "{}"
                            ),
                        },
                    }
                )
            message["tool_calls"] = tool_calls_list
        message["content"] = ensure_string(content.content)
        # DeepSeek thinking mode requires reasoning_content to be passed back
        thinking = getattr(content, "thinking_content", None)
        if thinking:
            message["reasoning_content"] = thinking
        return message

    @staticmethod
    def _convert_tool_message(content: conversation.Content) -> dict[str, Any]:
        tool_call_id = content.tool_call_id
        if not tool_call_id or not isinstance(tool_call_id, str) or not tool_call_id.strip():
            tool_call_id = ulid.ulid_now()
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "tool_name": content.tool_name,
            "content": (
                json.dumps(content.tool_result, ensure_ascii=False, default=str)
                if content.tool_result is not None
                else "{}"
            ),
        }

    @staticmethod
    def _convert_tool_message_list(content: conversation.Content) -> list[dict[str, Any]]:
        return [ChatMessageBuilder._convert_tool_message(content)]

    @staticmethod
    def format_tool(tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": str(tool.name) if tool.name else "",
                "description": str(tool.description) if tool.description else "",
                "parameters": ChatMessageBuilder.convert_schema(tool.parameters, custom_serializer),
            },
        }

    @staticmethod
    def convert_schema(schema: dict[str, Any], custom_serializer: Callable[[Any], Any] | None) -> dict[str, Any]:
        try:
            return to_openapi(
                schema,
                custom_serializer=custom_serializer if custom_serializer else llm.selector_serializer,
            )
        except Exception as err:
            _LOGGER.warning("Failed to convert schema with custom_serializer: %s", err)
            try:
                return to_openapi(schema, custom_serializer=llm.selector_serializer)
            except Exception:
                return schema
