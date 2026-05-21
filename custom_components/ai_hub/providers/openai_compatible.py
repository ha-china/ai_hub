"""OpenAI-compatible LLM provider for AI Hub integration.

This module provides an OpenAI-compatible implementation of the LLM provider
interface, which can be used with any OpenAI-compatible API endpoint.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import asyncio
import aiohttp

from ..http import async_post_json, async_stream_response_text
from .common_compatible import check_provider_health, finalize_buffered_tool_calls
from . import LLMMessage, LLMProvider, LLMResponse

_LOGGER = logging.getLogger(__name__)
_NATIVE_TOOL_SUPPORT_BY_URL: dict[str, bool] = {}
_EMULATED_SYSTEM_LIMIT = 6000
_EMULATED_TOOL_CATALOG_LIMIT = 4000
_EMULATED_TRANSCRIPT_LIMIT = 10000
_EMULATED_ITEM_LIMIT = 1500
_DISCONNECT_RETRY_MAX = 2
_DISCONNECT_RETRY_BACKOFF_SECONDS = 1.5


_RETRYABLE_DISCONNECT_ERRORS = (
    aiohttp.ServerDisconnectedError,
    aiohttp.ClientPayloadError,
    aiohttp.ClientOSError,
)


def _get_ssl_setting(url: str) -> bool:
    """Allow custom HTTP and self-signed HTTPS endpoints."""
    parsed = urlparse(url)
    return parsed.scheme != "http" and parsed.netloc == "api.openai.com"


def _normalize_openai_api_url(url: str | None) -> str:
    """Normalize OpenAI-compatible URLs to a request endpoint.

    Users often paste either:
    - a full chat-completions URL
    - a provider base URL ending in `/v1`
    - a plain host URL

    Accept all of them and normalize to a default endpoint this provider expects.
    """
    default_url = "https://api.openai.com/v1/chat/completions"
    if not url:
        return default_url

    normalized = url.rstrip("/")
    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/")

    if path.endswith("/responses"):
        return normalized

    if path.endswith("/chat/completions") or path.endswith("/completions"):
        return normalized

    if path.endswith("/v1"):
        return f"{normalized}/chat/completions"

    if not path:
        return f"{normalized}/v1/chat/completions"

    return f"{normalized}/chat/completions"


def _is_responses_api_url(url: str) -> bool:
    """Return whether the URL targets the Responses API."""
    return urlparse(url).path.rstrip("/").endswith("/responses")


async def _decode_json_response(response: aiohttp.ClientResponse) -> dict[str, Any]:
    """Decode JSON even when the upstream proxy uses the wrong content type."""
    response_text = await response.text()
    if not response_text.strip():
        raise ValueError("Empty response body")

    try:
        return json.loads(response_text)
    except json.JSONDecodeError as err:
        content_type = response.headers.get("Content-Type", "unknown")
        snippet = response_text[:200].replace("\n", " ").strip()
        raise ValueError(
            "Expected JSON response from OpenAI-compatible endpoint "
            f"(content-type={content_type}, body={snippet!r})"
        ) from err


def _strip_image_blocks(content: Any) -> Any:
    """Replace image_url content blocks with a short placeholder.

    Emulated tool mode and plain-chat fallbacks are text-only; shipping raw
    base64 data URLs would bloat the transcript and regularly causes upstream
    proxies to drop the connection.
    """
    if not isinstance(content, list):
        return content
    out: list[dict[str, Any]] = []
    image_count = 0
    for part in content:
        if not isinstance(part, dict):
            out.append(part)
            continue
        if part.get("type") == "image_url":
            image_count += 1
            continue
        out.append(part)
    if image_count and not out:
        return f"[omitted {image_count} image(s) - text-only mode]"
    if image_count:
        out.append({"type": "text", "text": f"[omitted {image_count} image(s) - text-only mode]"})
    return out


def _sanitize_messages_for_plain_chat(messages: list[LLMMessage]) -> list[LLMMessage]:
    """Drop tool-specific fields for compatibility fallbacks.

    Some OpenAI-compatible proxies disconnect when `tools` are present at all.
    When retrying without tools, we also need to remove tool-use/tool-result
    message shapes from history so the payload becomes plain chat-completions.
    Image content blocks are also stripped because plain chat mode is text only.
    """
    sanitized: list[LLMMessage] = []
    for message in messages:
        if message.role == "tool":
            sanitized.append(
                LLMMessage(
                    role="user",
                    content=(
                        f"[Tool result from {message.tool_name}]\n{message.content}"
                        if message.tool_name
                        else f"[Tool result]\n{message.content}"
                    ),
                )
            )
            continue

        sanitized.append(
            LLMMessage(
                role=message.role,
                content=_strip_image_blocks(message.content),
            )
        )
    return sanitized


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    """Extract a JSON object from model output."""
    stripped = text.strip()
    candidates = [stripped]

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start:end + 1])

    for candidate in candidates:
        if not candidate:
            continue
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    return None


def _coerce_tool_call_arguments(arguments: Any) -> str:
    """Normalize tool-call arguments to a JSON string."""
    if isinstance(arguments, str):
        return arguments
    if isinstance(arguments, dict):
        return json.dumps(arguments, ensure_ascii=False)
    return json.dumps({"value": arguments}, ensure_ascii=False)


def _convert_content_blocks(content: str | list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    """Normalize message content while keeping multimodal blocks intact."""
    if isinstance(content, str):
        return content

    normalized: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "text":
            normalized.append({"type": "text", "text": str(part.get("text", ""))})
            continue
        normalized.append(part)
    return normalized or ""


def _convert_request_tool_calls(tool_calls: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    """Normalize outgoing OpenAI-compatible tool calls."""
    if not tool_calls:
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
                    "arguments": _coerce_tool_call_arguments(function.get("arguments", {})),
                },
            }
        )

    return normalized or None


def _extract_openai_message(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract message payload from OpenAI-compatible JSON."""
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return {}, {}
    choice = choices[0] if isinstance(choices[0], dict) else {}
    message = choice.get("message", {})
    return choice, message if isinstance(message, dict) else {}


