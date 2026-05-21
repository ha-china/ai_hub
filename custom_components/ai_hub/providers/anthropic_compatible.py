"""Anthropic-compatible LLM provider for AI Hub integration."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from homeassistant.util import ulid

from ..http import (
    async_post_json,
    async_stream_response_text,
    build_json_headers,
    resolve_ssl_setting,
)
from .common_compatible import check_provider_health, finalize_buffered_tool_calls
from . import LLMMessage, LLMProvider, LLMResponse

_LOGGER = logging.getLogger(__name__)

_DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicCompatibleProvider(LLMProvider):
    """Anthropic Messages API provider."""

    _name = "anthropic_compatible"

    @property
    def name(self) -> str:
        return "anthropic_compatible"

    @property
    def supported_models(self) -> list[str]:
        return []

    def supports_vision(self) -> bool:
        return False

    def supports_tools(self) -> bool:
        return True

    def _get_headers(self) -> dict[str, str]:
        headers = build_json_headers(self.config.api_key)
        headers["anthropic-version"] = _ANTHROPIC_VERSION
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _get_api_url(self) -> str:
        url = self.config.base_url or _DEFAULT_API_URL
        if not url:
            return _DEFAULT_API_URL

        normalized = url.rstrip("/")
        if normalized.endswith("/v1/messages"):
            return normalized
        if normalized.endswith("/messages"):
            return normalized
        if normalized.endswith("/v1"):
            return f"{normalized}/messages"
        return f"{normalized}/v1/messages"

    def _convert_content_blocks_for_assistant(self, content: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert content blocks for assistant messages, preserving thinking with signature."""
        # Handle JSON-encoded content blocks (from ensure_string serialization)
        if isinstance(content, str):
            if content.startswith("[") and content.endswith("]"):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        content = parsed
                except json.JSONDecodeError:
                    pass
            if isinstance(content, str):
                return [{"type": "text", "text": content}] if content else []

        blocks: list[dict[str, Any]] = []
        for part in content:
            block_type = part.get("type")
            if block_type == "text":
                text = str(part.get("text", ""))
                if text:
                    blocks.append({"type": "text", "text": text})
            elif block_type == "thinking":
                # Anthropic requires signature for thinking blocks in input
                thinking = str(part.get("thinking", ""))
                signature = part.get("signature")
                if thinking and signature:
                    blocks.append({"type": "thinking", "thinking": thinking, "signature": signature})
                # Skip thinking without signature (can't be sent back)
            # tool_use handled separately via tool_calls attribute
        return blocks

    def _extract_text_content(self, content: str | list[dict[str, Any]]) -> str:
        """Extract text content only for user messages."""
        # Handle JSON-encoded content blocks
        if isinstance(content, str):
            if content.startswith("[") and content.endswith("]"):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        content = parsed
                except json.JSONDecodeError:
                    pass
            if isinstance(content, str):
                return content

        text_parts: list[str] = []
        for part in content:
            if part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "".join(text_parts)

    def _convert_messages(self, messages: list[LLMMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        system_parts: list[str] = []
        converted: list[dict[str, Any]] = []

        for message in messages:
            if message.role == "system":
                if isinstance(message.content, str) and message.content.strip():
                    system_parts.append(message.content)
                continue

            if message.role in {"user", "assistant"}:
                if message.role == "assistant":
                    content_blocks = self._convert_content_blocks_for_assistant(message.content)

                    # Add reasoning_content as thinking block for compatible APIs (e.g., Xiaomi)
                    # Note: Some APIs require signature, some don't. We add a placeholder.
                    reasoning = getattr(message, "reasoning_content", None)
                    if reasoning and not any(b.get("type") == "thinking" for b in content_blocks):
                        content_blocks.insert(0, {
                            "type": "thinking",
                            "thinking": reasoning,
                            "signature": "placeholder_sig"  # Required by some Anthropic-compatible APIs
                        })

                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            function_data = tool_call.get("function", {})
                            arguments = function_data.get("arguments", {})
                            if isinstance(arguments, str):
                                try:
                                    arguments = json.loads(arguments)
                                except json.JSONDecodeError:
                                    arguments = {"raw_arguments": arguments}
                            content_blocks.append(
                                {
                                    "type": "tool_use",
                                    "id": tool_call.get("id") or function_data.get("name", "tool_call"),
                                    "name": function_data.get("name", "tool"),
                                    "input": arguments if isinstance(arguments, dict) else {"value": arguments},
                                }
                            )

                    anthropic_message: dict[str, Any] = {
                        "role": message.role,
                        "content": content_blocks if content_blocks else "",
                    }
                else:
                    content = self._extract_text_content(message.content)
                    anthropic_message = {
                        "role": message.role,
                        "content": content,
                    }
                converted.append(anthropic_message)
                continue

            if message.role == "tool":
                tool_result_content = message.content
                if isinstance(tool_result_content, (dict, list)):
                    tool_result_content = json.dumps(tool_result_content, ensure_ascii=False, default=str)
                elif not isinstance(tool_result_content, str):
                    tool_result_content = str(tool_result_content) if tool_result_content is not None else "{}"
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": message.tool_call_id or "tool_call",
                    "content": tool_result_content,
                }
                if converted and converted[-1]["role"] == "user":
                    if isinstance(converted[-1]["content"], list):
                        converted[-1]["content"].append(tool_result_block)
                    else:
                        converted[-1]["content"] = [
                            {"type": "text", "text": converted[-1]["content"]} if converted[-1]["content"] else tool_result_block,
                            tool_result_block,
                        ]
                else:
                    converted.append(
                        {
                            "role": "user",
                            "content": [tool_result_block],
                        }
                    )

        system = "\n\n".join(part for part in system_parts if part) or None
        return system, converted

    def _convert_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None

        converted = []
        for tool in tools:
            function = tool.get("function", {})
            schema = function.get("parameters", {"type": "object", "properties": {}})
            if not isinstance(schema, dict) or "type" not in schema:
                schema = {"type": "object", "properties": {}}
            converted.append(
                {
                    "name": function.get("name", "tool"),
                    "description": function.get("description", ""),
                    "input_schema": schema,
                }
            )
        return converted

    def _extract_text(self, content_blocks: list[dict[str, Any]]) -> str:
        return "".join(block.get("text", "") for block in content_blocks if block.get("type") == "text")

    def _extract_response_text(self, data: dict[str, Any]) -> str:
        """Extract text from Anthropic-compatible responses.

        Some third-party compatible endpoints do not return the exact official
        Anthropic payload shape, so we accept a few common variants.
        """
        content = data.get("content", [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text = self._extract_text(content)
            if text:
                return text

        if isinstance(data.get("output_text"), str):
            return data["output_text"]
        if isinstance(data.get("text"), str):
            return data["text"]

        message = data.get("message")
        if isinstance(message, dict):
            if isinstance(message.get("content"), str):
                return message["content"]
            if isinstance(message.get("content"), list):
                text = self._extract_text(message["content"])
                if text:
                    return text

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                if isinstance(first.get("text"), str):
                    return first["text"]
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"]

        return ""

    def _extract_reasoning_content(self, data: dict[str, Any]) -> str | None:
        """Extract reasoning/thinking content from an Anthropic-compatible response."""
        content = data.get("content", [])
        if isinstance(content, list):
            thinking_parts = [
                block.get("thinking", "")
                for block in content
                if block.get("type") == "thinking"
            ]
            if thinking_parts:
                return "\n".join(thinking_parts)

        message = data.get("message")
        if isinstance(message, dict):
            msg_content = message.get("content")
            if isinstance(msg_content, list):
                thinking_parts = [
                    block.get("thinking", "")
                    for block in msg_content
                    if block.get("type") == "thinking"
                ]
                if thinking_parts:
                    return "\n".join(thinking_parts)

        return None


    def _extract_response_tool_calls(self, data: dict[str, Any]) -> list[dict[str, Any]] | None:
        """Extract tool calls from Anthropic-compatible responses."""
        content = data.get("content", [])
        if isinstance(content, list):
            tool_calls = self._extract_tool_calls(content)
            if tool_calls:
                return tool_calls

        message = data.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                tool_calls = self._extract_tool_calls(content)
                if tool_calls:
                    return tool_calls

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    tool_calls = message.get("tool_calls")
                    if isinstance(tool_calls, list):
                        return tool_calls

        return None

    def _extract_tool_calls(self, content_blocks: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        tool_calls = []
        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue
            tool_calls.append(
                {
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name", "tool"),
                        "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                    },
                }
            )
        return tool_calls or None

    def _apply_cache_control(
        self,
        system: str | None,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> tuple[Any, list[dict[str, Any]], list[dict[str, Any]] | None]:
        """Apply cache_control to maximize prompt caching.
        
        Anthropic prompt caching strategy:
        1. Cache system prompt (if >= 1024 tokens, ~4KB text)
        2. Cache tools definition
        3. Cache last 2 user messages (conversation context)
        
        This can reduce costs by up to 90% for repeated conversations.
        """
        CACHE_CONTROL = {"type": "ephemeral"}
        MIN_CACHE_CHARS = 4000  # ~1024 tokens
        
        # 1. Cache system prompt if large enough
        cached_system = system
        if system and len(system) >= MIN_CACHE_CHARS:
            cached_system = [
                {"type": "text", "text": system, "cache_control": CACHE_CONTROL}
            ]
        
        # 2. Cache tools (they're usually stable across turns)
        cached_tools = tools
        if tools and len(tools) > 0:
            cached_tools = tools.copy()
            cached_tools[-1] = {**cached_tools[-1], "cache_control": CACHE_CONTROL}
        
        # 3. Cache last 2 user messages for conversation context
        cached_messages = messages.copy()
        cache_count = 0
        for i in range(len(cached_messages) - 1, -1, -1):
            if cache_count >= 2:
                break
            msg = cached_messages[i]
            if msg.get("role") != "user":
                continue
            content = msg.get("content")
            if isinstance(content, list) and len(content) > 0:
                # Add cache_control to last content block
                new_content = content.copy()
                last_block = new_content[-1].copy()
                last_block["cache_control"] = CACHE_CONTROL
                new_content[-1] = last_block
                cached_messages[i] = {**msg, "content": new_content}
                cache_count += 1
            elif isinstance(content, str) and len(content) >= MIN_CACHE_CHARS:
                # Convert string to content block with cache_control
                cached_messages[i] = {
                    **msg,
                    "content": [{"type": "text", "text": content, "cache_control": CACHE_CONTROL}]
                }
                cache_count += 1
        
        return cached_system, cached_messages, cached_tools

    def _build_request(
        self,
        messages: list[LLMMessage],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        system, anthropic_messages = self._convert_messages(messages)
        anthropic_tools = self._convert_tools(tools)
        
        # Apply cache control for prompt caching optimization
        cached_system, cached_messages, cached_tools = self._apply_cache_control(
            system, anthropic_messages, anthropic_tools
        )
        
        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": cached_messages,
            "stream": stream,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if cached_system:
            request["system"] = cached_system

        if cached_tools:
            request["tools"] = cached_tools

        if self.config.enable_thinking and "thinking" not in self.config.extra:
            request["thinking"] = {"type": "enabled", "budget_tokens": self.config.max_tokens}

        request.update(self.config.extra)
        request.update(kwargs)
        if self.config.debug_log:
            try:
                msgs = request.get("messages", [])
                tools = request.get("tools", [])
                _LOGGER.debug(
                    "[AI_HUB_DEBUG] anthropic request model=%s stream=%s msg_count=%d tool_count=%d",
                    request.get("model", "?"), request.get("stream", False), len(msgs), len(tools),
                )
                for i, msg in enumerate(msgs):
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    preview = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
                    if len(preview) > 2000:
                        preview = preview[:2000] + f"...[truncated, total {len(preview)}]"
                    _LOGGER.warning("[AI_HUB_DEBUG]   msg[%d] role=%s content=%s", i, role, preview)
            except Exception:
                _LOGGER.warning("[AI_HUB_DEBUG] failed to log anthropic request", exc_info=True)
        return request

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        request = self._build_request(messages, stream=False, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = resolve_ssl_setting(url, _DEFAULT_API_URL)

        try:
            data = await async_post_json(
                url,
                payload=request,
                headers=headers,
                ssl=ssl,
                timeout=self.config.timeout,
                error_label="API error",
            )
        except Exception as err:
            if self.config.debug_log:
                _LOGGER.warning(
                    "[AI_HUB_DEBUG] anthropic API error: %s url=%s model=%s",
                    err, url, request.get("model", "?"),
                )
            raise
        if self.config.debug_log:
            try:
                # Log cache hit info for Anthropic
                raw_usage = data.get("usage", {})
                if isinstance(raw_usage, dict):
                    cache_info = ""
                    cache_read = raw_usage.get("cache_read_input_tokens", 0)
                    cache_write = raw_usage.get("cache_creation_input_tokens", 0)
                    input_tokens = raw_usage.get("input_tokens", 0)
                    if cache_read or cache_write:
                        total = input_tokens + cache_read + cache_write
                        hit_rate = (cache_read / total * 100) if total > 0 else 0
                        cache_info = f" cache_read={cache_read} cache_write={cache_write} hit_rate={hit_rate:.1f}%"
                    _LOGGER.warning(
                        "[AI_HUB_DEBUG] anthropic tokens: in=%s out=%s%s",
                        input_tokens,
                        raw_usage.get("output_tokens", "?"),
                        cache_info,
                    )
                resp_preview = json.dumps(data, ensure_ascii=False, default=str)
                if len(resp_preview) > 3000:
                    resp_preview = resp_preview[:3000] + "...[truncated]"
                _LOGGER.warning("[AI_HUB_DEBUG] anthropic response: %s", resp_preview)
            except Exception:
                _LOGGER.warning("[AI_HUB_DEBUG] anthropic response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))

        usage = data.get("usage")
        if isinstance(usage, dict):
            usage = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
            }

        text_content = self._extract_response_text(data)
        tool_calls = self._extract_response_tool_calls(data)
        if not text_content and not tool_calls:
            _LOGGER.debug("Anthropic-compatible empty response payload: %s", data)

        reasoning_content = self._extract_reasoning_content(data)

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            usage=usage,
            model=data.get("model"),
            finish_reason=data.get("stop_reason"),
            raw_response=data,
            reasoning_content=reasoning_content,
        )

    async def complete_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str | dict[str, Any], None]:
        request = self._build_request(messages, stream=True, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = resolve_ssl_setting(url, _DEFAULT_API_URL)
        if self.config.debug_log:
            _LOGGER.warning("[AI_HUB_DEBUG] anthropic complete_stream url=%s", url)

        buffer = ""
        tool_call_buffer: dict[int, dict[str, Any]] = {}
        async for chunk_text in async_stream_response_text(
            url,
            payload=request,
            headers=headers,
            ssl=ssl,
            timeout=self.config.timeout,
            error_label="API error",
        ):
            buffer += chunk_text

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()

                if not line or line.startswith("event:"):
                    continue
                if not line.startswith("data: "):
                    continue

                data_str = line[6:]

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    _LOGGER.debug("Anthropic SSE parse failed: %s", data_str)
                    continue

                if data.get("type") == "content_block_start":
                    content_block = data.get("content_block", {})
                    if content_block.get("type") == "tool_use":
                        index = int(data.get("index", 0))
                        tool_id = content_block.get("id")
                        if not isinstance(tool_id, str) or not tool_id.strip():
                            tool_id = ulid.ulid_now()
                        tool_call_buffer[index] = {
                            "id": tool_id,
                            "type": "function",
                            "function": {
                                "name": str(content_block.get("name", "tool")),
                                "arguments": "",
                            },
                        }
                    continue

                if data.get("type") == "content_block_delta":
                    index = int(data.get("index", 0))
                    delta = data.get("delta", {})
                    delta_type = delta.get("type")
                    if delta_type == "thinking_delta":
                        thinking = delta.get("thinking", "")
                        if thinking:
                            yield {"thinking_content": thinking}
                        continue
                    if delta_type == "text_delta":
                        text = delta.get("text", "")
                        if text:
                            yield text
                        continue

                    if delta_type == "input_json_delta":
                        partial_json = delta.get("partial_json", "")
                        if not partial_json:
                            continue
                        if index not in tool_call_buffer:
                            tool_call_buffer[index] = {
                                "id": ulid.ulid_now(),
                                "type": "function",
                                "function": {"name": "tool", "arguments": ""},
                            }
                        tool_call_buffer[index]["function"]["arguments"] += partial_json

        if tool_call_buffer:
            tool_calls = finalize_buffered_tool_calls(tool_call_buffer)
            if tool_calls:
                yield {"tool_calls": tool_calls}

    async def health_check(self) -> bool:
        try:
            url = self._get_api_url()
            ssl = resolve_ssl_setting(url, _DEFAULT_API_URL)

            return await check_provider_health(url, ssl=ssl, timeout=10)
        except Exception as err:
            _LOGGER.debug("Anthropic health check failed: %s", err)
            return False
