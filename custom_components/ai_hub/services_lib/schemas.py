"""Service schemas for AI Hub integration - 服务调用数据验证模式.

本模块定义所有 AI Hub 服务的数据验证模式 (Schema)。

可用模式:
- IMAGE_ANALYZER_SCHEMA: 图像分析服务
- IMAGE_GENERATOR_SCHEMA: 图像生成服务
- STT_SCHEMA: 语音转文本服务
- TRANSLATION_SCHEMA: 组件翻译服务
- BLUEPRINTS_TRANSLATION_SCHEMA: 蓝图翻译服务
"""

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from ..consts import (
    CONF_STT_FILE,
    IMAGE_SIZES,
    RECOMMENDED_IMAGE_ANALYSIS_MODEL,
    RECOMMENDED_IMAGE_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_STT_MODEL,
    RECOMMENDED_TEMPERATURE,
    SILICONFLOW_STT_MODELS,
)

CONFIG_ENTRY_FIELD = {vol.Optional("config_entry_id"): cv.string}

# Schema for image analysis service
IMAGE_ANALYZER_SCHEMA = {
    **CONFIG_ENTRY_FIELD,
    vol.Optional("image_file"): cv.string,
    vol.Optional("image_entity"): cv.entity_id,
    vol.Required("message"): cv.string,
    vol.Optional("model", default=RECOMMENDED_IMAGE_ANALYSIS_MODEL): cv.string,
    vol.Optional("temperature", default=RECOMMENDED_TEMPERATURE): vol.Coerce(float),
    vol.Optional("max_tokens", default=RECOMMENDED_MAX_TOKENS): cv.positive_int,
    vol.Optional("stream", default=False): cv.boolean,
}

# Schema for image generation service
IMAGE_GENERATOR_SCHEMA = {
    **CONFIG_ENTRY_FIELD,
    vol.Required("prompt"): cv.string,
    vol.Optional("size", default="1024x1024"): vol.In(IMAGE_SIZES),
    vol.Optional("model", default=RECOMMENDED_IMAGE_MODEL): cv.string,
}

# Schema for Silicon Flow STT service
STT_SCHEMA = {
    **CONFIG_ENTRY_FIELD,
    vol.Required(CONF_STT_FILE): cv.string,
    vol.Optional("model", default=RECOMMENDED_STT_MODEL): vol.In(SILICONFLOW_STT_MODELS),
}

# Schema for translation service
TRANSLATION_SCHEMA = {
    **CONFIG_ENTRY_FIELD,
    vol.Optional("list_components", default=False): cv.boolean,
    vol.Optional("force_translation", default=False): cv.boolean,
    vol.Optional("target_component", default=""): cv.string,
}

# Schema for blueprints translation service
BLUEPRINTS_TRANSLATION_SCHEMA = {
    **CONFIG_ENTRY_FIELD,
    vol.Optional("list_blueprints", default=False): cv.boolean,
    vol.Optional("target_blueprint", default=""): cv.string,
    vol.Optional("retranslate", default=False): cv.boolean,
}
