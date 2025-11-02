"""Services for AI Hub integration."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path

import aiohttp
import requests
import voluptuous as vol
from homeassistant.components import camera
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AI_HUB_CHAT_URL,
    AI_HUB_IMAGE_GEN_URL,
    AI_HUB_STT_AUDIO_FORMATS,
    AI_HUB_STT_MODELS,
    BEMFA_API_URL,
    CONF_API_KEY,
    CONF_BEMFA_UID,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_STT_FILE,
    CONF_TEMPERATURE,
    CONF_CUSTOM_COMPONENTS_PATH,
    DEFAULT_REQUEST_TIMEOUT,
    DOMAIN,
    EDGE_TTS_VOICES,
    ERROR_GETTING_RESPONSE,
    IMAGE_SIZES,
    RECOMMENDED_IMAGE_ANALYSIS_MODEL,
    RECOMMENDED_IMAGE_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_STT_MODEL,
    RECOMMENDED_TEMPERATURE,
    SERVICE_ANALYZE_IMAGE,
    SERVICE_GENERATE_IMAGE,
    SERVICE_STT_TRANSCRIBE,
    SERVICE_TTS_SPEECH,
    SERVICE_SEND_WECHAT_MESSAGE,
    SERVICE_TRANSLATE_COMPONENTS,
    SILICONFLOW_ASR_URL,
    STT_MAX_FILE_SIZE_MB,
    TTS_DEFAULT_PITCH,
    TTS_DEFAULT_RATE,
    TTS_DEFAULT_VOICE,
    TTS_DEFAULT_VOLUME,
)

_LOGGER = logging.getLogger(__name__)

# Schema for image analysis service
IMAGE_ANALYZER_SCHEMA = {
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
    vol.Required("prompt"): cv.string,
    vol.Optional("size", default="1024x1024"): vol.In(IMAGE_SIZES),
    vol.Optional("model", default=RECOMMENDED_IMAGE_MODEL): cv.string,
}

# Schema for Edge TTS service
TTS_SCHEMA = {
    vol.Required("text"): cv.string,
    vol.Optional("voice", default=TTS_DEFAULT_VOICE): vol.In(list(EDGE_TTS_VOICES.keys())),
    vol.Optional("rate", default=TTS_DEFAULT_RATE): cv.string,
    vol.Optional("volume", default=TTS_DEFAULT_VOLUME): cv.string,
    vol.Optional("pitch", default=TTS_DEFAULT_PITCH): cv.string,
    vol.Optional("media_player_entity"): cv.entity_id,
}

# Schema for Silicon Flow STT service
STT_SCHEMA = {
    vol.Required(CONF_STT_FILE): cv.string,
    vol.Optional("model", default=RECOMMENDED_STT_MODEL): vol.In(AI_HUB_STT_MODELS),
}

# Schema for Bemfa WeChat service
WECHAT_SCHEMA = {
    vol.Required("device_entity"): cv.entity_id,
    vol.Required("message"): cv.string,
    vol.Optional("group", default="default"): cv.string,
    vol.Optional("url", default=""): cv.string,
}

# Schema for translation service
TRANSLATION_SCHEMA = {
    vol.Optional("custom_components_path", default="custom_components"): cv.string,
}


async def async_setup_services(hass: HomeAssistant, config_entry) -> None:
    """Set up services for AI Hub integration."""

    api_key = config_entry.runtime_data
    bemfa_uid = config_entry.data.get(CONF_BEMFA_UID) if hasattr(config_entry, 'data') else None

    # Store bemfa_uid in config_entry for easy access
    if bemfa_uid:
        setattr(config_entry, 'bemfa_uid', bemfa_uid)

    # Function to check if we have required API keys for services
    def has_zhipu_api_key() -> bool:
        return api_key is not None and api_key.strip() != ""

    def has_bemfa_uid() -> bool:
        return bemfa_uid is not None and bemfa_uid.strip() != ""

    async def handle_analyze_image(call: ServiceCall) -> dict:
        """Handle image analysis service call."""
        try:
            if not has_zhipu_api_key():
                return {
                    "success": False,
                    "error": "智谱AI API密钥未配置，请先在集成配置中设置API密钥"
                }

            image_data = None

            # Get image from file
            if image_file := call.data.get("image_file"):
                image_data = await _load_image_from_file(hass, image_file)

            # Get image from camera entity
            elif image_entity := call.data.get("image_entity"):
                image_data = await _load_image_from_camera(hass, image_entity)

            if not image_data:
                raise ServiceValidationError("必须提供 image_file 或 image_entity 参数")

            # Resize and convert image to save bandwidth
            processed_image_data = await _process_image(image_data)
            base64_image = base64.b64encode(processed_image_data).decode()

            # Prepare API request
            model = call.data.get("model", RECOMMENDED_IMAGE_ANALYSIS_MODEL)
            message = call.data["message"]
            temperature = call.data.get("temperature", RECOMMENDED_TEMPERATURE)
            max_tokens = call.data.get("max_tokens", RECOMMENDED_MAX_TOKENS)
            stream = call.data.get("stream", False)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Try exact format from AI Hub official documentation
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": message
                            }
                        ]
                    }
                ]
            }

            # Only add non-problematic parameters
            if stream:
                payload["stream"] = True

            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    AI_HUB_CHAT_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error("API request failed: %s", error_text)
                        raise HomeAssistantError(f"{ERROR_GETTING_RESPONSE}: {error_text}")

                    if stream:
                        return await _handle_stream_response(hass, response)
                    else:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        return {
                            "success": True,
                            "content": content,
                            "model": model,
                        }

        except Exception as err:
            _LOGGER.error("Error analyzing image: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def handle_generate_image(call: ServiceCall) -> dict:
        """Handle image generation service call."""
        try:
            if not has_zhipu_api_key():
                return {
                    "success": False,
                    "error": "智谱AI API密钥未配置，请先在集成配置中设置API密钥"
                }
            prompt = call.data["prompt"]
            size = call.data.get("size", "1024x1024")
            model = call.data.get("model", RECOMMENDED_IMAGE_MODEL)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
            }

            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    AI_HUB_IMAGE_GEN_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),  # Image generation takes longer
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error("Image generation API request failed: %s", error_text)
                        raise HomeAssistantError(f"{ERROR_GETTING_RESPONSE}: {error_text}")

                    result = await response.json()

                    # Process the response based on AI Hub's actual API response format
                    if "data" in result and len(result["data"]) > 0:
                        image_data = result["data"][0]
                        image_url = image_data.get("url", "")
                        if image_url:
                            return {
                                "success": True,
                                "image_url": image_url,
                                "prompt": prompt,
                                "size": size,
                                "model": model,
                            }
                        else:
                            # If base64 image is returned instead of URL
                            b64_json = image_data.get("b64_json", "")
                            if b64_json:
                                return {
                                    "success": True,
                                    "image_base64": b64_json,
                                    "prompt": prompt,
                                    "size": size,
                                    "model": model,
                                }

                    raise HomeAssistantError("无法获取生成的图像")

        except Exception as err:
            _LOGGER.error("Error generating image: %s", err)
            return {
                "success": False,
                "error": str(err)
            }

    async def handle_tts_speech(call: ServiceCall) -> dict:
        """Handle TTS service call."""
        try:
            if not has_zhipu_api_key():
                return {
                    "success": False,
                    "error": "智谱AI API密钥未配置，请先在集成配置中设置API密钥"
                }
            text = call.data["text"]
            voice = call.data.get("voice", TTS_DEFAULT_VOICE)
            speed = float(call.data.get("speed", TTS_DEFAULT_VOLUME))
            volume = float(call.data.get("volume", TTS_DEFAULT_VOLUME))
            response_format = call.data.get("response_format", TTS_DEFAULT_RATE)
            encode_format = call.data.get("encode_format", TTS_DEFAULT_VOICE)
            stream = call.data.get("stream", TTS_DEFAULT_PITCH)
            media_player_entity = call.data.get("media_player_entity")

            # 验证参数
            if not text or not text.strip():
                raise ServiceValidationError("文本内容不能为空")

            if voice not in EDGE_TTS_VOICES:
                raise ServiceValidationError(f"不支持的语音类型: {voice}")

            if response_format not in TTS_DEFAULT_RATE:
                raise ServiceValidationError(f"不支持的响应格式: {response_format}")

            if encode_format not in TTS_DEFAULT_VOICE:
                raise ServiceValidationError(f"不支持的编码格式: {encode_format}")

            if not 0.25 <= speed <= 4.0:
                raise ServiceValidationError("语速必须在 0.25 到 4.0 之间")

            if not 0.1 <= volume <= 2.0:
                raise ServiceValidationError("音量必须在 0.1 到 2.0 之间")

            # 构建 TTS API 请求
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "cogtts",
                "input": text,
                "voice": voice,
                "response_format": response_format,
                "encode_format": encode_format,
                "stream": stream,
                "speed": speed,
                "volume": volume,
            }

            timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT / 1000)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    EDGE_TTS_VOICES,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "智谱AI TTS API 错误: %s - %s",
                            response.status,
                            error_text
                        )
                        return {
                            "success": False,
                            "error": f"TTS API 请求失败: {response.status}"
                        }

                    if stream:
                        # 处理流式响应
                        response_text = await response.text()
                        from .helpers import parse_streaming_response, combine_audio_chunks

                        audio_chunks = parse_streaming_response(response_text)

                        if not audio_chunks:
                            return {"success": False, "error": "未从流式响应中获取到音频数据"}

                        # 合并音频块
                        combined_audio = audio_chunks[0]  # 对于 TTS，通常第一个块就包含完整数据

                        # 如果有多个块，尝试合并
                        if len(audio_chunks) > 1:
                            try:
                                combined_audio = combine_audio_chunks(audio_chunks)
                            except Exception as exc:
                                _LOGGER.warning("音频合并失败，使用第一个音频块: %s", exc)

                        audio_base64 = combined_audio
                    else:
                        # 处理非流式响应
                        response_data = await response.json()

                        if "choices" not in response_data or not response_data["choices"]:
                            return {"success": False, "error": "API 响应格式错误"}

                        # 从非流式响应中提取音频数据
                        choice = response_data["choices"][0]
                        if "audio" in choice:
                            audio_base64 = choice["audio"]["content"]
                        elif "message" in choice and "content" in choice["message"]:
                            audio_base64 = choice["message"]["content"]
                        else:
                            return {"success": False, "error": "无法从响应中提取音频数据"}

                    # 解码音频为 WAV 格式
                    from .helpers import decode_base64_audio
                    wav_audio_data = decode_base64_audio(audio_base64)

                    # 如果指定了媒体播放器实体，直接播放
                    if media_player_entity:
                        try:
                            # 将音频数据保存为临时文件
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                                temp_file.write(wav_audio_data)
                                temp_file_path = temp_file.name

                            # 调用媒体播放器的播放服务
                            await hass.services.async_call(
                                "media_player",
                                "play_media",
                                {
                                    "entity_id": media_player_entity,
                                    "media_content_id": f"file://{temp_file_path}",
                                    "media_content_type": "audio/wav",
                                },
                                blocking=True,
                            )

                            # 延迟删除临时文件
                            await asyncio.sleep(1)
                            try:
                                os.unlink(temp_file_path)
                            except OSError:
                                pass  # 文件可能已被系统删除

                            return {
                                "success": True,
                                "message": "语音播放成功",
                                "media_player": media_player_entity,
                            }

                        except Exception as exc:
                            _LOGGER.error("媒体播放失败: %s", exc)
                            return {
                                "success": False,
                                "error": f"媒体播放失败: {exc}",
                                "audio_data": audio_base64,
                            }

                    # 返回音频数据供其他用途
                    return {
                        "success": True,
                        "audio_data": audio_base64,
                        "audio_format": "wav",
                        "voice": voice,
                        "speed": speed,
                        "volume": volume,
                    }

        except ServiceValidationError as exc:
            _LOGGER.error("TTS service validation error: %s", exc)
            return {"success": False, "error": str(exc)}
        except aiohttp.ClientError as exc:
            _LOGGER.error("TTS service network error: %s", exc)
            return {"success": False, "error": f"网络请求失败: {exc}"}
        except asyncio.TimeoutError as exc:
            _LOGGER.error("TTS service timeout: %s", exc)
            return {"success": False, "error": "请求超时"}
        except Exception as exc:
            _LOGGER.error("TTS service error: %s", exc, exc_info=True)
            return {"success": False, "error": f"TTS 生成失败: {exc}"}

    async def handle_stt_transcribe(call: ServiceCall) -> dict:
        """Handle Silicon Flow STT service call."""
        try:
            # Check if Silicon Flow API key is configured
            siliconflow_api_key = getattr(config_entry, 'data', {}).get(CONF_SILICONFLOW_API_KEY) if hasattr(config_entry, 'data') else None
            if not siliconflow_api_key or not siliconflow_api_key.strip():
                return {
                    "success": False,
                    "error": "Silicon Flow API密钥未配置，请先在集成配置中设置"
                }
            audio_file = call.data[CONF_STT_FILE]
            model = call.data.get("model", RECOMMENDED_STT_MODEL)

            # 验证参数
            if not audio_file or not audio_file.strip():
                raise ServiceValidationError("音频文件路径不能为空")

            if model not in AI_HUB_STT_MODELS:
                raise ServiceValidationError(f"不支持的模型: {model}")

            # 加载音频文件
            try:
                # 处理相对路径
                if not os.path.isabs(audio_file):
                    audio_file = os.path.join(hass.config.config_dir, audio_file)

                if not os.path.exists(audio_file):
                    raise ServiceValidationError(f"音频文件不存在: {audio_file}")

                if os.path.isdir(audio_file):
                    raise ServiceValidationError(f"提供的路径是一个目录: {audio_file}")

                # 检查文件大小
                file_size = os.path.getsize(audio_file)
                if file_size > STT_MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise ServiceValidationError(f"音频文件过大，最大支持 {STT_MAX_FILE_SIZE_MB}MB")

                # 检查文件格式
                file_ext = os.path.splitext(audio_file)[1].lower().lstrip('.')
                if file_ext not in SILICONFLOW_STT_AUDIO_FORMATS:
                    raise ServiceValidationError(f"不支持的音频格式: {file_ext}，支持的格式: {', '.join(SILICONFLOW_STT_AUDIO_FORMATS)}")

                # 读取音频文件
                with open(audio_file, "rb") as f:
                    audio_data = f.read()

            except IOError as err:
                raise ServiceValidationError(f"读取音频文件失败: {err}")

            # 构建 STT API 请求
            headers = {
                "Authorization": f"Bearer {siliconflow_api_key}",
            }

            # 准备文件上传
            form_data = aiohttp.FormData()
            form_data.add_field(
                "file",
                audio_data,
                filename=os.path.basename(audio_file),
                content_type=f"audio/{file_ext}"
            )
            form_data.add_field("model", model)

            timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT / 1000)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    SILICONFLOW_ASR_URL,
                    headers=headers,
                    data=form_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "智谱AI STT API 错误: %s - %s",
                            response.status,
                            error_text
                        )
                        return {
                            "success": False,
                            "error": f"STT API 请求失败: {response.status}"
                        }

                    if stream:
                        # 处理流式响应
                        full_text = ""
                        async for line in response.content:
                            if line:
                                line_text = line.decode('utf-8').strip()
                                if line_text.startswith('data: '):
                                    try:
                                        data_str = line_text[6:]  # Remove 'data: ' prefix
                                        data_dict = json.loads(data_str)

                                        if "text" in data_dict:
                                            full_text += data_dict["text"]
                                    except (json.JSONDecodeError, KeyError) as exc:
                                        _LOGGER.warning("解析流式响应失败: %s", exc)
                                        continue

                        transcribed_text = full_text.strip()
                    else:
                        # 处理非流式响应
                        response_data = await response.json()

                        if "text" not in response_data:
                            _LOGGER.error("STT API 响应格式错误: %s", response_data)
                            return {"success": False, "error": "API 响应格式错误"}

                        transcribed_text = response_data["text"]

                    return {
                        "success": True,
                        "text": transcribed_text,
                        "model": model,
                        "language": language,
                        "audio_file": audio_file,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                    }

        except ServiceValidationError as exc:
            _LOGGER.error("STT service validation error: %s", exc)
            return {"success": False, "error": str(exc)}
        except aiohttp.ClientError as exc:
            _LOGGER.error("STT service network error: %s", exc)
            return {"success": False, "error": f"网络请求失败: {exc}"}
        except asyncio.TimeoutError as exc:
            _LOGGER.error("STT service timeout: %s", exc)
            return {"success": False, "error": "请求超时"}
        except Exception as exc:
            _LOGGER.error("STT service error: %s", exc, exc_info=True)
            return {"success": False, "error": f"STT 转录失败: {exc}"}

    async def handle_send_wechat_message(call: ServiceCall) -> dict:
        """Handle Bemfa WeChat message service call."""
        try:
            # Get Bemfa UID from config entry or service data
            bemfa_uid = getattr(config_entry, 'bemfa_uid', None) or call.data.get("bemfa_uid")

            if not bemfa_uid or not bemfa_uid.strip():
                return {
                    "success": False,
                    "error": "Bemfa UID 未配置，请在集成配置中设置或通过服务参数提供"
                }

            device_entity = call.data["device_entity"]
            message = call.data["message"].strip()
            group = call.data.get("group", "default")
            url = call.data.get("url", "")

            if not device_entity or not message:
                return {
                    "success": False,
                    "error": "device_entity 和 message 参数必填"
                }

            # Get entity state
            state_obj = hass.states.get(device_entity)
            if state_obj:
                friendly_name = state_obj.attributes.get("friendly_name", device_entity)
                state_value = state_obj.state
            else:
                friendly_name = device_entity
                state_value = "无实体状态"

            final_message = f"{friendly_name}（状态：{state_value}）: {message}"
            _LOGGER.debug("最终发送微信消息内容：%s", final_message)

            payload = {
                "uid": bemfa_uid,
                "device": device_entity.replace(".", "_"),
                "message": final_message,
                "group": group,
                "url": url,
            }

            headers = {"Content-Type": "application/json; charset=utf-8"}

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    BEMFA_API_URL,
                    json=payload,
                    headers=headers
                ) as response:
                    resp_text = await response.text()
                    if response.status == 200:
                        _LOGGER.info("微信消息发送成功")
                        return {
                            "success": True,
                            "message": "微信消息发送成功",
                            "device": device_entity,
                            "group": group
                        }
                    else:
                        _LOGGER.error("发送失败 [%s]: %s", response.status, resp_text)
                        return {
                            "success": False,
                            "error": f"发送失败 [{response.status}]: {resp_text}"
                        }

        except aiohttp.ClientError as exc:
            _LOGGER.error("网络请求错误: %s", exc)
            return {"success": False, "error": f"网络请求错误: {exc}"}
        except Exception as exc:
            _LOGGER.exception("发送微信消息异常: %s", exc)
            return {"success": False, "error": f"发送微信消息异常: {exc}"}

    async def handle_translate_components(call: ServiceCall) -> dict:
        """Handle translation service call."""
        try:
            # Get parameters
            custom_components_path = call.data.get("custom_components_path", "custom_components")

            # Check if Zhipu API key is available
            if not has_zhipu_api_key():
                return {
                    "success": False,
                    "error": "智谱AI API密钥未配置，请先配置AI Hub集成"
                }

            _LOGGER.info("开始组件翻译...")

            # Run translation in background thread
            result = await hass.async_add_executor_job(
                translate_all_components,
                custom_components_path,
                api_key
            )

            return {
                "success": True,
                "result": result
            }

        except Exception as exc:
            _LOGGER.error("翻译服务错误: %s", exc)
            return {
                "success": False,
                "error": f"翻译服务错误: {exc}"
            }

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_ANALYZE_IMAGE,
        handle_analyze_image,
        schema=vol.Schema(IMAGE_ANALYZER_SCHEMA),
        supports_response=True
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_IMAGE,
        handle_generate_image,
        schema=vol.Schema(IMAGE_GENERATOR_SCHEMA),
        supports_response=True
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TTS_SPEECH,
        handle_tts_speech,
        schema=vol.Schema(TTS_SCHEMA),
        supports_response=True
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STT_TRANSCRIBE,
        handle_stt_transcribe,
        schema=vol.Schema(STT_SCHEMA),
        supports_response=True
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_WECHAT_MESSAGE,
        handle_send_wechat_message,
        schema=vol.Schema(WECHAT_SCHEMA),
        supports_response=True
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSLATE_COMPONENTS,
        handle_translate_components,
        schema=vol.Schema(TRANSLATION_SCHEMA),
        supports_response=True
    )


async def _load_image_from_file(hass: HomeAssistant, image_file: str) -> bytes:
    """Load image from file path."""
    try:
        # Handle relative paths
        if not os.path.isabs(image_file):
            image_file = os.path.join(hass.config.config_dir, image_file)

        if not os.path.exists(image_file):
            raise ServiceValidationError(f"图像文件不存在: {image_file}")

        if os.path.isdir(image_file):
            raise ServiceValidationError(f"提供的路径是一个目录: {image_file}")

        with open(image_file, "rb") as f:
            return f.read()

    except IOError as err:
        raise ServiceValidationError(f"读取图像文件失败: {err}")


async def _load_image_from_camera(hass: HomeAssistant, entity_id: str) -> bytes:
    """Load image from camera entity."""
    try:
        if not entity_id.startswith("camera."):
            raise ServiceValidationError(f"无效的摄像头实体ID: {entity_id}")

        if not hass.states.get(entity_id):
            raise ServiceValidationError(f"摄像头实体不存在: {entity_id}")

        # Get image from camera
        image = await camera.async_get_image(hass, entity_id, timeout=10)

        if not image or not image.content:
            raise ServiceValidationError(f"无法从摄像头获取图像: {entity_id}")

        return image.content

    except (camera.CameraEntityImageError, TimeoutError) as err:
        raise ServiceValidationError(f"获取摄像头图像失败: {err}")


async def _process_image(image_data: bytes, max_size: int = 1024, quality: int = 85) -> bytes:
    """Process image: resize and compress to optimize for API."""
    try:
        # Open image
        from PIL import Image
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            else:
                background.paste(img)
            img = background

        # Resize if too large
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Compress to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()

    except Exception as err:
        _LOGGER.warning("Failed to process image: %s, using original", err)
        return image_data


async def _handle_stream_response(hass: HomeAssistant, response: aiohttp.ClientResponse) -> dict:
    """Handle streaming response from API."""
    event_id = f"zhipuai_image_analysis_{int(time.time())}"

    try:
        hass.bus.async_fire(f"{DOMAIN}_image_analysis_start", {"event_id": event_id})

        accumulated_text = ""
        async for line in response.content:
            if line:
                try:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        line_text = line_text[6:]  # Remove 'data: ' prefix

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
        return {
            "success": False,
            "error": str(err)
        }


# Translation functionality (adapted from translation_localizer)
def translate_all_components(custom_components_path: str, api_key: str) -> dict:
    """Translate all components in the custom_components directory."""
    # Find the custom components directory
    base_path = None

    # Try common paths
    paths_to_try = [
        Path(custom_components_path),
        Path("/config") / custom_components_path,
        Path.home() / ".homeassistant" / custom_components_path,
    ]

    for path in paths_to_try:
        if path.exists() and path.is_dir():
            base_path = path
            break

    if not base_path:
        return {
            "translated": 0,
            "skipped": 0,
            "error": f"Custom components directory not found: {custom_components_path}"
        }

    _LOGGER.info(f"Scanning components in: {base_path}")

    translated = 0
    skipped = 0

    # Process each component directory
    for component_dir in base_path.iterdir():
        if not component_dir.is_dir() or component_dir.name in ["ai_hub", "translation_localizer"]:
            continue

        try:
            result = translate_component(component_dir, api_key)
            if result == "translated":
                translated += 1
            else:
                skipped += 1
        except Exception as e:
            _LOGGER.error(f"Error processing {component_dir.name}: {e}")

    return {
        "translated": translated,
        "skipped": skipped,
        "total": translated + skipped
    }


def translate_component(component_dir: Path, api_key: str) -> str:
    """Translate a single component."""
    translations_dir = component_dir / "translations"
    en_file = translations_dir / "en.json"
    zh_file = translations_dir / "zh-Hans.json"

    # Check if translation is needed
    if not translations_dir.exists() or not en_file.exists():
        return "skipped"

    if zh_file.exists():
        return "skipped"

    _LOGGER.info(f"Translating {component_dir.name}")

    try:
        # Load English translations
        with open(en_file, 'r', encoding='utf-8') as f:
            en_data = json.load(f)

        # Translate the data
        zh_data = translate_json_values(en_data, api_key)

        # Save Chinese translations
        with open(zh_file, 'w', encoding='utf-8') as f:
            json.dump(zh_data, f, ensure_ascii=False, indent=2)

        _LOGGER.info(f"Successfully translated {component_dir.name}")
        return "translated"

    except Exception as e:
        _LOGGER.error(f"Failed to translate {component_dir.name}: {e}")
        return "error"


def translate_json_values(data: any, api_key: str) -> any:
    """Recursively translate JSON values."""
    if isinstance(data, dict):
        return {key: translate_json_values(value, api_key) for key, value in data.items()}
    elif isinstance(data, list):
        return [translate_json_values(item, api_key) for item in data]
    elif isinstance(data, str) and data.strip():
        # Translate strings
        return translate_text(data, api_key)
    else:
        return data


def translate_text(text: str, api_key: str) -> str:
    """Translate text using Zhipu AI while preserving placeholders."""
    if not text or len(text.strip()) < 2:
        return text

    # Skip placeholders and code - use regex to find placeholder patterns
    # Pattern to match {placeholder}, %placeholder, ${placeholder}, etc.
    placeholder_pattern = r'\{[^}]+\}|%\w+|\$\{[^}]+\}'

    # Check if text is primarily a placeholder
    if re.fullmatch(placeholder_pattern, text.strip()):
        return text

    # Check if text starts with placeholder patterns
    if text.startswith(("{", "%", "${")) or text.isupper():
        return text

    # Find all placeholders in the text
    placeholders = re.findall(placeholder_pattern, text)

    if not placeholders:
        # No placeholders, translate directly
        return _translate_simple_text(text, api_key)

    # Extract placeholders and replace them with temporary markers
    placeholder_map = {}
    temp_text = text
    for i, placeholder in enumerate(placeholders):
        marker = f"__PLACEHOLDER_{i}__"
        placeholder_map[marker] = placeholder
        temp_text = temp_text.replace(placeholder, marker, 1)

    # Translate the text with placeholders removed
    translated_temp = _translate_simple_text(temp_text, api_key)

    # Restore the original placeholders
    translated_text = translated_temp
    for marker, placeholder in placeholder_map.items():
        translated_text = translated_text.replace(marker, placeholder)

    return translated_text


def _translate_simple_text(text: str, api_key: str) -> str:
    """Simple translation function for text without placeholders."""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-4-flash-250414",
        "messages": [
            {
                "role": "system",
                "content": "Translate English to Chinese. Return only the translation, no explanation."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        translated = result["choices"][0]["message"]["content"].strip()

        _LOGGER.debug(f"Translated: {text} -> {translated}")
        return translated

    except Exception as e:
        _LOGGER.error(f"Translation failed for '{text}': {e}")
        return text  # Return original on failure