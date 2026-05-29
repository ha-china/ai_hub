"""AI Task support for AI Hub."""

from __future__ import annotations

import io
import json
import logging

import aiohttp
from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .consts import (
    AI_HUB_CHAT_URL,
    AI_HUB_IMAGE_GEN_URL,
    CONF_CHAT_MODEL,
    CONF_CHAT_URL,
    CONF_IMAGE_MODEL,
    CONF_IMAGE_URL,
    ERROR_GETTING_RESPONSE,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_IMAGE_ANALYSIS_MODEL,
    RECOMMENDED_IMAGE_MODEL,
    SUBENTRY_AI_TASK,
    SUBENTRY_CONVERSATION,
    VISION_MODELS,
)
from .entity import AIHubBaseLLMEntity
from .http import build_json_headers, client_timeout
from .llm_model_utils import (
    chat_log_has_media_attachments,
    parse_structured_json_response,
    select_media_model,
)
from .services_lib.image_utils import decode_base64_image, extract_generated_image_payload
from .utils.serialization import ensure_string

_LOGGER = logging.getLogger(__name__)


def _get_conversation_model(config_entry: ConfigEntry) -> str:
    """Get the chat model from Conversation Agent subentry."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_CONVERSATION:
            return subentry.data.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL)
    return RECOMMENDED_CHAT_MODEL


def _get_conversation_chat_url(config_entry: ConfigEntry) -> str:
    """Get the chat URL from Conversation Agent subentry."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type == SUBENTRY_CONVERSATION:
            chat_url = subentry.data.get(CONF_CHAT_URL, AI_HUB_CHAT_URL)
            if isinstance(chat_url, str) and chat_url.strip():
                return chat_url
    return AI_HUB_CHAT_URL


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AI task entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_AI_TASK:
            continue

        async_add_entities(
            [AIHubTaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class AIHubTaskEntity(
    ai_task.AITaskEntity,
    AIHubBaseLLMEntity,
):
    """AI Hub AI Task entity."""

    def __init__(
        self, entry: ConfigEntry, subentry: ConfigSubentry
    ) -> None:
        """Initialize the entity."""
        # Get chat model from Conversation Agent subentry (AI Task follows Conversation's model)
        conversation_model = _get_conversation_model(entry)
        default_model = conversation_model
        super().__init__(entry, subentry, default_model)

        # Start with basic features
        self._attr_supported_features = (
            ai_task.AITaskEntityFeature.GENERATE_DATA
            | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
        )

        # Add image generation support if configured
        # Enable for: 1) Vision models, 2) Image generation models, 3) Recommended mode
        model = conversation_model
        is_recommended = subentry.data.get("recommended", False)

        from .consts import AI_HUB_IMAGE_MODELS

        if (
            model in VISION_MODELS
            or model in AI_HUB_IMAGE_MODELS
            or "-image" in model.lower()
            or "cogview" in model.lower()
            or is_recommended  # Always enable in recommended mode
        ):
            self._attr_supported_features |= ai_task.AITaskEntityFeature.GENERATE_IMAGE

    def _get_model_config(self, chat_log: conversation.ChatLog | None = None) -> dict[str, Any]:
        """AI Task follows Conversation model and chat URL settings."""
        model_config = super()._get_model_config(chat_log)
        chat_url = self.subentry.data.get(CONF_CHAT_URL)
        if not isinstance(chat_url, str) or not chat_url.strip():
            chat_url = _get_conversation_chat_url(self.entry)
        model_config[CONF_CHAT_URL] = chat_url
        return model_config

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task."""
        # Get model from Conversation Agent (AI Task follows Conversation's model)
        configured_model = _get_conversation_model(self.entry)

        final_model = configured_model
        if chat_log_has_media_attachments(chat_log):
            vision_models = [RECOMMENDED_IMAGE_ANALYSIS_MODEL]
            final_model = select_media_model(
                configured_model,
                vision_models,
                RECOMMENDED_IMAGE_ANALYSIS_MODEL,
            )
            if final_model != configured_model:
                _LOGGER.info(
                    "Auto-switched AI Task from %s to vision model %s for media attachments",
                    configured_model,
                    final_model,
                )

        _LOGGER.info("AI Task using final model: %s (configured: %s)", final_model, configured_model)

        # Process chat log with optional structure
        await self._async_handle_chat_log(chat_log, task.structure)

        # Ensure the last message is from assistant
        if not isinstance(chat_log.content[-1], conversation.AssistantContent):
            _LOGGER.error(
                "Last content in chat log is not an AssistantContent: %s. "
                "This could be due to the model not returning a valid response",
                chat_log.content[-1],
            )
            raise HomeAssistantError(ERROR_GETTING_RESPONSE)

        text = ensure_string(chat_log.content[-1].content)

        # If structure is requested, parse as JSON
        if task.structure:
            try:
                data = parse_structured_json_response(text)
            except json.JSONDecodeError as err:
                _LOGGER.error(
                    "Failed to parse JSON response: %s. Response: %s",
                    err,
                    text,
                )
                raise HomeAssistantError(ERROR_GETTING_RESPONSE) from err

            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=data,
            )

        # Otherwise return as text
        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=text,
        )

    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task."""
        options = self.subentry.data
        image_model = options.get(CONF_IMAGE_MODEL, RECOMMENDED_IMAGE_MODEL)

        # Get user prompt from chat log
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)

        # Build request parameters
        request_params = {
            "model": image_model,
            "prompt": user_message.content,
            "size": "1024x1024",  # Default size, AI Hub supports various sizes
        }

        _LOGGER.info("Generating image with model: %s, prompt: %s", image_model, user_message.content[:100])

        try:
            # Call AI Hub image generation API via HTTP
            headers = build_json_headers(self._api_key)

            # Get image URL from config (complete URL)
            image_url = options.get(CONF_IMAGE_URL, AI_HUB_IMAGE_GEN_URL)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    image_url,
                    json=request_params,
                    headers=headers,
                    timeout=client_timeout(120),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error("Image generation API failed: %s", error_text)
                        raise HomeAssistantError(f"Image generation failed: {error_text}")

                    result = await response.json()
                    _LOGGER.debug("Image generation response: %s", result)

                    image_payload = extract_generated_image_payload(result)
                    image_url = image_payload.get("url")
                    if image_url:
                        # Download image from URL
                        _LOGGER.info("Downloading image from URL: %s", image_url)
                        async with session.get(image_url) as img_response:
                            if img_response.status != 200:
                                raise HomeAssistantError(
                                    f"Failed to download image: {img_response.status}"
                                )

                            image_bytes = await img_response.read()
                            _LOGGER.info("Successfully downloaded image, size: %d bytes", len(image_bytes))
                    else:
                        _LOGGER.info("Using base64 image data")
                        image_bytes = decode_base64_image(image_payload["image_base64"])

            # Convert to PNG for better compatibility (requires Pillow, optional)
            try:
                from PIL import Image
            except ImportError:
                _LOGGER.debug("Pillow not available, using original image format")
                png_bytes = image_bytes
            else:
                try:
                    image = Image.open(io.BytesIO(image_bytes))

                    # Convert to RGB if needed
                    if image.mode in ("RGBA", "LA", "P"):
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        if image.mode == "P":
                            image = image.convert("RGBA")
                        if image.mode == "RGBA":
                            background.paste(image, mask=image.split()[-1])
                        else:
                            background.paste(image)
                        image = background

                    png_buffer = io.BytesIO()
                    image.save(png_buffer, format="PNG", optimize=True)
                    png_bytes = png_buffer.getvalue()
                    _LOGGER.info("Successfully converted image to PNG, size: %d bytes", len(png_bytes))

                except Exception as img_err:
                    _LOGGER.warning("Failed to convert image to PNG, using original: %s", img_err)
                    png_bytes = image_bytes

            # Add assistant content to chat log
            chat_log.async_add_assistant_content_without_tools(
                conversation.AssistantContent(
                    agent_id=self.entity_id,
                    content=f"Generated image using {image_model}",
                )
            )

            return ai_task.GenImageTaskResult(
                conversation_id=chat_log.conversation_id,
                image_data=png_bytes,
                mime_type="image/png",
                model=image_model,
            )

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error generating image: %s", err)
            raise HomeAssistantError(f"Network error: {err}") from err
        except Exception as err:
            _LOGGER.error("Error generating image: %s", err)
            raise HomeAssistantError(f"Error generating image: {err}") from err
