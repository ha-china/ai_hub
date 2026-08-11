"""Image services for AI Hub - 图像分析和生成功能.

本模块提供图像相关的服务功能：
- 图像分析：使用 SiliconFlow 视觉模型分析图像内容
- 图像生成：使用 SiliconFlow 模型生成图像

主要函数:
- handle_analyze_image: 处理图像分析服务调用
- handle_generate_image: 处理图像生成服务调用
- load_image_from_file: 从文件加载图像
- load_image_from_camera: 从摄像头实体加载图像
- process_image: 处理和优化图像
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import time

import aiohttp
from homeassistant.components import camera
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from ..consts import (
    DEFAULT_IMAGE_SIZE,
    DOMAIN,
    ERROR_GETTING_RESPONSE,
    IMAGE_PROCESS_MAX_SIZE,
    IMAGE_PROCESS_QUALITY,
    RECOMMENDED_IMAGE_ANALYSIS_MODEL,
    RECOMMENDED_IMAGE_MODEL,
    TIMEOUT_CAMERA_IMAGE,
    TIMEOUT_CHAT_API,
    TIMEOUT_IMAGE_API,
)
from ..helpers import translation_placeholders
from .image_utils import extract_generated_image_payload

_LOGGER = logging.getLogger(__name__)


async def load_image_from_file(hass: HomeAssistant, image_file: str) -> bytes:
    """Load image from file path."""
    try:
        if not os.path.isabs(image_file):
            image_file = os.path.join(hass.config.config_dir, image_file)

        if not await asyncio.to_thread(os.path.exists, image_file):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_file_not_found",
                translation_placeholders=translation_placeholders(path=image_file),
            )

        if await asyncio.to_thread(os.path.isdir, image_file):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="path_is_directory",
                translation_placeholders=translation_placeholders(path=image_file),
            )

        return await asyncio.to_thread(_read_file_bytes, image_file)

    except IOError as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="image_file_read_failed",
            translation_placeholders=translation_placeholders(error=err),
        ) from err


def _read_file_bytes(path: str) -> bytes:
    """Read a binary file synchronously."""
    with open(path, "rb") as f:
        return f.read()


async def load_image_from_camera(hass: HomeAssistant, entity_id: str) -> bytes:
    """Load image from camera entity."""
    try:
        if not entity_id.startswith("camera."):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_invalid_camera_entity",
                translation_placeholders=translation_placeholders(entity_id=entity_id),
            )

        if not hass.states.get(entity_id):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_camera_not_found",
                translation_placeholders=translation_placeholders(entity_id=entity_id),
            )

        image = await camera.async_get_image(hass, entity_id, timeout=TIMEOUT_CAMERA_IMAGE)

        if not image or not image.content:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_camera_unavailable",
                translation_placeholders=translation_placeholders(entity_id=entity_id),
            )

        return image.content

    except (camera.CameraEntityImageError, TimeoutError) as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="image_camera_fetch_failed",
            translation_placeholders=translation_placeholders(error=err),
        ) from err


async def process_image(
    image_data: bytes,
    max_size: int = IMAGE_PROCESS_MAX_SIZE,
    quality: int = IMAGE_PROCESS_QUALITY,
) -> bytes:
    """Process image: resize and compress to optimize for API."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_data))

        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background

        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()

    except Exception as err:
        _LOGGER.warning("Failed to process image: %s, using original", err)
        return image_data


async def handle_stream_response(hass: HomeAssistant, response: aiohttp.ClientResponse) -> dict:
    """Handle streaming response from API."""
    event_id = f"siliconflow_image_analysis_{int(time.time())}"

    try:
        hass.bus.async_fire(f"{DOMAIN}_image_analysis_start", {"event_id": event_id})

        accumulated_text = ""
        async for line in response.content:
            if line:
                try:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        line_text = line_text[6:]

                    if line_text == '[DONE]':
                        break

                    if line_text:
                        json_data = json.loads(line_text)
                        if 'choices' in json_data and len(json_data['choices']) > 0:
                            content = json_data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                accumulated_text += content
                                hass.bus.async_fire(
                                    f"{DOMAIN}_image_analysis_token",
                                    {
                                        "event_id": event_id,
                                        "content": content,
                                        "full_content": accumulated_text
                                    }
                                )
                except json.JSONDecodeError:
                    continue

        return {
            "success": True,
            "content": accumulated_text,
            "stream_event_id": event_id,
        }

    except Exception as err:
        _LOGGER.error("Error handling stream response: %s", err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="image_stream_failed",
            translation_placeholders=translation_placeholders(error=err),
        ) from err


async def handle_analyze_image(
    hass: HomeAssistant,
    call: ServiceCall,
    api_key: str,
    chat_url: str
) -> dict:
    """Handle image analysis service call."""
    try:
        if not api_key or not api_key.strip():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_api_key_not_configured",
            )

        image_data = None

        if image_file := call.data.get("image_file"):
            image_data = await load_image_from_file(hass, image_file)
        elif image_entity := call.data.get("image_entity"):
            image_data = await load_image_from_camera(hass, image_entity)

        if not image_data:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="image_source_required",
            )

        processed_image_data = await process_image(image_data)
        base64_image = base64.b64encode(processed_image_data).decode()

        model = call.data.get("model", RECOMMENDED_IMAGE_ANALYSIS_MODEL)
        message = call.data["message"]
        stream = call.data.get("stream", False)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                        {"type": "text", "text": message}
                    ]
                }
            ]
        }

        if stream:
            payload["stream"] = True

        async with aiohttp.ClientSession() as session:
            async with session.post(
                chat_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_CHAT_API),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("API request failed: %s", error_text)
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="api_request_failed",
                        translation_placeholders=translation_placeholders(
                            error=f"{ERROR_GETTING_RESPONSE}: {error_text}"
                        ),
                    )

                if stream:
                    return await handle_stream_response(hass, response)
                else:
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    return {"success": True, "content": content, "model": model}

    except (ServiceValidationError, HomeAssistantError):
        raise
    except Exception as err:
        _LOGGER.error("Error analyzing image: %s", err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="image_analyze_failed",
            translation_placeholders=translation_placeholders(error=err),
        ) from err


async def handle_generate_image(
    hass: HomeAssistant,
    call: ServiceCall,
    api_key: str,
    image_url: str
) -> dict:
    """Handle image generation service call."""
    try:
        if not api_key or not api_key.strip():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_api_key_not_configured",
            )

        prompt = call.data["prompt"]
        size = call.data.get("size", DEFAULT_IMAGE_SIZE)
        model = call.data.get("model", RECOMMENDED_IMAGE_MODEL)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {"model": model, "prompt": prompt, "size": size}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                image_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_IMAGE_API),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("Image generation API request failed: %s", error_text)
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="api_request_failed",
                        translation_placeholders=translation_placeholders(
                            error=f"{ERROR_GETTING_RESPONSE}: {error_text}"
                        ),
                    )

                result = await response.json()
                image_payload = extract_generated_image_payload(result)
                return {
                    "success": True,
                    **image_payload,
                    "prompt": prompt,
                    "size": size,
                    "model": model,
                }

    except (ServiceValidationError, HomeAssistantError):
        raise
    except Exception as err:
        _LOGGER.error("Error generating image: %s", err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="image_generate_failed",
            translation_placeholders=translation_placeholders(error=err),
        ) from err
