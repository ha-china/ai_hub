"""Speech to Text support for AI Hub using Silicon Flow ASR."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from typing import Any

from homeassistant.components import stt
from homeassistant.components.stt import SpeechToTextEntity, SpeechResultState
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import aiohttp

from .const import (
    CONF_SILICONFLOW_API_KEY,
    SILICONFLOW_ASR_URL,
    SILICONFLOW_STT_MODELS,
    STT_DEFAULT_MODEL,
    DOMAIN,
)
from .entity import AIHubEntityBase
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STT entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "stt":
            continue

        async_add_entities(
            [AIHubSpeechToTextEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class AIHubSpeechToTextEntity(SpeechToTextEntity, AIHubEntityBase):
    """AI Hub speech-to-text entity using Silicon Flow ASR."""

    _attr_has_entity_name = True
    _attr_supported_options = ["model"]

    def __init__(self, config_entry: ConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the STT entity."""
        super().__init__(config_entry, subentry, STT_DEFAULT_MODEL)
        self._attr_available = True

        # Override device info for STT
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="老王杂谈说",
            model="Silicon Flow ASR",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

        # Get Silicon Flow API key
        self._api_key = config_entry.data.get(CONF_SILICONFLOW_API_KEY)

    @property
    def options(self) -> dict[str, Any]:
        """Return the options for this entity."""
        return self.subentry.data

    @property
    def default_options(self) -> dict[str, Any]:
        """Return default options."""
        return {
            "model": STT_DEFAULT_MODEL,
        }

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        # Silicon Flow ASR官方支持的格式：wav, mp3, pcm, opus, webm
        return ["zh-CN", "en-US"]

    @property
    def supported_formats(self) -> list[str]:
        """Return a list of supported audio formats."""
        # Silicon Flow ASR官方支持的格式：wav, mp3, pcm, opus, webm
        return ["wav", "mp3", "opus", "webm"]

    @property
    def supported_codecs(self) -> list[str]:
        """Return a list of supported audio codecs."""
        return ["pcm", "mp3", "wav", "flac", "aac", "ogg"]

    @property
    def supported_sample_rates(self) -> list[int]:
        """Return a list of supported sample rates."""
        return [8000, 11025, 16000, 22050, 44100, 48000]

    @property
    def supported_bit_rates(self) -> list[int]:
        """Return a list of supported bit rates."""
        return [8, 16, 24, 32, 64, 128, 256, 320]

    @property
    def supported_channels(self) -> list[int]:
        """Return a list of supported audio channels."""
        return [1, 2]

    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream
    ) -> stt.SpeechResult:
        """Process an audio stream and return the transcription result."""
        _LOGGER.info("=== 开始STT处理: format=%s, sample_rate=%d, channel=%d ===",
                     metadata.format, metadata.sample_rate, metadata.channel)

        if not self._api_key:
            _LOGGER.error("Silicon Flow API key not configured")
            raise HomeAssistantError(
                "Silicon Flow API key not configured. Please add the API key in the integration settings."
            )

        audio_data = b""
        chunk_count = 0
        async for chunk in stream:
            audio_data += chunk
            chunk_count += 1

        _LOGGER.debug("Audio data collected: chunks=%d, total_size=%d bytes", chunk_count, len(audio_data))

        # Quick check for empty or too small audio (optimized for voice assistant)
        # Voice assistant audio is typically 10-50KB for 3-5 seconds of speech
        if len(audio_data) < 1000:  # Less than 1KB
            _LOGGER.warning("Audio data too small: %d bytes, skipping STT", len(audio_data))
            return stt.SpeechResult("", SpeechResultState.ERROR)

        # For voice assistant scenario, warn if audio is too long which might cause timeouts
        # Typical voice assistant commands are 3-10 seconds
        max_voice_assistant_size = 500 * 1024  # 500KB should cover ~30 seconds of audio
        if len(audio_data) > max_voice_assistant_size:
            _LOGGER.warning("Voice assistant audio is quite large: %d bytes, this might cause delays", len(audio_data))

        try:
            model = self.options.get("model", STT_DEFAULT_MODEL)

            if model not in SILICONFLOW_STT_MODELS:
                raise HomeAssistantError(f"不支持的模型: {model}")

            # Convert raw PCM data to WAV format if needed
            # Check if audio data already has a WAV header
            if len(audio_data) < 12 or audio_data[:4] != b'RIFF':
                _LOGGER.info("Converting raw PCM data to WAV format")

                # Create WAV header for 16-bit PCM, mono, 16kHz
                sample_rate = metadata.sample_rate
                channels = metadata.channel
                bits_per_sample = metadata.bit_rate
                byte_rate = sample_rate * channels * bits_per_sample // 8
                block_align = channels * bits_per_sample // 8

                # WAV header structure
                wav_header = bytearray()
                # RIFF header
                wav_header.extend(b'RIFF')
                wav_header.extend((36 + len(audio_data)).to_bytes(4, 'little'))  # File size - 8
                wav_header.extend(b'WAVE')

                # fmt chunk
                wav_header.extend(b'fmt ')
                wav_header.extend((16).to_bytes(4, 'little'))  # Chunk size
                wav_header.extend((1).to_bytes(2, 'little'))   # Audio format (PCM = 1)
                wav_header.extend(channels.to_bytes(2, 'little'))  # Number of channels
                wav_header.extend(sample_rate.to_bytes(4, 'little'))  # Sample rate
                wav_header.extend(byte_rate.to_bytes(4, 'little'))    # Byte rate
                wav_header.extend(block_align.to_bytes(2, 'little'))  # Block align
                wav_header.extend(bits_per_sample.to_bytes(2, 'little'))  # Bits per sample

                # data chunk
                wav_header.extend(b'data')
                wav_header.extend(len(audio_data).to_bytes(4, 'little'))  # Data size

                # Combine header and audio data
                audio_data = bytes(wav_header) + audio_data
                _LOGGER.info("Created WAV header, new total size: %d bytes", len(audio_data))
            else:
                _LOGGER.info("Audio data already has WAV format")

            # Check file size (limit to 10MB for better reliability)
            max_size = 10 * 1024 * 1024  # 10MB
            if len(audio_data) > max_size:
                _LOGGER.error("音频文件过大: %d bytes (最大支持: %d bytes)", len(audio_data), max_size)
                raise HomeAssistantError(f"音频文件过大，请使用小于10MB的音频文件，或缩短录音时间")

            # Check if file format is supported
            supported_formats = ["wav", "mp3", "pcm", "opus", "webm"]
            if metadata.format.lower() not in supported_formats:
                _LOGGER.error("不支持的音频格式: %s (支持的格式: %s)", metadata.format, ", ".join(supported_formats))
                raise HomeAssistantError(f"不支持的音频格式: {metadata.format}。请使用以下格式: {', '.join(supported_formats)}")

            # Set headers exactly like the curl command - but let aiohttp handle Content-Type for multipart
            # aiohttp will automatically set the correct Content-Type with boundary
            headers = {
                "Authorization": f"Bearer {self._api_key}",
            }

            # Create multipart form data exactly like the working curl command
            # Replicate the curl: --form model=FunAudioLLM/SenseVoiceSmall --form file=@filename.mp3
            import io
            data = aiohttp.FormData()

            # Add model field exactly as in curl command
            data.add_field('model', model)

            # Add file field exactly as in curl command (--form file=@filename)
            # Since we converted to WAV format, always use WAV content-type
            content_type = 'audio/wav'
            filename = 'recording.wav'

            data.add_field('file', audio_data,
                         filename=filename,
                         content_type=content_type)

            # Very aggressive timeout for voice assistant - fail fast rather than hang
            timeout = aiohttp.ClientTimeout(
                total=8,     # Total timeout for voice assistant (8 seconds max)
                connect=3,   # Connect timeout (3 seconds)
                sock_read=5  # Socket read timeout (5 seconds) - very aggressive to avoid hanging
            )

            _LOGGER.info("Sending request to Silicon Flow ASR: model=%s, format=%s, size=%d bytes",
                        model, metadata.format, len(audio_data))

            # Log the actual request details for debugging
            _LOGGER.debug("Request details: URL=%s, headers=%s", SILICONFLOW_ASR_URL, headers)
            _LOGGER.debug("Request form fields: model=%s, file_size=%d bytes, filename=%s, content_type=%s",
                         model, len(audio_data), filename, content_type)

            # Debug: Log first few bytes of audio data to understand the actual format
            if len(audio_data) >= 8:
                header_bytes = audio_data[:8]
                _LOGGER.info("Audio data header: %s", header_bytes.hex())
                _LOGGER.info("Audio metadata from HA: format=%s, codec=%s, sample_rate=%d, bit_rate=%d",
                           metadata.format, metadata.codec, metadata.sample_rate, metadata.bit_rate)

                # Check if this is raw PCM data or has a container format
                if header_bytes[:4] == b'RIFF':
                    _LOGGER.info("Detected WAV container format")
                elif header_bytes[:4] == b'ftyp':
                    _LOGGER.info("Detected MP4/M4A container format")
                else:
                    _LOGGER.info("Appears to be raw audio data (likely PCM)")
                    # Log more of the header to understand the format
                    _LOGGER.debug("First 16 bytes: %s", audio_data[:16].hex())

            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    # Log the actual multipart data before sending
                    _LOGGER.debug("Multipart form data being sent:")
                    _LOGGER.debug("  - field: file, size: %d bytes, filename: audio.%s",
                                 len(audio_data), metadata.format)
                    _LOGGER.debug("  - field: model, value: %s", model)

                    _LOGGER.info("Starting HTTP POST request to %s", SILICONFLOW_ASR_URL)
                    async with session.post(
                        SILICONFLOW_ASR_URL,
                        headers=headers,
                        data=data
                    ) as response:
                        _LOGGER.info("HTTP response received: status=%d, content-type=%s",
                                     response.status, response.headers.get('content-type', 'unknown'))
                        if response.status != 200:
                            error_text = await response.text()
                            _LOGGER.error("HTTP错误: %s - %s", response.status, error_text)
                            raise HomeAssistantError(f"HTTP请求失败: {response.status}")

                        try:
                            _LOGGER.info("Waiting for JSON response from Silicon Flow API...")
                            response_data = await response.json()
                            _LOGGER.info("Silicon Flow ASR 响应成功: %s", response_data)
                        except Exception as e:
                            _LOGGER.error("解析Silicon Flow ASR响应失败: %s", e)
                            try:
                                response_text = await response.text()
                                _LOGGER.error("原始响应内容: %s", response_text[:500])  # 只显示前500字符
                            except Exception as text_error:
                                _LOGGER.error("无法获取原始响应文本: %s", text_error)
                            raise HomeAssistantError(f"解析响应失败: {e}") from e

                    # Log the full response structure for debugging
                    _LOGGER.info("响应结构分析: keys=%s", list(response_data.keys()) if isinstance(response_data, dict) else "不是字典")

                    # Try to extract transcribed text from various possible response formats
                    transcribed_text = None

                    # First check for direct OpenAI-style response (most likely)
                    if "text" in response_data:
                        transcribed_text = response_data["text"]
                        _LOGGER.info("从text字段提取文本: '%s'", transcribed_text)
                    elif "transcription" in response_data:
                        transcribed_text = response_data["transcription"]
                        _LOGGER.info("从transcription字段提取文本: '%s'", transcribed_text)

                    # Check for Silicon Flow API format: {"code": 20000, "message": "...", "data": {...}}
                    elif "code" in response_data:
                        code = response_data.get("code")
                        _LOGGER.info("API响应码: %s", code)

                        if code != 20000:
                            error_msg = response_data.get("message", "Unknown API error")
                            _LOGGER.error("Silicon Flow API错误: code=%s, message=%s", code, error_msg)
                            raise HomeAssistantError(f"API错误: {error_msg}")

                        # Success response, data contains the transcription
                        data = response_data.get("data")
                        _LOGGER.info("data字段内容: %s", data)

                        if data:
                            transcribed_text = data.get("text") or data.get("transcription")
                            _LOGGER.info("从data提取的文本: '%s'", transcribed_text)

                    # Check for result field
                    elif "result" in response_data:
                        result = response_data["result"]
                        _LOGGER.info("result字段内容: %s", result)
                        if isinstance(result, dict) and "text" in result:
                            transcribed_text = result["text"]
                        elif isinstance(result, str):
                            transcribed_text = result

                    # Last resort: look for any string field that might contain the transcription
                    if not transcribed_text and isinstance(response_data, dict):
                        _LOGGER.info("尝试查找可能的文本字段...")
                        for key, value in response_data.items():
                            if isinstance(value, str) and len(value.strip()) > 0 and key not in ["message", "msg"]:
                                _LOGGER.info("找到可能的文本字段 %s: '%s'", key, value)
                                transcribed_text = value
                                break

                    if not transcribed_text:
                        _LOGGER.error("无法从响应中提取转录文本: %s", response_data)
                        raise HomeAssistantError("API 响应格式错误，无法找到转录文本")

                    _LOGGER.info("=== STT识别成功: '%s' ===", transcribed_text)
                    _LOGGER.info("返回SpeechResult对象，格式检查...")

                    # Create SpeechResult object using the correct format like zhipuai
                    result = stt.SpeechResult(
                        transcribed_text.strip(),
                        stt.SpeechResultState.SUCCESS
                    )
                    _LOGGER.info("SpeechResult创建成功，text='%s'", result.text)
                    return result

            except asyncio.TimeoutError as exc:
                _LOGGER.error("Silicon Flow ASR 请求超时: %s", exc)
                # For voice assistant, provide a more helpful error message that suggests alternatives
                if "SocketTimeoutError" in str(exc) or "Timeout on reading data" in str(exc):
                    # This is likely a server-side delay, common with voice assistant scenarios
                    _LOGGER.warning("SiliconFlow服务器响应延迟，语音识别超时")
                    # Provide a more constructive error message for voice assistant users
                    raise HomeAssistantError("语音识别服务暂时繁忙，可以尝试：1. 再次说一遍 2. 检查网络连接 3. 稍后再试") from exc
                elif "Timeout on connect" in str(exc):
                    # Connection timeout - network issue
                    raise HomeAssistantError("无法连接到语音识别服务，请检查网络连接后重试") from exc
                else:
                    # General timeout
                    raise HomeAssistantError("语音识别超时，请再次尝试或检查网络") from exc
            except aiohttp.ClientConnectorError as exc:
                _LOGGER.error("Silicon Flow ASR 连接失败: %s", exc)
                raise HomeAssistantError("无法连接到Silicon Flow服务器，请检查网络连接") from exc
            except aiohttp.ClientError as exc:
                _LOGGER.error("Silicon Flow ASR 网络错误: %s", exc)
                raise HomeAssistantError("语音识别网络请求失败，请稍后重试") from exc
            except Exception as exc:
                _LOGGER.error("Silicon Flow ASR 转录失败: %s", exc, exc_info=True)
                raise HomeAssistantError(f"ASR 转录失败: {exc}") from exc

        except Exception as exc:
            _LOGGER.error("Silicon Flow ASR 转录失败: %s", exc, exc_info=True)
            _LOGGER.error("异常类型: %s", type(exc).__name__)
            _LOGGER.error("异常详情: %s", str(exc))
            raise HomeAssistantError(f"ASR 转录失败: {exc}") from exc