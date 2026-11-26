"""Regression tests for speech-only YAML intent routing."""

from dataclasses import dataclass, field
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("homeassistant")

from homeassistant.components import conversation
from homeassistant.helpers import intent

try:
    from homeassistant.components.intent_script.helpers import ScriptIntentHandler
except ImportError:
    from homeassistant.components.intent_script import ScriptIntentHandler

from custom_components.ai_hub.conversation import AIHubConversationAgent


@dataclass
class FakeChatLog:
    conversation_id: str = "speech-only-test"
    content: list = field(default_factory=lambda: [object()])
    continue_conversation: bool = False

    def async_add_assistant_content_without_tools(self, content):
        self.content.append(content)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind, speech, follow_up, reprompt, error, explicit, expected_local, expected_query",
    [
        ("speech", "15 lights", False, False, False, False, True, True),
        ("action", "Done", False, False, False, False, False, False),
        ("other", "Done", False, False, False, False, False, False),
        ("missing", "Done", False, False, False, False, False, False),
        ("no_intent", "Done", False, False, False, False, False, False),
        ("no_speech_config", "Done", False, False, False, False, False, False),
        ("speech", "", False, False, False, False, False, False),
        ("speech", "  ", False, False, False, False, False, False),
        ("speech", "Which light?", True, False, False, False, False, False),
        ("speech", "Which light?", False, True, False, False, False, False),
        ("speech", "Failed", False, False, True, False, False, False),
        ("action", "Done", False, False, False, True, True, False),
        ("no_match", "", False, False, False, False, False, False),
    ],
)
async def test_speech_only_intent_routing(
    monkeypatch, kind, speech, follow_up, reprompt, error, explicit,
    expected_local, expected_query,
):
    """Only speech-only scripts bypass the empty-action rejection."""
    intent_name = "TestLightQuery"
    # Older HA versions inspect intent.category in the constructor.
    response = intent.IntentResponse(language="zh-CN")
    if kind != "no_intent":
        response.intent = SimpleNamespace(intent_type=intent_name)
    response.async_set_speech(speech)
    if reprompt:
        response.async_set_reprompt("Please clarify")
    if error:
        response.async_set_error(intent.IntentResponseErrorCode.FAILED_TO_HANDLE, "Failed")
    if explicit:
        response.success_results = [
            intent.IntentResponseTarget(
                name="Light", type=intent.IntentResponseTargetType.ENTITY, id="light.test"
            )
        ]

    config = {} if kind == "no_speech_config" else {"speech": {}}
    if kind == "action":
        config["action"] = object()
    handlers = [] if kind == "missing" else [
        SimpleNamespace(intent_type=intent_name, config=config)
        if kind == "other" else ScriptIntentHandler(intent_name, config)
    ]
    monkeypatch.setattr(intent, "async_get", lambda hass: handlers)
    monkeypatch.setattr(
        conversation, "async_handle_intents",
        AsyncMock(return_value=None if kind == "no_match" else response),
    )
    monkeypatch.setattr(
        "custom_components.ai_hub.intents.get_global_intent_handler", lambda hass: None
    )

    agent = SimpleNamespace(
        hass=MagicMock(), entity_id="conversation.test",
        subentry=SimpleNamespace(data={}),
        _async_try_local_intent_fallback=AsyncMock(return_value=None),
        _async_handle_llm_message=AsyncMock(return_value="llm"),
    )
    agent._async_handle_local_and_builtin_intents = partial(
        AIHubConversationAgent._async_handle_local_and_builtin_intents, agent
    )
    result = await AIHubConversationAgent._async_handle_message(
        agent, SimpleNamespace(text="query", language="zh-CN"),
        FakeChatLog(continue_conversation=follow_up),
    )
    if expected_local:
        assert result.response is response
        agent._async_handle_llm_message.assert_not_awaited()
        agent._async_try_local_intent_fallback.assert_not_awaited()
        assert response.response_type is (
            intent.IntentResponseType.QUERY_ANSWER if expected_query
            else intent.IntentResponseType.ACTION_DONE
        )
    else:
        assert result == "llm"
        agent._async_handle_llm_message.assert_awaited_once()
        assert response.response_type is not intent.IntentResponseType.QUERY_ANSWER
