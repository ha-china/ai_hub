"""STT services for AI Hub - 语音转文字功能.

本模块提供语音识别服务，使用硅基流动 (SiliconFlow) SenseVoice API。

主要函数:
- handle_stt_transcribe: 处理语音转文字服务调用

特性:
- 自动语言检测，无需手动指定语言
- 支持中文、英文、日文、韩文等多种语言
- 支持的音频格式: WAV, MP3, FLAC, M4A, OGG, WebM
- 最大文件大小: 25MB
"""

from __future__ import annotations

import asyncio
import logging
import os

import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from ..consts import (
    DOMAIN,
    CONF_STT_FILE,
    DEFAULT_REQUEST_TIMEOUT,
    RECOMMENDED_STT_MODEL,
    SILICONFLOW_ASR_URL,
    SILICONFLOW_STT_AUDIO_FORMATS,
    SILICONFLOW_STT_MODELS,
    STT_MAX_FILE_SIZE_MB,
)
from ..helpers import translation_placeholders

_LOGGER = logging.getLogger(__name__)


async def handle_stt_transcribe(
    hass: HomeAssistant,
    call: ServiceCall,
    siliconflow_api_key: str,
    api_url: str = SILICONFLOW_ASR_URL,
) -> dict:
    """Handle Silicon Flow STT service call."""
    try:
        if not siliconflow_api_key or not siliconflow_api_key.strip():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="service_api_key_not_configured",
            )

        audio_file = call.data[CONF_STT_FILE]
        model = call.data.get("model", RECOMMENDED_STT_MODEL)

        if not audio_file or not audio_file.strip():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="stt_audio_file_required",
            )

        if model not in SILICONFLOW_STT_MODELS:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="stt_unsupported_model",
                translation_placeholders=translation_placeholders(model=model),
            )

        # 处理相对路径
        if not os.path.isabs(audio_file):
            audio_file = os.path.join(hass.config.config_dir, audio_file)

        if not await asyncio.to_thread(os.path.exists, audio_file):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="stt_audio_file_not_found",
                translation_placeholders=translation_placeholders(path=audio_file),
            )

        if await asyncio.to_thread(os.path.isdir, audio_file):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="path_is_directory",
                translation_placeholders=translation_placeholders(path=audio_file),
            )

        file_size = await asyncio.to_thread(os.path.getsize, audio_file)
        if file_size > STT_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="stt_file_too_large",
                translation_placeholders=translation_placeholders(max_size_mb=STT_MAX_FILE_SIZE_MB),
            )

        file_ext = os.path.splitext(audio_file)[1].lower().lstrip('.')
        if file_ext not in SILICONFLOW_STT_AUDIO_FORMATS:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="stt_unsupported_audio_format",
                translation_placeholders=translation_placeholders(
                    file_ext=file_ext,
                    supported_formats=", ".join(SILICONFLOW_STT_AUDIO_FORMATS),
                ),
            )

        audio_data = await asyncio.to_thread(_read_file_bytes, audio_file)

        headers = {"Authorization": f"Bearer {siliconflow_api_key}"}

        form_data = aiohttp.FormData()
        form_data.add_field(
            "file", audio_data,
            filename=os.path.basename(audio_file),
            content_type=f"audio/{file_ext}"
        )
        form_data.add_field("model", model)

        timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT / 1000)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(api_url, headers=headers, data=form_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("STT API error: %s - %s", response.status, error_text)
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="stt_api_request_failed",
                        translation_placeholders=translation_placeholders(status=response.status),
                    )

                response_data = await response.json()

                if "text" not in response_data:
                    _LOGGER.error("STT API response format error: %s", response_data)
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="stt_api_response_invalid",
                    )

                return {
                    "success": True,
                    "text": response_data["text"],
                    "model": model,
                    "audio_file": audio_file,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                }

    except ServiceValidationError as exc:
        _LOGGER.error("STT service validation error: %s", exc)
        raise
    except HomeAssistantError:
        raise
    except aiohttp.ClientError as exc:
        _LOGGER.error("STT service network error: %s", exc)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="stt_network_request_failed",
            translation_placeholders=translation_placeholders(error=exc),
        ) from exc
    except asyncio.TimeoutError:
        _LOGGER.error("STT service timeout")
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="stt_request_timeout",
        )
    except Exception as exc:
        _LOGGER.error("STT service error: %s", exc, exc_info=True)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="stt_transcription_failed",
            translation_placeholders=translation_placeholders(error=exc),
        ) from exc


def _read_file_bytes(path: str) -> bytes:
    """Read a binary file synchronously."""
    with open(path, "rb") as f:
        return f.read()
