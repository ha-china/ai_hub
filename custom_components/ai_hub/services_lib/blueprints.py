"""Blueprint translation services for AI Hub - 蓝图翻译功能.

本模块提供 Home Assistant 蓝图 (Blueprint) 的翻译服务。

主要函数:
- async_translate_blueprint_file: 异步翻译单个蓝图文件
- async_translate_all_blueprints: 异步翻译所有蓝图

翻译特性:
- 保护 Home Assistant 特殊语法 (!input, !secret, !include)
- 智能翻译 name, description 等用户界面文本
- 支持嵌套结构和复杂蓝图
- 原位翻译，不产生额外文件
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import yaml

from .batch_utils import build_batch_result, build_list_result, select_named_items
from .translation import async_translate_text

_LOGGER = logging.getLogger(__name__)


async def _async_translate_blueprint_inputs(
    inputs: dict,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> None:
    """异步递归翻译blueprint的input字段."""
    for key, value in inputs.items():
        if isinstance(value, dict):
            if 'name' in value and isinstance(value['name'], str):
                value['name'] = await async_translate_text(value['name'], api_key, api_url, model)
            if 'description' in value and isinstance(value['description'], str):
                value['description'] = await async_translate_text(value['description'], api_key, api_url, model)
            if 'default' in value and isinstance(value['default'], str) and len(value['default']) > 2:
                value['default'] = await async_translate_text(value['default'], api_key, api_url, model)
            if 'selector' in value and isinstance(value['selector'], dict):
                await _async_translate_blueprint_selectors(value['selector'], api_key, api_url, model)
            if 'input' in value and isinstance(value['input'], dict):
                await _async_translate_blueprint_inputs(value['input'], api_key, api_url, model)
        elif isinstance(value, str) and len(value) > 2:
            inputs[key] = await async_translate_text(value, api_key, api_url, model)


async def _async_translate_blueprint_variables(
    variables: dict,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> None:
    """异步递归翻译blueprint的variables字段."""
    for key, value in variables.items():
        if isinstance(value, str) and len(value) > 2:
            variables[key] = await async_translate_text(value, api_key, api_url, model)


async def _async_translate_blueprint_selectors(
    selector: dict,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> None:
    """异步递归翻译blueprint的selector字段."""
    if 'select' in selector and isinstance(selector['select'], dict):
        options = selector['select'].get('options')
        if isinstance(options, list):
            for i, option in enumerate(options):
                if isinstance(option, str) and len(option) > 2:
                    options[i] = await async_translate_text(option, api_key, api_url, model)
        elif isinstance(options, dict):
            for key, value in options.items():
                if isinstance(value, str) and len(value) > 2:
                    options[key] = await async_translate_text(value, api_key, api_url, model)


async def _async_translate_blueprint_section_descriptions(
    item: dict,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> None:
    """异步递归翻译blueprint各section中的description字段."""
    if 'description' in item and isinstance(item['description'], str):
        item['description'] = await async_translate_text(item['description'], api_key, api_url, model)
    if 'alias' in item and isinstance(item['alias'], str):
        item['alias'] = await async_translate_text(item['alias'], api_key, api_url, model)
    if 'mode' in item and isinstance(item['mode'], str):
        item['mode'] = await async_translate_text(item['mode'], api_key, api_url, model)

    for key, value in item.items():
        if isinstance(value, dict):
            await _async_translate_blueprint_section_descriptions(value, api_key, api_url, model)
        elif isinstance(value, list):
            for list_item in value:
                if isinstance(list_item, dict):
                    await _async_translate_blueprint_section_descriptions(list_item, api_key, api_url, model)


async def async_translate_blueprint_file(
    yaml_file: Path,
    api_key: str,
    api_url: str | None = None,
    model: str | None = None
) -> str:
    """异步翻译单个blueprint YAML文件."""
    _LOGGER.info(f"Translating {yaml_file.name} (async)")

    try:
        def home_assistant_constructor(loader, node):
            if node.tag == '!input':
                return f"!{loader.construct_scalar(node)}"
            return loader.construct_scalar(node)

        yaml.SafeLoader.add_constructor('!input', home_assistant_constructor)
        yaml.SafeLoader.add_constructor('!secret', home_assistant_constructor)
        yaml.SafeLoader.add_constructor('!include', home_assistant_constructor)

        content = await asyncio.to_thread(yaml_file.read_text, encoding='utf-8')
        blueprint_data = yaml.safe_load(content)

        if not blueprint_data or 'blueprint' not in blueprint_data:
            return "skipped (not a valid blueprint)"

        blueprint_section = blueprint_data.get('blueprint', {})

        if 'name' in blueprint_section and isinstance(blueprint_section['name'], str):
            blueprint_section['name'] = await async_translate_text(
                blueprint_section['name'], api_key, api_url, model
            )
        if 'description' in blueprint_section and isinstance(blueprint_section['description'], str):
            blueprint_section['description'] = await async_translate_text(
                blueprint_section['description'], api_key, api_url, model
            )
        if 'input' in blueprint_section and isinstance(blueprint_section['input'], dict):
            await _async_translate_blueprint_inputs(blueprint_section['input'], api_key, api_url, model)
        if 'variables' in blueprint_section and isinstance(blueprint_section['variables'], dict):
            await _async_translate_blueprint_variables(blueprint_section['variables'], api_key, api_url, model)

        blueprint_data['blueprint'] = blueprint_section

        for section in ['action', 'trigger', 'condition']:
            if section in blueprint_data and isinstance(blueprint_data[section], list):
                for item in blueprint_data[section]:
                    if isinstance(item, dict):
                        await _async_translate_blueprint_section_descriptions(item, api_key, api_url, model)

        if 'mode' in blueprint_data and isinstance(blueprint_data['mode'], dict):
            await _async_translate_blueprint_section_descriptions(blueprint_data['mode'], api_key, api_url, model)
        if 'trace' in blueprint_data and isinstance(blueprint_data['trace'], dict):
            await _async_translate_blueprint_section_descriptions(blueprint_data['trace'], api_key, api_url, model)

        class HomeAssistantDumper(yaml.SafeDumper):
            def represent_scalar(self, tag, value, style=None):
                if isinstance(value, str) and value.startswith('!input'):
                    return self.represent_scalar('tag:yaml.org,2002:str', value, style)
                return super().represent_scalar(tag, value, style)

        output = yaml.dump(blueprint_data, allow_unicode=True, Dumper=HomeAssistantDumper, sort_keys=False)
        await asyncio.to_thread(yaml_file.write_text, output, encoding='utf-8')

        return "translated"

    except Exception as err:
        _LOGGER.error("Error translating blueprint %s: %s", yaml_file, err)
        return f"skipped (error: {err})"


async def async_translate_all_blueprints(
    api_key: str,
    retranslate: bool = False,
    target_blueprint: str = "",
    list_blueprints: bool = False,
    blueprints_path: str = "/config/blueprints",
    api_url: str | None = None,
    model: str | None = None
) -> dict:
    """异步翻译或列出blueprints目录中的文件."""
    base_path = Path(blueprints_path)

    if not await asyncio.to_thread(base_path.exists) or not await asyncio.to_thread(
        base_path.is_dir
    ):
        return {"translated": 0, "skipped": 0, "error": f"Blueprints directory not found: {blueprints_path}"}

    _LOGGER.info(f"Scanning blueprints in: {base_path}")

    if list_blueprints:
        all_blueprints = []
        available_translations = []

        for yaml_file in await asyncio.to_thread(list, base_path.rglob("*.yaml")):
            blueprint_info = {"path": str(yaml_file.relative_to(base_path)), "has_translation": False, "name": ""}

            try:
                content = await asyncio.to_thread(yaml_file.read_text, encoding='utf-8')
                blueprint_data = yaml.safe_load(content)
                if blueprint_data and 'blueprint' in blueprint_data:
                    blueprint_info["name"] = blueprint_data['blueprint'].get('name', '')
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(blueprint_data))
                    if has_chinese:
                        blueprint_info["has_translation"] = True
                        available_translations.append(str(yaml_file.relative_to(base_path)))
            except Exception:
                pass

            all_blueprints.append(blueprint_info)

        return build_list_result(
            mode="list_only",
            total_key="total_blueprints",
            all_items_key="all_blueprints",
            all_items=all_blueprints,
            translated_key="blueprints_with_translations",
            translated_items=available_translations,
            extra={
                "available_translations": len(available_translations),
                "target_blueprint": target_blueprint,
            },
        )

    translated_blueprints = []
    skipped_blueprints = []

    yaml_files = await asyncio.to_thread(list, base_path.rglob("*.yaml"))
    yaml_files, error = select_named_items(
        yaml_files,
        target_blueprint,
        matcher=lambda item, target: item.name == target or item.name == f"{target}.yaml",
        not_found_error=f"Target blueprint not found: {target_blueprint}",
    )
    if error is not None:
        return {"translated": 0, "skipped": 0, **error}
    assert yaml_files is not None

    for yaml_file in yaml_files:
        try:
            if not retranslate:
                try:
                    content = await asyncio.to_thread(yaml_file.read_text, encoding='utf-8')
                    if any('\u4e00' <= char <= '\u9fff' for char in content):
                        skipped_blueprints.append(str(yaml_file.relative_to(base_path)))
                        continue
                except Exception:
                    pass

            result = await async_translate_blueprint_file(yaml_file, api_key, api_url, model)
            if result == "translated":
                translated_blueprints.append(str(yaml_file.relative_to(base_path)))
            else:
                skipped_blueprints.append(str(yaml_file.relative_to(base_path)))
        except Exception as err:
            _LOGGER.error("Error processing %s: %s", yaml_file, err)
            skipped_blueprints.append(str(yaml_file.relative_to(base_path)))

    return build_batch_result(
        mode="translation",
        translated_items=translated_blueprints,
        skipped_items=skipped_blueprints,
        translated_key="translated_blueprints",
        skipped_key="skipped_blueprints",
        extra={"target_blueprint": target_blueprint},
    )
