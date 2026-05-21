"""Ollama-compatible LLM provider for AI Hub integration."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from ..http import async_post_json, async_stream_response_text
from . import LLMMessage, LLMProvider, LLMResponse
from .common_compatible import check_provider_health, finalize_buffered_tool_calls

_LOGGER = logging.getLogger(__name__)


def _parse_arguments_object(arguments: Any) -> Any:
    """Convert OpenAI-style JSON-string arguments into Ollama-native objects."""
    if isinstance(arguments, dict):
        return arguments

    if isinstance(arguments, str):
        stripped = arguments.strip()
        if not stripped:
            return {}
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return {"value": arguments}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    if arguments is None:
        return {}

    return {"value": arguments}


def _convert_content_blocks(content: str | list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    """Keep text content readable while preserving non-text blocks."""
    if isinstance(content, str):
        return content

    blocks: list[dict[str, Any]] = []
    text_parts: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text":
            text_parts.append(str(part.get("text", "")))
            continue
        blocks.append(part)

    if blocks:
        if text_parts:
            blocks.append({"type": "text", "text": "".join(text_parts)})
        return blocks

    return "".join(text_parts)


def _convert_request_tool_calls(tool_calls: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    """Convert shared tool calls into Ollama-native request objects."""
    if not tool_calls:
        return None

    converted: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        function = tool_call.get("function", {})
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if not name:
            continue

        converted_call: dict[str, Any] = {
            "function": {
                "name": str(name),
                "arguments": _parse_arguments_object(function.get("arguments", {})),
            }
        }
        if tool_call.get("id"):
            converted_call["id"] = tool_call["id"]
        converted.append(converted_call)

    return converted or None


def _normalize_ollama_api_url(url: str | None) -> str:
    """Normalize Ollama URLs to the `/api/chat` endpoint."""
    default_url = "http://localhost:11434/api/chat"
    if not url:
        return default_url

    normalized = url.rstrip("/")
    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/")

    if path.endswith("/api/chat"):
        return normalized

    if not path:
        return f"{normalized}/api/chat"

    return f"{normalized}/api/chat"


def _coerce_arguments(arguments: Any) -> str:
    """Normalize tool-call arguments to a JSON string."""
    if isinstance(arguments, str):
        return arguments
    if isinstance(arguments, dict):
        return json.dumps(arguments, ensure_ascii=False)
    return json.dumps({"value": arguments}, ensure_ascii=False)


def _parse_tool_calls(tool_calls: Any) -> list[dict[str, Any]] | None:
    """Convert Ollama tool calls to the shared normalized structure."""
    if not isinstance(tool_calls, list):
        return None

    normalized: list[dict[str, Any]] = []
    for item in tool_calls:
        if not isinstance(item, dict):
            continue
        function = item.get("function", {})
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if not name:
            continue
        normalized.append(
            {
                "id": item.get("id") or f"stream_{uuid4().hex}",
                "type": "function",
                "function": {
                    "name": str(name),
                    "arguments": _coerce_arguments(function.get("arguments", {})),
                },
            }
        )

    return normalized or None


class OllamaCompatibleProvider(LLMProvider):
    """Ollama provider using the native `/api/chat` protocol."""

    _name = "ollama_compatible"

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "ollama_compatible"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return []

    def supports_vision(self) -> bool:
        """Check if vision is supported."""
        model = self.config.model.lower()
        return any(keyword in model for keyword in ("vision", "llava", "moondream"))

    def supports_tools(self) -> bool:
        """Check if tools are supported."""
        return True

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _get_api_url(self) -> str:
        """Get the Ollama chat API URL."""
        return _normalize_ollama_api_url(self.config.base_url)

    def _build_request(
        self,
        messages: list[LLMMessage],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build an Ollama `/api/chat` request."""
        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": self._convert_messages(messages),
            "stream": stream,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        if tools:
            request["tools"] = tools

        if self.config.enable_thinking:
            request["think"] = True

        extra = dict(self.config.extra)
        extra_options = extra.pop("options", None)
        if isinstance(extra_options, dict):
            request["options"].update(extra_options)
        request.update(extra)
        request.update(kwargs)
        if self.config.debug_log:
            try:
                msgs = request.get("messages", [])
                tools_list = request.get("tools", [])
                _LOGGER.debug(
                    "[AI_HUB_DEBUG] ollama request model=%s stream=%s msg_count=%d tool_count=%d",
                    request.get("model", "?"), request.get("stream", False), len(msgs), len(tools_list),
                )
                for i, msg in enumerate(msgs):
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    preview = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
                    if len(preview) > 2000:
                        preview = preview[:2000] + f"...[truncated, total {len(preview)}]"
                    _LOGGER.warning("[AI_HUB_DEBUG]   msg[%d] role=%s content=%s", i, role, preview)
            except Exception:
                _LOGGER.warning("[AI_HUB_DEBUG] failed to log ollama request", exc_info=True)
        return request

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert shared chat history into Ollama-native message payloads."""
        converted: list[dict[str, Any]] = []

        for message in messages:
            if message.role in {"system", "user", "assistant"}:
                ollama_message: dict[str, Any] = {
                    "role": message.role,
                    "content": _convert_content_blocks(message.content),
                }
                converted_tool_calls = _convert_request_tool_calls(message.tool_calls)
                if converted_tool_calls:
                    ollama_message["tool_calls"] = converted_tool_calls
                converted.append(ollama_message)
                continue

            if message.role == "tool":
                tool_result_content = message.content
                if isinstance(tool_result_content, (dict, list)):
                    tool_result_content = json.dumps(tool_result_content, ensure_ascii=False, default=str)
                elif not isinstance(tool_result_content, str):
                    tool_result_content = str(tool_result_content) if tool_result_content is not None else "{}"

                converted.append(
                    {
                        "role": "tool",
                        "content": tool_result_content,
                        "tool_call_id": message.tool_call_id or "tool_call",
                        "name": message.tool_name or "tool",
                    }
                )

        return converted

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a non-streaming Ollama completion."""
        request = self._build_request(messages, stream=False, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = False if url.startswith("http://") else None

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
                    "[AI_HUB_DEBUG] ollama API error: %s url=%s model=%s",
                    err, url, request.get("model", "?"),
                )
            raise
        if self.config.debug_log:
            try:
                resp_preview = json.dumps(data, ensure_ascii=False, default=str)
                if len(resp_preview) > 3000:
                    resp_preview = resp_preview[:3000] + "...[truncated]"
                _LOGGER.warning("[AI_HUB_DEBUG] ollama response: %s", resp_preview)
            except Exception:
                _LOGGER.warning("[AI_HUB_DEBUG] ollama response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))

        message = data.get("message", {})
        if not isinstance(message, dict):
            message = {}

        return LLMResponse(
            content=str(message.get("content", "") or data.get("response", "") or ""),
            tool_calls=_parse_tool_calls(message.get("tool_calls")),
            model=data.get("model"),
            finish_reason=data.get("done_reason"),
            raw_response=data,
        )

    async def complete_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str | dict[str, Any], None]:
        """Generate a streaming completion from Ollama's `/api/chat` endpoint."""
        request = self._build_request(messages, stream=True, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = False if url.startswith("http://") else None
        if self.config.debug_log:
            _LOGGER.warning("[AI_HUB_DEBUG] ollama complete_stream url=%s", url)

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
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                message = data.get("message")
                if not isinstance(message, dict):
                    response_text = data.get("response")
                    if isinstance(response_text, str) and response_text:
                        yield response_text
                    continue

                content = message.get("content")
                if isinstance(content, str) and content:
                    yield content

                parsed_tool_calls = _parse_tool_calls(message.get("tool_calls"))
                if parsed_tool_calls:
                    for index, tool_call in enumerate(parsed_tool_calls):
                        tool_call_buffer[index] = tool_call

        if tool_call_buffer:
            tool_calls = finalize_buffered_tool_calls(tool_call_buffer)
            if tool_calls:
                yield {"tool_calls": tool_calls}

    async def health_check(self) -> bool:
        """Check if the Ollama API is reachable."""
        try:
            url = self._get_api_url()
            ssl = False if url.startswith("http://") else None
            return await check_provider_health(url, ssl=ssl, timeout=10)
        except Exception as err:
            _LOGGER.debug("Ollama health check failed: %s", err)
            return False