def _extract_response_payload(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract a normalized response payload from common compatible formats."""
    if isinstance(data.get("choices"), list):
        return _extract_openai_message(data)
    if isinstance(data.get("output"), list) or isinstance(data.get("output_text"), str):
        message: dict[str, Any] = {
            "content": _extract_responses_text(data),
        }
        tool_calls = _extract_responses_tool_calls(data)
        if tool_calls:
            message["tool_calls"] = tool_calls
        reasoning = _extract_responses_reasoning(data)
        if reasoning:
            message["reasoning_content"] = reasoning
        return {}, message
    return {}, {}


def _extract_response_content(message: dict[str, Any], data: dict[str, Any]) -> str:
    """Extract assistant text from normalized message/data payloads."""
    content = message.get("content")
    if isinstance(content, str):
        return content

    return ""


def _extract_response_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Extract tool calls from normalized message payloads."""
    tool_calls = message.get("tool_calls")
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
                    "arguments": _coerce_tool_call_arguments(function.get("arguments", {})),
                },
            }
        )

    return normalized or None


def _extract_responses_text(data: dict[str, Any]) -> str:
    """Extract assistant text from Responses API payloads."""
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    texts: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") in {"output_text", "text"} and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return "".join(texts)


def _extract_responses_reasoning(data: dict[str, Any]) -> str | None:
    """Extract reasoning text from Responses API payloads when present."""
    reasoning_parts: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        if item.get("type") == "reasoning":
            summary = item.get("summary")
            if isinstance(summary, list):
                for part in summary:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        reasoning_parts.append(part["text"])
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") in {"reasoning", "reasoning_text"} and isinstance(part.get("text"), str):
                reasoning_parts.append(part["text"])
    return "\n".join(part for part in reasoning_parts if part) or None


