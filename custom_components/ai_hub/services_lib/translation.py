"""Translation services for AI Hub - 组件翻译功能.

本模块提供 Home Assistant 自定义组件的翻译服务，使用 SiliconFlow AI 进行翻译。

主要函数:
- async_translate_text: 异步翻译单个文本
- async_translate_json_values: 异步递归翻译 JSON 值
- async_translate_component: 异步翻译单个组件
- async_translate_all_components: 异步翻译所有组件

翻译特性:
- 自动保留占位符 ({}, %s, ${} 等)
- 智能跳过纯占位符文本
- 支持批量处理和强制重新翻译
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

import aiohttp

from ..consts import (
    AI_HUB_CHAT_URL,
    RECOMMENDED_CHAT_MODEL,
    TIMEOUT_TRANSLATION_API,
    TRANSLATION_MAX_TOKENS,
    TRANSLATION_SYSTEM_PROMPT,
    TRANSLATION_TEMPERATURE,
)
from .batch_utils import build_batch_result, build_list_result, select_named_items

_LOGGER = logging.getLogger(__name__)


async def async_translate_text(
    text: str,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> str:
    """异步翻译文本，保留占位符."""
    if not text or len(text.strip()) < 2:
        return text

    placeholder_pattern = r'\{[^}]+\}|%\w+|\$\{[^}]+\}'

    if re.fullmatch(placeholder_pattern, text.strip()):
        return text

    if text.startswith(("{", "%", "${")) or text.isupper():
        return text

    placeholders = re.findall(placeholder_pattern, text)

    if not placeholders:
        return await _async_translate_simple_text(text, api_key, api_url, model)

    placeholder_map = {}
    temp_text = text
    for i, placeholder in enumerate(placeholders):
        marker = f"__PLACEHOLDER_{i}__"
        placeholder_map[marker] = placeholder
        temp_text = temp_text.replace(placeholder, marker, 1)

    translated_temp = await _async_translate_simple_text(temp_text, api_key, api_url, model)

    translated_text = translated_temp
    for marker, placeholder in placeholder_map.items():
        translated_text = translated_text.replace(marker, placeholder)

    return translated_text


async def async_translate_json_values(
    data,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
):
    """异步递归翻译JSON值."""
    if isinstance(data, dict):
        return {key: await async_translate_json_values(value, api_key, api_url, model) for key, value in data.items()}
    elif isinstance(data, list):
        return [await async_translate_json_values(item, api_key, api_url, model) for item in data]
    elif isinstance(data, str) and data.strip():
        return await async_translate_text(data, api_key, api_url, model)
    else:
        return data


async def _async_translate_simple_text(
    text: str,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> str:
    """异步翻译函数."""
    # Use provided values or defaults
    url = api_url or AI_HUB_CHAT_URL
    chat_model = model or RECOMMENDED_CHAT_MODEL

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": chat_model,
        "messages": [
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": TRANSLATION_TEMPERATURE,
        "max_tokens": TRANSLATION_MAX_TOKENS
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload,
                                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_TRANSLATION_API)) as response:
                response.raise_for_status()
                result = await response.json()
                return result["choices"][0]["message"]["content"].strip()
    except Exception as err:
        _LOGGER.error("Translation failed for '%s': %s", text, err)
        return text


def _read_json_file(path: Path) -> Any:
    """Read a JSON file synchronously."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(path: Path, data: Any) -> None:
    """Write a JSON file synchronously."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _iter_component_dirs(base_path: Path) -> list[Path]:
    """List component directories synchronously."""
    return [
        d for d in base_path.iterdir()
        if d.is_dir() and d.name not in ["ai_hub", "translation_localizer"]
    ]


async def async_translate_component(
    component_dir: Path,
    component_name: str,
    api_key: str,
    force_translation: bool = False,
    api_url: str | None = None,
    model: str | None = None
) -> str:
    """异步翻译单个组件."""
    translations_dir = component_dir / "translations"
    en_file = translations_dir / "en.json"
    zh_file = translations_dir / "zh-Hans.json"

    if not await asyncio.to_thread(translations_dir.exists) or not await asyncio.to_thread(
        en_file.exists
    ):
        return "skipped"

    if await asyncio.to_thread(zh_file.exists) and not force_translation:
        return "skipped"

    try:
        en_data = await asyncio.to_thread(_read_json_file, en_file)

        zh_data = await async_translate_json_values(en_data, api_key, api_url, model)

        await asyncio.to_thread(_write_json_file, zh_file, zh_data)

        _LOGGER.info(f"Successfully translated {component_name}")
        return "translated"
    except Exception as err:
        _LOGGER.error("Failed to translate %s: %s", component_name, err)
        return "error"


async def async_translate_all_components(
    custom_components_path: str = "custom_components",
    api_key: str | None = None,
    force_translation: bool = False,
    target_component: str = "",
    list_components: bool = False,
    api_url: str | None = None,
    model: str | None = None
) -> dict:
    """异步翻译所有组件."""
    base_path = None
    paths_to_try = [
        Path(custom_components_path),
        Path("/config") / custom_components_path,
        Path.home() / ".homeassistant" / custom_components_path,
    ]

    for path in paths_to_try:
        if await asyncio.to_thread(path.exists) and await asyncio.to_thread(path.is_dir):
            base_path = path
            break

    if not base_path:
        return {"error": f"Custom components directory not found: {custom_components_path}"}

    if list_components:
        all_components = []
        available_translations = []

        for component_dir in await asyncio.to_thread(_iter_component_dirs, base_path):
            all_components.append(component_dir.name)
            zh_file = component_dir / "translations" / "zh-Hans.json"
            if await asyncio.to_thread(zh_file.exists):
                available_translations.append(component_dir.name)

        return build_list_result(
            mode="list_only",
            total_key="total_components",
            all_items_key="all_components",
            all_items=sorted(all_components),
            translated_key="components_with_translations",
            translated_items=sorted(available_translations),
        )

    translated_components = []
    skipped_components = []

    component_dirs = await asyncio.to_thread(_iter_component_dirs, base_path)
    component_dirs, error = select_named_items(
        component_dirs,
        target_component,
        matcher=lambda item, target: item.name == target,
        not_found_error=f"Target component not found: {target_component}",
    )
    if error is not None:
        return error
    assert component_dirs is not None

    for component_dir in component_dirs:
        result = await async_translate_component(
            component_dir, component_dir.name, api_key, force_translation, api_url, model
        )
        if result == "translated":
            translated_components.append(component_dir.name)
        else:
            skipped_components.append(component_dir.name)

    return build_batch_result(
        mode="translate",
        translated_items=translated_components,
        skipped_items=skipped_components,
        translated_key="translated_components",
        skipped_key="skipped_components",
    )
