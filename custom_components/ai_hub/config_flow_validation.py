"""Validation helpers for AI Hub config flows."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

import aiohttp
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from .consts import (
    CONF_CHAT_URL,
    CONF_CHAT_MODEL,
    CONF_CUSTOM_API_KEY,
    CONF_LLM_PROVIDER,
    AI_HUB_CHAT_URL,
    CONFIG_FLOW_TEST_MAX_TOKENS,
    CONFIG_FLOW_TEST_MESSAGE,
    RECOMMENDED_CHAT_MODEL,
    SILICONFLOW_API_KEY_URL,
    SILICONFLOW_REGISTER_URL,
    TIMEOUT_CONFIG_FLOW_VALIDATION,
)
from .http import build_json_headers, client_timeout
from .providers.openai_compatible import _normalize_openai_api_url

FLOW_DESCRIPTION_PLACEHOLDERS = {
    "register_url": SILICONFLOW_REGISTER_URL,
    "api_key_url": SILICONFLOW_API_KEY_URL,
}


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    del hass
    api_key = data.get(CONF_API_KEY, "").strip()
    if not api_key:
        return

    payload = {
        "model": RECOMMENDED_CHAT_MODEL,
        "messages": [{"role": "user", "content": CONFIG_FLOW_TEST_MESSAGE}],
        "max_tokens": CONFIG_FLOW_TEST_MAX_TOKENS,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AI_HUB_CHAT_URL,
                json=payload,
                headers=build_json_headers(api_key),
                timeout=client_timeout(TIMEOUT_CONFIG_FLOW_VALIDATION),
            ) as response:
                if response.status == 401:
                    raise ValueError("invalid_auth")
                if response.status != 200:
                    error_text = await response.text()
                    detail = error_text if error_text.strip() else f"HTTP {response.status}"
                    raise ValueError(f"cannot_connect:{detail}")
    except aiohttp.ClientError as err:
        detail = str(err).strip() or type(err).__name__
        raise ValueError(f"cannot_connect:{detail}") from err
    except asyncio.TimeoutError as err:
        detail = str(err).strip() or type(err).__name__
        raise ValueError(f"cannot_connect:{detail}") from err


def _openai_endpoint_candidates(url: str | None) -> list[str]:
    """Build config-time endpoint candidates for OpenAI-compatible URLs."""
    normalized = _normalize_openai_api_url(url)
    original_path = urlparse((url or "").rstrip("/")).path.rstrip("/")
    normalized_path = urlparse(normalized).path.rstrip("/")

    if original_path.endswith(("/chat/completions", "/completions", "/responses")):
        return [normalized]

    if normalized_path.endswith("/chat/completions"):
        root = normalized[: -len("/chat/completions")]
        return [normalized, f"{root}/responses"]

    return [normalized]


def _build_probe_payload(url: str, model: str) -> dict[str, Any]:
    """Build the smallest probe request for the endpoint shape."""
    if urlparse(url).path.rstrip("/").endswith("/responses"):
        return {
            "model": model,
            "input": CONFIG_FLOW_TEST_MESSAGE,
            "max_output_tokens": CONFIG_FLOW_TEST_MAX_TOKENS,
        }

    return {
        "model": model,
        "messages": [{"role": "user", "content": CONFIG_FLOW_TEST_MESSAGE}],
        "max_tokens": CONFIG_FLOW_TEST_MAX_TOKENS,
    }


def _should_try_next_endpoint(status: int, detail: str) -> bool:
    """Return whether the error looks like an unsupported endpoint."""
    if status == 404:
        return True

    message = detail.lower()
    return any(
        marker in message
        for marker in (
            "not found",
            "unsupported",
            "unknown path",
            "unknown endpoint",
            "invalid endpoint",
            "invalid url",
            "no route",
        )
    )


async def resolve_openai_chat_url(
    url: str | None,
    api_key: str,
    model: str,
    max_retries: int = 2,
) -> str:
    """Resolve and validate the final OpenAI-compatible endpoint during config."""
    candidates = _openai_endpoint_candidates(url)
    headers = build_json_headers(api_key)
    last_error: str | None = None

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                for index, candidate in enumerate(candidates):
                    payload = _build_probe_payload(candidate, model)
                    try:
                        async with session.post(
                            candidate,
                            json=payload,
                            headers=headers,
                            timeout=client_timeout(TIMEOUT_CONFIG_FLOW_VALIDATION),
                        ) as response:
                            if response.status == 401:
                                raise ValueError("invalid_auth")
                            if response.status == 200:
                                return candidate

                            error_text = await response.text()
                            detail = error_text.strip() or f"HTTP {response.status}"
                            last_error = detail
                            if index < len(candidates) - 1 and _should_try_next_endpoint(response.status, detail):
                                continue
                            return candidate
                    except aiohttp.ClientError as err:
                        last_error = str(err).strip() or type(err).__name__
                        raise
                    except asyncio.TimeoutError as err:
                        last_error = str(err).strip() or type(err).__name__
                        raise
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise ValueError(f"cannot_connect:{last_error}") from None

    raise ValueError(f"cannot_connect:{last_error or 'unknown endpoint error'}")


async def normalize_subentry_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Normalize subentry network settings before saving them."""
    del hass
    normalized = dict(data)
    provider = normalized.get(CONF_LLM_PROVIDER)
    chat_url = normalized.get(CONF_CHAT_URL)
    api_key = str(normalized.get(CONF_API_KEY, "") or normalized.get(CONF_CUSTOM_API_KEY, "")).strip()
    model = str(normalized.get(CONF_CHAT_MODEL) or RECOMMENDED_CHAT_MODEL)

    if (
        provider == "openai_compatible"
        and isinstance(chat_url, str)
        and chat_url.strip()
        and api_key
    ):
        fallback_url = _normalize_openai_api_url(chat_url)
        try:
            normalized[CONF_CHAT_URL] = await resolve_openai_chat_url(chat_url, api_key, model)
        except ValueError as err:
            reason = str(err)
            if reason.startswith("cannot_connect"):
                normalized[CONF_CHAT_URL] = fallback_url
            else:
                raise
    elif provider == "openai_compatible" and isinstance(chat_url, str) and chat_url.strip():
        normalized[CONF_CHAT_URL] = _normalize_openai_api_url(chat_url)

    return normalized
