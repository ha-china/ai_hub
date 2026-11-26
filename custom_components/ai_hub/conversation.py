"""Conversation agent support for AI Hub integration.

This module implements the ConversationEntity for AI-powered
dialogue interactions, supporting:
- Streaming responses
- Tool calling (Home Assistant control)
- Image understanding (vision models)
- Context-aware conversations
- Three-tier intent processing (local → HA built-in → LLM)"""

from __future__ import annotations

from dataclasses import replace
import logging
from typing import Any, Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent, llm
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .consts import CONF_LLM_HASS_API, CONF_PROMPT, DOMAIN, LLM_API_ASSIST, SUBENTRY_CONVERSATION
from .entity import AIHubBaseLLMEntity
from .intents import get_config_cache

_LOGGER = logging.getLogger(__name__)

MATCH_ALL: Literal["*"] = "*"


def _is_speech_only_intent_script(
    hass: HomeAssistant, response: intent.IntentResponse
) -> bool:
    """Identify registered YAML intent scripts that do not run actions."""
    intent_type = getattr(getattr(response, "intent", None), "intent_type", None)
    if not intent_type:
        return False

    # Intent Script moved its handler in newer Home Assistant releases.
    try:
        from homeassistant.components.intent_script.helpers import ScriptIntentHandler
    except ImportError:
        try:
            from homeassistant.components.intent_script import ScriptIntentHandler
        except ImportError:
            return False

    for handler in intent.async_get(hass):
        if handler.intent_type == intent_type:
            return (
                type(handler) is ScriptIntentHandler
                and "speech" in handler.config
                and "action" not in handler.config
            )
    return False


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    _LOGGER.debug("Setting up conversation entities, subentries: %s", config_entry.subentries)

    conversation_subentries = [
        subentry
        for subentry in config_entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_CONVERSATION
    ]

    if not conversation_subentries:
        _LOGGER.debug("No conversation subentries found for entry: %s", config_entry.entry_id)
        return

    for subentry in conversation_subentries:
        _LOGGER.debug("Processing subentry: %s, type: %s", subentry.subentry_id, subentry.subentry_type)

        async_add_entities(
            [AIHubConversationAgent(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )
        _LOGGER.debug("Created conversation agent for subentry: %s", subentry.subentry_id)


class AIHubConversationAgent(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
    AIHubBaseLLMEntity,
):
    """AI Hub conversation agent."""

    _attr_supports_streaming = True

    def __init__(
        self,
        entry: ConfigEntry,
        subentry: ConfigSubentry,
        *,
        warn_on_missing_api_key: bool = True,
    ) -> None:
        """Initialize the agent."""
        from .consts import RECOMMENDED_CHAT_MODEL

        super().__init__(
            entry,
            subentry,
            RECOMMENDED_CHAT_MODEL,
            warn_on_missing_api_key=warn_on_missing_api_key,
        )

        # 初始化配置缓存
        self._config_cache = get_config_cache()

        if self.subentry.data.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a sentence and return a response.

        处理流程:
        1. 先交给 Home Assistant 处理内置 intents
        2. 如果 HA 没匹配，再回退到本地增强意图
        3. 最后交给 LLM
        """
        options = self.subentry.data

        local_or_builtin_result = await self._async_handle_local_and_builtin_intents(
            user_input,
            chat_log,
        )
        if local_or_builtin_result is not None:
            return local_or_builtin_result

        return await self._async_handle_llm_message(user_input, chat_log, options)

    async def _async_handle_local_and_builtin_intents(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult | None:
        """Run Home Assistant built-in intents first, then local fallback intents."""

        intent_handler = None
        try:
            from .intents import get_global_intent_handler
            intent_handler = get_global_intent_handler(self.hass)
        except Exception as e:
            _LOGGER.debug("Local intent handler initialization failed: %s", e)

        # ========== 步骤1: 尝试 HA 内置意图处理 ==========
        # timer、shopping list、设备控制、状态查询等 HA 原生支持的意图
        try:
            from homeassistant.components import conversation as ha_conversation

            ha_chat_log = replace(chat_log, content=chat_log.content.copy())

            _LOGGER.debug("调用 HA 内置 intents 处理: %s", user_input.text)
            ha_response = await ha_conversation.async_handle_intents(
                self.hass,
                user_input,
                ha_chat_log,
            )

            _LOGGER.debug("HA intents 返回结果: %s", ha_response)

            if ha_response is not None:
                response_type = ha_response.response_type
                _LOGGER.debug("HA intents response_type: %s", response_type)

                plain_speech = None
                if ha_response.speech and ha_response.speech.get("plain"):
                    plain_speech = ha_response.speech["plain"].get("speech")

                response_data = getattr(ha_response, "data", None) or {}
                has_error = hasattr(ha_response, "error") and ha_response.error
                is_error_type = response_type == intent.IntentResponseType.ERROR
                is_no_match = (
                    response_type == intent.IntentResponseType.NO_INTENT_MATCHED
                    if hasattr(intent.IntentResponseType, "NO_INTENT_MATCHED")
                    else False
                )
                response_has_content = bool(plain_speech)
                success_results = response_data.get("success") or getattr(ha_response, "success_results", []) or []
                failed_results = response_data.get("failed") or getattr(ha_response, "failed_results", []) or []
                has_explicit_success = bool(success_results)
                has_explicit_failure = bool(failed_results)
                has_explicit_outcome = has_explicit_success or has_explicit_failure
                continue_conversation = bool(getattr(ha_chat_log, "continue_conversation", False))
                # Speech-only intent_script handlers return ACTION_DONE even
                # though they execute no action and have no target outcomes.
                if (
                    response_type == intent.IntentResponseType.ACTION_DONE
                    and not has_explicit_outcome
                    and not has_error
                    and not getattr(ha_response, "error_code", None)
                    and isinstance(plain_speech, str)
                    and plain_speech.strip()
                    and not continue_conversation
                    and not getattr(ha_response, "reprompt", None)
                    and _is_speech_only_intent_script(self.hass, ha_response)
                ):
                    response_type = intent.IntentResponseType.QUERY_ANSWER
                    ha_response.response_type = response_type
                    _LOGGER.debug("Normalized speech-only intent_script as query answer")

                is_empty_action_done = (
                    response_type == intent.IntentResponseType.ACTION_DONE
                    and not has_explicit_outcome
                )
                is_follow_up_prompt = (
                    response_type == intent.IntentResponseType.QUERY_ANSWER
                    and continue_conversation
                    and not has_explicit_outcome
                )
                is_acceptable_type = (
                    (
                        response_type == intent.IntentResponseType.QUERY_ANSWER
                        and not is_follow_up_prompt
                    )
                    or (
                        response_type == intent.IntentResponseType.ACTION_DONE
                        and has_explicit_outcome
                    )
                )

                if (
                    not has_error
                    and not is_error_type
                    and not is_no_match
                    and response_has_content
                    and is_acceptable_type
                    and not is_empty_action_done
                ):
                    chat_log.content = ha_chat_log.content
                    if not isinstance(chat_log.content[-1], conversation.AssistantContent):
                        chat_log.async_add_assistant_content_without_tools(
                            conversation.AssistantContent(
                                agent_id=self.entity_id,
                                content=plain_speech,
                            )
                        )
                    _LOGGER.debug("Conversation result source: ha_builtin")
                    _LOGGER.info("HA 内置意图处理成功: %s, type: %s", user_input.text, response_type)
                    return conversation.ConversationResult(
                        response=ha_response,
                        conversation_id=chat_log.conversation_id,
                        continue_conversation=continue_conversation,
                    )

                if response_type == intent.IntentResponseType.QUERY_ANSWER and not has_explicit_outcome:
                    _LOGGER.debug(
                        "HA 内置意图已判定为查询类响应，跳过本地 fallback: %s",
                        user_input.text,
                    )
                    return None

                fallback_result = await self._async_try_local_intent_fallback(
                    user_input,
                    chat_log,
                    intent_handler,
                )
                if fallback_result is not None:
                    return fallback_result

                _LOGGER.debug(
                    "HA 内置意图未匹配、返回错误或结果异常("
                    "has_error=%s, is_error_type=%s, is_no_match=%s, "
                    "is_acceptable_type=%s, is_empty_action_done=%s, "
                    "continue_conversation=%s, is_follow_up_prompt=%s)，交给 LLM 处理",
                    has_error,
                    is_error_type,
                    is_no_match,
                    is_acceptable_type,
                    is_empty_action_done,
                    continue_conversation,
                    is_follow_up_prompt,
                )
            else:
                fallback_result = await self._async_try_local_intent_fallback(
                    user_input,
                    chat_log,
                    intent_handler,
                )
                if fallback_result is not None:
                    return fallback_result

        except Exception as e:
            _LOGGER.warning("HA 内置意图处理异常: %s", e, exc_info=True)

        return None

    async def _async_try_local_intent_fallback(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
        intent_handler: Any,
    ) -> conversation.ConversationResult | None:
        """Handle strictly sentence-matched local intents after HA built-in intents."""
        if intent_handler is None:
            return None

        matches_sentence_template = getattr(intent_handler, "matches_sentence_template", None)
        if not callable(matches_sentence_template) or not matches_sentence_template(user_input.text):
            return None

        _LOGGER.debug("Sentence-matched local intent processing: %s", user_input.text)
        intent_result = await intent_handler.handle(user_input.text, user_input.language)
        if not intent_result:
            return None

        speech = intent_result["response"].speech.get("plain", {}).get("speech")
        if speech:
            chat_log.async_add_assistant_content_without_tools(
                conversation.AssistantContent(
                    agent_id=self.entity_id,
                    content=speech,
                )
            )

        _LOGGER.debug("Conversation result source: ai_hub_local_sentence")
        return conversation.ConversationResult(
            response=intent_result["response"],
            conversation_id=chat_log.conversation_id,
        )

    async def _async_handle_llm_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
        options: dict[str, Any],
    ) -> conversation.ConversationResult:
        """Handle the remaining request via LLM."""

        try:
            # High-performance LLM API config retrieval
            llm_apis_value = options.get(CONF_LLM_HASS_API, [])
            if isinstance(llm_apis_value, str):
                llm_apis = [llm_apis_value] if llm_apis_value.strip() else []
            elif isinstance(llm_apis_value, (list, tuple, set)):
                llm_apis = [item for item in llm_apis_value if isinstance(item, str) and item.strip()]
            else:
                llm_apis = []

            valid_api_ids = {api.id for api in llm.async_get_apis(self.hass)}
            llm_apis = [api_id for api_id in llm_apis if api_id in valid_api_ids]

            if not llm_apis:
                _LOGGER.warning("LLM API config not found, checking LLM_API_ASSIST")
                # Try using the default LLM API ASSIST
                try:
                    default_llm_api = LLM_API_ASSIST
                    llm_apis = [default_llm_api]
                    _LOGGER.debug("Using default LLM API")
                except Exception as err:
                    _LOGGER.error("LLM_API_ASSIST retrieval failed: %s", err)
                    empty_response = intent.IntentResponse(language=user_input.language)
                    error_msg = self._config_cache.get_error_message("llm_config_error")
                    empty_response.async_set_speech(error_msg)
                    return conversation.ConversationResult(
                        response=empty_response,
                        conversation_id=user_input.conversation_id
                    )

            # Provide LLM data (tools, home info, etc.)
            user_prompt = options.get(CONF_PROMPT, "")
            _LOGGER.debug(
                "Preparing LLM data for '%s' with APIs=%s",
                user_input.text,
                llm_apis,
            )
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                llm_apis,
                user_prompt,
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            _LOGGER.error("LLM conversation error: %s", err)
            return err.as_conversation_result()

        # Loop until the provider has answered all pending tool results.
        while True:
            await self._async_handle_chat_log(chat_log)
            if not chat_log.unresponded_tool_results:
                break

        # Return result from chat log
        _LOGGER.debug("Conversation result source: llm")
        return conversation.async_get_result_from_chat_log(user_input, chat_log)
