"""Regression tests for speech-only YAML intent routing."""

from dataclasses import dataclass, field
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock

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
    "kind, speech, follow_up, reprompt, error, explicit, expected_local, expected_query, registry_change",
    [
        ("speech", "15 lights", False, False, False, False, True, True, None),
        ("action", "Done", False, False, False, False, False, False, None),
        ("other", "Done", False, False, False, False, False, False, None),
        ("missing", "Done", False, False, False, False, False, False, None),
        ("no_intent", "Done", False, False, False, False, False, False, None),
        ("no_speech_config", "Done", False, False, False, False, False, False, None),
        ("speech", "", False, False, False, False, False, False, None),
        ("speech", "  ", False, False, False, False, False, False, None),
        ("speech", "Which light?", True, False, False, False, False, False, None),
        ("speech", "Which light?", False, True, False, False, False, False, None),
        ("speech", "Failed", False, False, True, False, False, False, None),
        ("action", "Done", False, False, False, True, True, False, None),
        ("no_match", "", False, False, False, False, False, False, None),
        ("speech", "15 lights", False, False, False, False, False, False, "remove"),
        ("speech", "15 lights", False, False, False, False, False, False, "speech"),
        ("action", "Done", False, False, False, False, False, False, "speech"),
        ("speech", "15 lights", False, False, False, False, False, False, "action"),
        ("speech", "15 lights", False, False, False, False, True, True, "unrelated"),
        ("missing", "Done", False, False, False, False, False, False, "speech"),
        ("speech", "15 lights", False, False, False, False, False, False, "mutate"),
        ("action", "Failed", False, False, False, "failed", True, False, None),
    ],
)
async def test_speech_only_intent_routing(
    monkeypatch, kind, speech, follow_up, reprompt, error, explicit,
    expected_local, expected_query, registry_change,
):
    """Exercise the real HA registry and ensure only unchanged speech scripts qualify."""
    intent_name = "TestLightQuery"
    # Use the real registry helpers with isolated HA data; do not mock async_get.
    hass = SimpleNamespace(data={})
    response = intent.IntentResponse(language="zh-CN")
    if kind != "no_intent":
        response.intent = SimpleNamespace(intent_type=intent_name)
    response.async_set_speech(speech)
    if reprompt:
        response.async_set_reprompt("Please clarify")
    if error:
        response.async_set_error(intent.IntentResponseErrorCode.FAILED_TO_HANDLE, "Failed")
    if explicit:
        targets = [
            intent.IntentResponseTarget(
                name="Light", type=intent.IntentResponseTargetType.ENTITY, id="light.test"
            )
        ]
        if explicit == "failed":
            response.failed_results = targets
        else:
            response.success_results = targets

    config = {} if kind == "no_speech_config" else {"speech": {}}
    if kind == "action":
        config["action"] = object()
    handler = (
        SimpleNamespace(intent_type=intent_name, config=config)
        if kind == "other" else ScriptIntentHandler(intent_name, config)
    )
    if kind != "missing":
        intent.async_register(hass, handler)
        assert list(intent.async_get(hass)) == [handler]
    else:
        assert list(intent.async_get(hass)) == []
    intent.async_register(hass, ScriptIntentHandler("OtherQuery", {"speech": {}}))

    async def handle_intents(*args, **kwargs):
        # Model registry changes while HA processes the request, before it returns.
        if registry_change == "remove":
            intent.async_remove(hass, intent_name)
        elif registry_change in ("speech", "action"):
            intent.async_remove(hass, intent_name)
            new_config = {"speech": {}}
            if registry_change == "action":
                new_config["action"] = object()
            intent.async_register(hass, ScriptIntentHandler(intent_name, new_config))
        elif registry_change == "unrelated":
            intent.async_remove(hass, "OtherQuery")
            intent.async_register(hass, ScriptIntentHandler("OtherQuery", {"speech": {}}))
        elif registry_change == "mutate":
            handler.config["action"] = object()
        return None if kind == "no_match" else response

    ha_handle = AsyncMock(side_effect=handle_intents)
    monkeypatch.setattr(conversation, "async_handle_intents", ha_handle)
    monkeypatch.setattr(
        "custom_components.ai_hub.intents.get_global_intent_handler", lambda hass: None
    )

    agent = SimpleNamespace(
        hass=hass, entity_id="conversation.test",
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
    ha_handle.assert_awaited_once()
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
