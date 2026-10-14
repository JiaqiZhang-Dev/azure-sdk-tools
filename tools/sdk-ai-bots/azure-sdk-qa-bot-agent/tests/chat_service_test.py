"""Unit tests for ChatService memory scope resolution."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.chat import ChatRequest, Message as ChatMessage
from services.chat_service import ChatService

# -- Memory scope handling ------------


def test_chat_service_resolves_memory_scope() -> None:
    service = ChatService()

    # user_id present → user_{user_id}
    with_user_id = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(
            role="user", content="hello", user_id="29:orgid:abc-def-123"
        ),
    )
    assert service._resolve_memory_scope(with_user_id) == "user_29orgidabc-def-123"

    # user_id present even when extra fields are set
    with_both = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(
            role="user", content="hello", user_id="29:orgid:abc-def-123"
        ),
    )
    assert service._resolve_memory_scope(with_both) == "user_29orgidabc-def-123"

    # No user_id → None
    no_user_id = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(role="user", content="hello"),
    )
    assert service._resolve_memory_scope(no_user_id) is None

    # No user_id → None
    scope_but_no_user = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(role="user", content="hello"),
    )
    assert service._resolve_memory_scope(scope_but_no_user) is None

    assert (
        service._build_memory_scope_message("my-scope")
        == "[memory_scope] value=my-scope"
    )


def test_chat_service_returns_none_when_user_id_empty() -> None:
    """Empty/whitespace user_id returns None."""
    service = ChatService()

    empty_id = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(role="user", content="hello", user_id=""),
    )
    assert service._resolve_memory_scope(empty_id) is None

    whitespace_id = ChatRequest(
        tenant_id="azure_sdk_qa_bot",
        message=ChatMessage(role="user", content="hello", user_id="  "),
    )
    assert service._resolve_memory_scope(whitespace_id) is None


@pytest.mark.asyncio
async def test_rebuild_replays_safe_messages_in_chronological_order() -> None:
    """Recovery replays durable Cosmos messages into a fresh conversation."""
    from datetime import datetime, timezone

    from models.conversation import ConversationMessageItem, ConversationType, Role

    openai_client = MagicMock()
    openai_client.conversations.create = AsyncMock(
        return_value=SimpleNamespace(id="conv-new")
    )
    service = ChatService()
    service._conversation_service.get_messages_by_conversation_id = AsyncMock(
        return_value=[
            ConversationMessageItem(
                id="user-old",
                tenant_id="azure_sdk_qa_bot",
                sender_role=Role.User,
                sender_id="user-1",
                sender_name="Ada",
                content="previous question",
                created_at=datetime.now(timezone.utc),
                conversation_id="teams-thread",
                conversation_type="teams_channel",
                conversation_partition="teams_channel:teams-thread",
            ),
            ConversationMessageItem(
                id="bot-old",
                tenant_id="azure_sdk_qa_bot",
                sender_role=Role.System,
                sender_id="azure-sdk-qa-bot",
                sender_name="Azure SDK Q&A Bot",
                content="previous answer",
                created_at=datetime.now(timezone.utc),
                conversation_id="teams-thread",
                conversation_type="teams_channel",
                conversation_partition="teams_channel:teams-thread",
            ),
            ConversationMessageItem(
                id="current-message",
                tenant_id="azure_sdk_qa_bot",
                sender_role=Role.User,
                sender_id="user-1",
                sender_name="Ada",
                content="current question",
                created_at=datetime.now(timezone.utc),
                conversation_id="teams-thread",
                conversation_type="teams_channel",
                conversation_partition="teams_channel:teams-thread",
            ),
        ]
    )
    replacement_id, rebuilt = await service._rebuild_conversation_after_failure(
        "teams-thread",
        ConversationType.teams_channel,
        openai_client,
    )

    assert replacement_id == "conv-new"
    assert [item["role"] for item in rebuilt] == [
        "user",
        "assistant",
        "user",
    ]
    assert [item["content"] for item in rebuilt] == [
        "previous question",
        "previous answer",
        "current question",
    ]
    assert openai_client.conversations.items.list.call_count == 0


def test_stateless_session_ids_are_isolated_by_agent() -> None:
    """Warm stateless sessions are reused only by the agent that created them."""
    service = ChatService(openai_client=MagicMock())

    service._set_stateless_session_id("azure-sdk-agent", "sdk-session")
    service._set_stateless_session_id("azure-mcp-agent", "mcp-session")

    assert service._get_stateless_session_id("azure-sdk-agent") == "sdk-session"
    assert service._get_stateless_session_id("azure-mcp-agent") == "mcp-session"


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt_agent", [False, True])
@pytest.mark.parametrize("threaded", [False, True])
async def test_chat_preserves_prompt_and_hosted_agent_paths(
    monkeypatch: pytest.MonkeyPatch, prompt_agent: bool, threaded: bool
) -> None:
    """Avatar passthrough must not replace main's hosted-agent lifecycle."""
    import asyncio

    import services.chat_service as chat_module

    agent_name = "jay-parikh-agent" if prompt_agent else "azure-sdk-chat-agent"
    tenant_id = "digital_avatar_jay_parikh" if prompt_agent else "typespec_channel_qa_bot"
    project_client = MagicMock()
    project_client.agents.get = AsyncMock(
        return_value=SimpleNamespace(
            versions=SimpleNamespace(
                latest=SimpleNamespace(name=agent_name, version="2")
            )
        )
    )
    service = ChatService(
        project_client=project_client,
        settings=lambda key, default=None: default,
    )
    hosted_client = MagicMock()
    monkeypatch.setattr(service, "_get_openai_client", MagicMock(return_value=hosted_client))
    service._resolve_conversation = AsyncMock(return_value=("conv-existing", False))
    service._save_bot_answer_to_conversation = AsyncMock()
    service._set_stateless_session_id(agent_name, "warm-session")
    response = SimpleNamespace(
        id="response-1", status="completed", output=[], output_text="answer",
        model_extra={"agent_session_id": "captured-session"},
    )
    invoke = AsyncMock(return_value=("trace-1", response))
    monkeypatch.setattr(chat_module.HostedAgentClient, "invoke", invoke)

    result = await service.chat(
        ChatRequest(
            tenant_id=tenant_id,
            conversation_id="thread-1" if threaded else None,
            conversation_type="teams_channel" if threaded else None,
            message=ChatMessage(role="user", content="hello", user_id="user-1"),
        )
    )
    await asyncio.sleep(0)

    project_client.agents.get.assert_awaited_once_with(agent_name)
    assert result.trace_id == "trace-1"
    assert result.agent_conversation_id == ("conv-existing" if threaded else None)
    call = invoke.call_args.kwargs
    assert call["agent_ref"]["name"] == agent_name
    assert call["agent_ref"]["version"] == "2"
    assert call["agent_session_id"] == (
        "warm-session" if not threaded and not prompt_agent else None
    )
    items = call["conversation_items"]
    assert items[-1] == {"type": "message", "role": "user", "content": "hello"}
    if prompt_agent:
        project_client.get_openai_client.assert_called_once_with()
        service._get_openai_client.assert_not_called()
        assert len(items) == 1
        service._save_bot_answer_to_conversation.assert_not_awaited()
    else:
        project_client.get_openai_client.assert_not_called()
        service._get_openai_client.assert_called_once_with(agent_name)
        assert any("[memory_scope]" in item["content"] for item in items)
        if not threaded:
            assert "[tenant_context]" in items[0]["content"]
        service._save_bot_answer_to_conversation.assert_awaited_once()


