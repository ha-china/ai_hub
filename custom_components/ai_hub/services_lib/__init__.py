"""Services library module for AI Hub integration - 模块化服务.

本模块提供 AI Hub 集成的所有服务功能，包括：

模块结构:
- schemas.py: 服务调用的数据验证模式
- image.py: 图像分析和生成服务
- stt.py: 语音转文本服务
- translation.py: 组件翻译服务
- blueprints.py: 蓝图翻译服务

使用示例:
    from .services_lib import (
        handle_analyze_image,
        handle_generate_image,
        handle_stt_transcribe,
    )

    # 在服务注册中使用
    result = await handle_analyze_image(hass, call, api_key)
"""

from __future__ import annotations

# Blueprint translation services
from .blueprints import (
    async_translate_all_blueprints,
    async_translate_blueprint_file,
)

# Image services
from .image import (
    handle_analyze_image,
    handle_generate_image,
    handle_stream_response,
    load_image_from_camera,
    load_image_from_file,
    process_image,
)

# Schemas
from .schemas import (
    BLUEPRINTS_TRANSLATION_SCHEMA,
    IMAGE_ANALYZER_SCHEMA,
    IMAGE_GENERATOR_SCHEMA,
    STT_SCHEMA,
    TRANSLATION_SCHEMA,
)

# STT services
from .stt import handle_stt_transcribe

# Translation services
from .translation import (
    async_translate_all_components,
    async_translate_component,
    async_translate_json_values,
    async_translate_text,
)

__all__ = [
    # Schemas
    "IMAGE_ANALYZER_SCHEMA",
    "IMAGE_GENERATOR_SCHEMA",
    "STT_SCHEMA",
    "TRANSLATION_SCHEMA",
    "BLUEPRINTS_TRANSLATION_SCHEMA",
    # Image
    "handle_analyze_image",
    "handle_generate_image",
    "load_image_from_file",
    "load_image_from_camera",
    "process_image",
    "handle_stream_response",
    # STT
    "handle_stt_transcribe",
    # Translation
    "async_translate_text",
    "async_translate_json_values",
    "async_translate_component",
    "async_translate_all_components",
    # Blueprints
    "async_translate_blueprint_file",
    "async_translate_all_blueprints",
]