def _extract_responses_tool_calls(data: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Extract tool calls from Responses API payloads."""
    normalized: list[dict[str, Any]] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        if item.get("type") != "function_call":
            continue
        name = item.get("name")
        if not name:
            continue
        normalized.append(
            {
                "id": item.get("call_id") or item.get("id") or f"stream_{uuid4().hex}",
                "type": "function",
                "function": {
                    "name": str(name),
                    "arguments": _coerce_tool_call_arguments(item.get("arguments", {})),
                },
            }
        )
    return normalized or None


def _stringify_message_content(content: str | list[dict[str, Any]]) -> str:
    """Convert a message payload to readable text for emulated tool mode."""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def _convert_content_blocks_for_responses(
    content: str | list[dict[str, Any]],
) -> str | list[dict[str, Any]]:
    """Convert multimodal content to the common Responses API shape."""
    if isinstance(content, str):
        return content

    normalized: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type == "text":
            normalized.append({"type": "input_text", "text": str(part.get("text", ""))})
            continue
        if part_type == "image_url":
            image_url = part.get("image_url")
            if isinstance(image_url, dict):
                image_url = image_url.get("url")
            if image_url:
                normalized.append({"type": "input_image", "image_url": str(image_url)})
            continue
        normalized.append(part)
    return normalized or ""


def _extract_responses_stream_delta(data: dict[str, Any]) -> dict[str, Any]:
    """Extract content/reasoning/tool-calls from a Responses API stream event."""
    event_type = data.get("type")
    if not isinstance(event_type, str):
        return {"content": "", "reasoning": "", "tool_calls": []}

    if event_type in {"response.output_text.delta", "response.output_text"}:
        delta = data.get("delta") or data.get("text") or ""
        return {"content": delta if isinstance(delta, str) else "", "reasoning": "", "tool_calls": []}

    if event_type in {"response.reasoning.delta", "response.reasoning_summary_text.delta"}:
        delta = data.get("delta") or ""
        return {"content": "", "reasoning": delta if isinstance(delta, str) else "", "tool_calls": []}

    if event_type == "response.function_call_arguments.done":
        name = data.get("name")
        if not name:
            return {"content": "", "reasoning": "", "tool_calls": []}
        return {
            "content": "",
            "reasoning": "",
            "tool_calls": [
                {
                    "id": data.get("call_id") or data.get("item_id") or f"stream_{uuid4().hex}",
                    "type": "function",
                    "function": {
                        "name": str(name),
                        "arguments": _coerce_tool_call_arguments(data.get("arguments", {})),
                    },
                }
            ],
        }

    return {"content": "", "reasoning": "", "tool_calls": []}


def _render_tool_catalog(
    tools: list[dict[str, Any]],
    *,
    max_chars: int = _EMULATED_TOOL_CATALOG_LIMIT,
) -> str:
    """Render a compact tool catalog: name + short desc + required param names only.

    Drops full parameter schemas because some upstream OpenAI-compatible proxies
    disconnect when the system prompt exceeds their internal budget.
    """
    catalog: list[dict[str, Any]] = []
    for tool in tools:
        function = tool.get("function", {})
        name = function.get("name", "")
        if not name:
            continue
        desc = str(function.get("description", "") or "").strip()
        if len(desc) > 160:
            desc = desc[:160].rstrip() + "..."
        parameters = function.get("parameters") or {}
        required = parameters.get("required") if isinstance(parameters, dict) else None
        param_names: list[str] = []
        if isinstance(parameters, dict):
            props = parameters.get("properties") or {}
            if isinstance(props, dict):
                param_names = [str(key) for key in props.keys()][:12]
        entry: dict[str, Any] = {"name": name, "desc": desc}
        if param_names:
            entry["params"] = param_names
        if isinstance(required, list) and required:
            entry["required"] = [str(item) for item in required]
        catalog.append(entry)

    rendered = json.dumps(catalog, ensure_ascii=False)
    if len(rendered) <= max_chars:
        return rendered

    kept: list[dict[str, Any]] = []
    running = 2
    for entry in catalog:
        piece = json.dumps(entry, ensure_ascii=False)
        if running + len(piece) + 1 > max_chars:
            break
        kept.append(entry)
        running += len(piece) + 1
    dropped = len(catalog) - len(kept)
    tail = f'{{"_truncated":"{dropped} more tools omitted"}}'
    return json.dumps(kept + [json.loads(tail)], ensure_ascii=False)


def _truncate_transcript_item(text: str, *, limit: int = _EMULATED_ITEM_LIMIT) -> str:
    if len(text) <= limit:
        return text

    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return f"[structured content omitted, {len(text)} chars total]"

    prefix = text[:limit]
    if prefix.count("{") > prefix.count("}") or prefix.count("[") > prefix.count("]"):
        return f"[structured content truncated safely, {len(text)} chars total]"

    return prefix + f"...[truncated, {len(text)} chars total]"


def _render_emulated_tool_transcript(
    messages: list[LLMMessage],
    *,
    max_chars: int = _EMULATED_TRANSCRIPT_LIMIT,
) -> str:
    """Flatten chat history into a plain-text transcript with per-item and total caps.

    Older items are dropped first so the most recent tool results stay intact,
    preventing unbounded chat_log growth from disconnecting the upstream.
    """
    rendered_sections: list[str] = []
    for index, message in enumerate(messages, start=1):
        role = message.role.upper()
        content = _truncate_transcript_item(
            _stringify_message_content(message.content)
        )
        if message.role == "tool":
            content = (
                f"[Tool result from {message.tool_name}]\n{content}"
                if message.tool_name
                else f"[Tool result]\n{content}"
            )
        lines = [f"[{index}] {role}", content]
        if message.tool_calls:
            lines.append(
                "TOOL_CALLS: "
                + _truncate_transcript_item(
                    json.dumps(message.tool_calls, ensure_ascii=False)
                )
            )
        if message.tool_call_id:
            lines.append(f"TOOL_CALL_ID: {message.tool_call_id}")
        if message.tool_name:
            lines.append(f"TOOL_NAME: {message.tool_name}")
        rendered_sections.append("\n".join(line for line in lines if line))

    total_len = sum(len(section) + 2 for section in rendered_sections)
    if total_len <= max_chars:
        return "\n\n".join(rendered_sections)

    kept_tail: list[str] = []
    running = 0
    for section in reversed(rendered_sections):
        piece_len = len(section) + 2
        if running + piece_len > max_chars:
            break
        kept_tail.append(section)
        running += piece_len
    kept_tail.reverse()
    dropped = len(rendered_sections) - len(kept_tail)
    if dropped:
        kept_tail.insert(0, f"[{dropped} earlier turns omitted for length]")
    return "\n\n".join(kept_tail)


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible LLM provider implementation.

    This provider can be used with any API that follows the OpenAI
    chat completions format, including:
    - OpenAI
    - Azure OpenAI
    - Local LLMs (LM Studio, Ollama, etc.)
    - Other compatible services

    Example:
        config = LLMConfig(
            api_key="your-api-key",
            model="gpt-3.5-turbo",
            base_url="https://api.openai.com/v1/chat/completions",
        )
        provider = OpenAICompatibleProvider(config)

        response = await provider.complete([
            LLMMessage(role="user", content="Hello!")
        ])
    """

    # Class-level attributes for registration
    _name = "openai_compatible"

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "openai_compatible"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models.

        Since this is a generic provider, return empty list.
        The specific models depend on the endpoint being used.
        """
        return []

    def supports_vision(self) -> bool:
        """Check if vision is supported.

        Depends on the model being used.
        """
        vision_keywords = ["vision", "4v", "gpt-4o", "4-turbo"]
        return any(kw in self.config.model.lower() for kw in vision_keywords)

    def supports_tools(self) -> bool:
        """Check if tools are supported."""
        return True

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _get_api_url(self) -> str:
        """Get the API URL."""
        return _normalize_openai_api_url(self.config.base_url)

    def _is_responses_api(self, url: str | None = None) -> bool:
        """Return whether the request should use the Responses API payload shape."""
        return _is_responses_api_url(url or self._get_api_url())

    def _build_request(
        self,
        messages: list[LLMMessage],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the API request body."""
        if self._is_responses_api():
            request = self._build_responses_request(messages, stream=stream, tools=tools, **kwargs)
            request.update(self.config.extra)
            request.update(kwargs)
            if self.config.debug_log:
                self._log_request_payload(request)
            return request

        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": self._convert_messages(messages),
            "stream": stream,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if tools:
            request["tools"] = tools

        if self.config.enable_thinking:
            request["enable_thinking"] = True

        request.update(self.config.extra)
        request.update(kwargs)

        if self.config.debug_log:
            self._log_request_payload(request)
        return request

    def _build_responses_request(
        self,
        messages: list[LLMMessage],
        stream: bool = False,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build a Responses API request body."""
        request: dict[str, Any] = {
            "model": self.config.model,
            "input": self._convert_messages_for_responses(messages),
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }

        if stream:
            request["stream"] = True

        if tools:
            request["tools"] = tools

        if self.config.enable_thinking:
            request["reasoning"] = {"effort": "medium"}

        if "max_tokens" in kwargs and "max_output_tokens" not in kwargs:
            request["max_output_tokens"] = kwargs["max_tokens"]

        return request

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert shared chat history into OpenAI-compatible message payloads."""
        converted: list[dict[str, Any]] = []

        for message in messages:
            if message.role in {"system", "user", "assistant"}:
                converted_message: dict[str, Any] = {
                    "role": message.role,
                    "content": _convert_content_blocks(message.content),
                }
                converted_tool_calls = _convert_request_tool_calls(message.tool_calls)
                if converted_tool_calls:
                    converted_message["tool_calls"] = converted_tool_calls
                # DeepSeek thinking mode requires reasoning_content to be passed back
                reasoning = getattr(message, "reasoning_content", None)
                if reasoning:
                    converted_message["reasoning_content"] = reasoning
                converted.append(converted_message)
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
                        "tool_name": message.tool_name or "tool",
                    }
                )

        return converted

    def _convert_messages_for_responses(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert shared chat history into Responses API input items."""
        converted: list[dict[str, Any]] = []

        for message in messages:
            if message.role in {"system", "user", "assistant"}:
                item: dict[str, Any] = {
                    "role": message.role,
                    "content": _convert_content_blocks_for_responses(message.content),
                }
                converted_tool_calls = _convert_request_tool_calls(message.tool_calls)
                if converted_tool_calls:
                    item["tool_calls"] = converted_tool_calls
                reasoning = getattr(message, "reasoning_content", None)
                if reasoning:
                    item["reasoning_content"] = reasoning
                converted.append(item)
                continue

            if message.role == "tool":
                tool_output = message.content
                if isinstance(tool_output, (dict, list)):
                    tool_output = json.dumps(tool_output, ensure_ascii=False, default=str)
                elif not isinstance(tool_output, str):
                    tool_output = str(tool_output) if tool_output is not None else "{}"

                converted.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.tool_call_id or "tool_call",
                        "output": tool_output,
                    }
                )

        return converted

    def _build_emulated_tool_messages(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
    ) -> list[LLMMessage]:
        """Build a plain-chat tool-emulation prompt."""
        sanitized_messages = _sanitize_messages_for_plain_chat(messages)
        system_context_parts = [
            _stringify_message_content(message.content)
            for message in sanitized_messages
            if message.role == "system"
        ]
        system_context = "\n\n".join(part for part in system_context_parts if part).strip()
        if len(system_context) > _EMULATED_SYSTEM_LIMIT:
            system_context = system_context[:_EMULATED_SYSTEM_LIMIT] + "\n\n[system context truncated]"

        transcript = _render_emulated_tool_transcript(
            [message for message in sanitized_messages if message.role != "system"]
        )
        tool_catalog = _render_tool_catalog(tools)
        system_prompt = (
            "You are a Home Assistant voice assistant. "
            "Native tool calling is unavailable for this OpenAI-compatible endpoint. "
            "You must emulate the next assistant step with strict JSON only.\n\n"
            "Original system instructions:\n"
            f"{system_context}\n\n"
            "Available tools:\n"
            f"{tool_catalog}\n\n"
            "Return exactly one JSON object in one of these forms:\n"
            '{"mode":"answer","content":"user-facing reply"}\n'
            '{"mode":"tool_calls","tool_calls":[{"name":"tool_name","arguments":{}}]}\n\n'
            "Rules:\n"
            "- Use tool_calls when tools are needed.\n"
            "- Use only the listed tool names.\n"
            "- arguments must always be a JSON object.\n"
            "- After tool results appear in the transcript, either request more tools or answer.\n"
            "- No markdown, no code fences, no extra commentary outside the JSON object."
        )
        user_prompt = (
            "Conversation transcript:\n"
            f"{transcript}\n\n"
            "Produce the next assistant step now."
        )
        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

    def _parse_emulated_tool_response(self, content: str) -> LLMResponse:
        """Parse an emulated tool-calling response."""
        payload = _extract_json_payload(content)
        if not payload:
            return LLMResponse(
                content=content.strip(),
                raw_response={"emulated_tool_calling": True, "raw_text": content},
            )

        mode = str(payload.get("mode", "")).lower()
        tool_calls_payload = payload.get("tool_calls")
        if not isinstance(tool_calls_payload, list):
            tool_calls_payload = payload.get("toolcalls")

        if mode in {"tool_calls", "toolcalls"}:
            tool_calls: list[dict[str, Any]] = []
            for item in (tool_calls_payload or [])[:8]:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                arguments = item.get("arguments", {})
                if not name:
                    continue
                if not isinstance(arguments, dict):
                    arguments = {"value": arguments}
                tool_calls.append(
                    {
                        "id": f"emulated_{uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": str(name),
                            "arguments": json.dumps(arguments, ensure_ascii=False),
                        },
                    }
                )
            if tool_calls:
                return LLMResponse(
                    content="",
                    tool_calls=tool_calls,
                    raw_response={
                        "emulated_tool_calling": True,
                        "parsed": payload,
                    },
                )

        answer = payload.get("content")
        if isinstance(answer, str):
            return LLMResponse(
                content=answer,
                raw_response={"emulated_tool_calling": True, "parsed": payload},
            )

        return LLMResponse(
            content=content.strip(),
            raw_response={"emulated_tool_calling": True, "parsed": payload},
        )

    def _log_request_payload(self, request: dict[str, Any]) -> None:
        """Log full request payload for debugging (uses WARNING level to ensure visibility)."""
        try:
            msgs = request.get("messages") or request.get("input") or []
            tools = request.get("tools") or []
            _LOGGER.warning(
                "[AI_HUB_DEBUG] request model=%s stream=%s msg_count=%d tool_count=%d",
                request.get("model", "?"),
                request.get("stream", False),
                len(msgs),
                len(tools),
            )
            for i, msg in enumerate(msgs):
                role = msg.get("role", "?")
                content = msg.get("content", "")
                content_preview = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
                if len(content_preview) > 2000:
                    content_preview = content_preview[:2000] + f"...[truncated, total {len(content_preview)}]"
                tc = msg.get("tool_calls")
                tc_info = f" tool_calls={json.dumps(tc, ensure_ascii=False)}" if tc else ""
                extra_keys = {k: msg[k] for k in msg if k not in ("role", "content", "tool_calls")}
                extra_info = f" extra={json.dumps(extra_keys, ensure_ascii=False, default=str)}" if extra_keys else ""
                _LOGGER.warning(
                    "[AI_HUB_DEBUG]   msg[%d] role=%s content=%s%s%s",
                    i, role, content_preview, tc_info, extra_info,
                )
            if tools:
                for i, tool in enumerate(tools):
                    _LOGGER.warning(
                        "[AI_HUB_DEBUG]   tool[%d] %s",
                        i,
                        json.dumps(tool, ensure_ascii=False)[:500],
                    )
        except Exception:
            _LOGGER.warning("[AI_HUB_DEBUG] failed to log request payload", exc_info=True)

    async def _perform_request(
        self,
        *,
        request: dict[str, Any],
        headers: dict[str, str],
        url: str,
        ssl: bool,
    ) -> dict[str, Any]:
        """Execute a non-streaming request with auto retry on transient disconnects."""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            try:
                body_size = len(json.dumps(request, ensure_ascii=False))
            except Exception:
                body_size = -1
            msgs = request.get("messages") or []
            _LOGGER.debug(
                "OpenAI-compatible request: url=%s messages=%d body=%dB tools=%s",
                url,
                len(msgs),
                body_size,
                bool(request.get("tools")),
            )

        last_error: Exception | None = None
        for attempt in range(_DISCONNECT_RETRY_MAX + 1):
            try:
                data = await async_post_json(
                    url,
                    payload=request,
                    headers=headers,
                    ssl=ssl,
                    timeout=self.config.timeout,
                    error_label="API error",
                    response_decoder=_decode_json_response,
                )
                if self.config.debug_log:
                    try:
                        # Log cache hit info if available
                        usage = data.get("usage", {})
                        if isinstance(usage, dict):
                            cache_info = ""
                            # OpenAI style: prompt_tokens_details.cached_tokens
                            details = usage.get("prompt_tokens_details", {})
                            if isinstance(details, dict) and details.get("cached_tokens"):
                                cached = details["cached_tokens"]
                                total = usage.get("prompt_tokens", 0)
                                hit_rate = (cached / total * 100) if total > 0 else 0
                                cache_info = f" cache_hit={cached}/{total}({hit_rate:.1f}%)"
                            # DeepSeek style: prompt_cache_hit_tokens
                            elif usage.get("prompt_cache_hit_tokens"):
                                cached = usage["prompt_cache_hit_tokens"]
                                total = usage.get("prompt_tokens", 0)
                                hit_rate = (cached / total * 100) if total > 0 else 0
                                cache_info = f" cache_hit={cached}/{total}({hit_rate:.1f}%)"
                            _LOGGER.warning(
                                "[AI_HUB_DEBUG] response tokens: in=%s out=%s%s",
                                usage.get("prompt_tokens", usage.get("input_tokens", "?")),
                                usage.get("completion_tokens", usage.get("output_tokens", "?")),
                                cache_info,
                            )
                        resp_preview = json.dumps(data, ensure_ascii=False, default=str)
                        if len(resp_preview) > 3000:
                            resp_preview = resp_preview[:3000] + "...[truncated]"
                        _LOGGER.warning("[AI_HUB_DEBUG] response: %s", resp_preview)
                    except Exception:
                        _LOGGER.warning("[AI_HUB_DEBUG] response keys: %s", list(data.keys()) if isinstance(data, dict) else type(data))
                return data
            except _RETRYABLE_DISCONNECT_ERRORS as err:
                last_error = err
                if attempt >= _DISCONNECT_RETRY_MAX:
                    break
                backoff = _DISCONNECT_RETRY_BACKOFF_SECONDS * (attempt + 1)
                if attempt >= 2:
                    _LOGGER.info(
                        "Upstream disconnected (%s); retry %d/%d after %.1fs",
                        err.__class__.__name__,
                        attempt + 1,
                        _DISCONNECT_RETRY_MAX,
                        backoff,
                    )
                await asyncio.sleep(backoff)
        assert last_error is not None
        raise last_error

    def _supports_tool_compat_retry(self, err: Exception, tools: list[dict[str, Any]] | None) -> bool:
        """Return whether we should retry as plain chat without tools."""
        if not tools:
            return False
        return isinstance(err, aiohttp.ClientError)

    async def _complete_with_emulated_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Run tool-capable turns through JSON-based tool emulation."""
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = _get_ssl_setting(url)
        request = self._build_request(
            self._build_emulated_tool_messages(messages, tools),
            stream=False,
            tools=None,
            **kwargs,
        )
        data = await self._perform_request(
            request=request,
            headers=headers,
            url=url,
            ssl=ssl,
        )
        _choice, message = _extract_response_payload(data)
        return self._parse_emulated_tool_response(
            _extract_response_content(message, data)
        )

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion.

        Args:
            messages: List of conversation messages
            tools: Optional list of tools
            **kwargs: Additional parameters

        Returns:
            LLMResponse containing the generated content
        """
        request = self._build_request(messages, stream=False, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()

        if tools and _NATIVE_TOOL_SUPPORT_BY_URL.get(url) is False:
            _LOGGER.info(
                "OpenAI-compatible endpoint is marked as no-native-tools; using emulated tool mode: %s",
                url,
            )
            return await self._complete_with_emulated_tools(messages, tools, **kwargs)

        try:
            data = await self._perform_request(
                request=request,
                headers=headers,
                url=url,
                ssl=_get_ssl_setting(url),
            )
        except Exception as err:
            if self.config.debug_log:
                _LOGGER.warning(
                    "[AI_HUB_DEBUG] API error: %s url=%s model=%s",
                    err, url, request.get("model", "?"),
                )
            if not self._supports_tool_compat_retry(err, tools):
                raise

            _LOGGER.warning(
                "OpenAI-compatible endpoint disconnected with tools; switching to emulated tool mode: %s",
                err,
            )
            _NATIVE_TOOL_SUPPORT_BY_URL[url] = False
            return await self._complete_with_emulated_tools(
                messages,
                tools or [],
                **kwargs,
            )
        else:
            if tools:
                _NATIVE_TOOL_SUPPORT_BY_URL[url] = True

        choice, message = _extract_response_payload(data)

        return LLMResponse(
            content=_extract_response_content(message, data),
            tool_calls=_extract_response_tool_calls(message),
            usage=data.get("usage"),
            model=data.get("model"),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
            reasoning_content=message.get("reasoning_content"),
        )

    async def complete_stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str | dict[str, Any], None]:
        """Generate a streaming completion.

        Args:
            messages: List of conversation messages
            tools: Optional list of tools
            **kwargs: Additional parameters

        Yields:
            Generated content chunks
        """
        request = self._build_request(messages, stream=True, tools=tools, **kwargs)
        headers = self._get_headers()
        url = self._get_api_url()
        ssl = _get_ssl_setting(url)
        if self.config.debug_log:
            _LOGGER.warning("[AI_HUB_DEBUG] complete_stream url=%s model=%s", url, request.get("model", "?"))

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

                if not line or line == "data: [DONE]":
                    continue

                data_str = line[6:] if line.startswith("data: ") else line
                if not data_str.strip():
                    continue

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    _LOGGER.debug("SSE parse failed: %s", data_str)
                    continue

                if _is_responses_api_url(url):
                    delta = _extract_responses_stream_delta(data)
                    if delta["reasoning"]:
                        yield {"thinking_content": delta["reasoning"]}
                    if delta["content"]:
                        yield delta["content"]
                    for tool_call in delta["tool_calls"]:
                        tool_call_buffer[len(tool_call_buffer)] = tool_call
                    continue

                choices = data.get("choices")
                if isinstance(choices, list) and choices:
                    first_choice = choices[0]
                    if not isinstance(first_choice, dict):
                        _LOGGER.debug("OpenAI-compatible SSE first choice is invalid: %s", data)
                        continue

                    delta = first_choice.get("delta", {})
                    if not isinstance(delta, dict):
                        _LOGGER.debug("OpenAI-compatible SSE delta is invalid: %s", data)
                        continue

                    reasoning = delta.get("reasoning_content") or delta.get("thinking_content") or ""
                    if reasoning:
                        yield {"thinking_content": reasoning}
                    content = delta.get("content", "")
                    if content:
                        yield content
                    if "tool_calls" in delta:
                        for tc_delta in delta["tool_calls"]:
                            index = tc_delta.get("index", 0)
                            if index not in tool_call_buffer:
                                tool_call_buffer[index] = {
                                    "id": tc_delta.get("id") or f"stream_{uuid4().hex}",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""},
                                }
                            if tc_delta.get("id"):
                                tool_call_buffer[index]["id"] = tc_delta["id"]
                            if "function" in tc_delta:
                                function_data = tc_delta["function"]
                                if function_data.get("name"):
                                    tool_call_buffer[index]["function"]["name"] = function_data["name"]
                                if function_data.get("arguments"):
                                    tool_call_buffer[index]["function"]["arguments"] += function_data["arguments"]
                    continue

                _LOGGER.debug("OpenAI-compatible stream chunk in unknown format: %s", data)

        if tool_call_buffer:
            tool_calls = finalize_buffered_tool_calls(tool_call_buffer)
            if tool_calls:
                yield {"tool_calls": tool_calls}

    async def health_check(self) -> bool:
        """Check if the API is reachable."""
        try:
            url = self._get_api_url()
            ssl = _get_ssl_setting(url)

            return await check_provider_health(url, ssl=ssl, timeout=10)
        except Exception as e:
            _LOGGER.debug("OpenAI compatible health check failed: %s", e)
            return False