def test_prompt_agent_response_is_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avatar output keeps its markdown and skips shared result enrichment."""
    service = ChatService()
    for method in ("_extract_tool_results", "_extract_routed_tenant", "_extract_references_from_text"):
        monkeypatch.setattr(service, method, MagicMock(side_effect=AssertionError(method)))
    result = service._postprocess(
        ChatRequest(
            tenant_id="digital_avatar_jay_parikh",
            message=ChatMessage(role="user", content="hello"),
            with_full_context=True,
        ),
        SimpleNamespace(
            id="response-1", output=[],
            output_text="Answer\n\n**References**\n- [Public source](https://example.com)",
        ),
        None,
    )
    assert result.answer == "Answer\n\n**References**\n- [Public source](https://example.com)"
    assert result.references is None
    assert result.full_context is None
    assert result.route_tenant is None


@pytest.mark.asyncio
async def test_get_agent_uses_configured_version() -> None:
    project_client = MagicMock()
    expected = SimpleNamespace(name="azure-sdk-chat-agent", version="3")
    project_client.agents.get_version = AsyncMock(return_value=expected)

    agent = await ChatService()._get_agent(project_client, expected.name, "3")

    assert agent is expected
    project_client.agents.get_version.assert_awaited_once_with(expected.name, "3")
    project_client.agents.get.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt_agent", [False, True])
async def test_conversation_recovery_preserves_prompt_passthrough(
    monkeypatch: pytest.MonkeyPatch, prompt_agent: bool
) -> None:
    import asyncio

    import services.chat_service as chat_module
    from utils.azure_ai_foundry_agent import ConversationBrokenError

    service = ChatService(
        project_client=MagicMock(), openai_client=MagicMock(),
        settings=lambda key, default=None: default,
    )
    service._get_agent = AsyncMock(return_value=SimpleNamespace(name="agent", version="1"))
    service._resolve_conversation = AsyncMock(return_value=("conv-broken", True))
    service._rebuild_conversation_after_failure = AsyncMock(
        return_value=("conv-replacement", [{"type": "message", "role": "user", "content": "hello"}])
    )
    service._conversation_service.save_agent_conversation_mapping = AsyncMock()
    service._save_bot_answer_to_conversation = AsyncMock()
    response = SimpleNamespace(id="response-1", status="completed", output=[], output_text="answer")
    invoke = AsyncMock(side_effect=[ConversationBrokenError("empty"), ("trace-1", response)])
    monkeypatch.setattr(chat_module.HostedAgentClient, "invoke", invoke)

    result = await service.chat(
        ChatRequest(
            tenant_id="digital_avatar_jay_parikh" if prompt_agent else "typespec_channel_qa_bot",
            conversation_id="thread-1", conversation_type="teams_channel",
            message=ChatMessage(role="user", content="hello"),
        )
    )
    await asyncio.sleep(0)

    assert result.agent_conversation_id == "conv-replacement"
    assert invoke.await_count == 2
    recovered = invoke.call_args.kwargs
    assert recovered["agent_conversation_id"] == "conv-replacement"
    system_items = [item for item in recovered["conversation_items"] if item["role"] == "system"]
    if prompt_agent:
        assert system_items == []
    else:
        assert "[tenant_context]" in system_items[0]["content"]
    service._conversation_service.save_agent_conversation_mapping.assert_awaited_once_with(
        "thread-1", "teams_channel", agent_conversation_id="conv-replacement"
    )
