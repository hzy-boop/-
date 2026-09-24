import pytest
import tiktoken
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.memory import (
    InputTooLongError,
    append_turn,
    count_message_tokens,
    get_history,
    get_or_create_conversation,
    trim_history,
)


def test_new_conversation_can_be_reused() -> None:
    conversation_id = get_or_create_conversation(None)

    assert conversation_id
    assert get_or_create_conversation(conversation_id) == conversation_id
    assert get_history(conversation_id) == []


def test_two_turns_are_saved_as_complete_message_pairs() -> None:
    conversation_id = get_or_create_conversation(None)

    append_turn(conversation_id, "我的订单是 A123", "收到，订单号是 A123。")
    append_turn(conversation_id, "我刚才的订单号是什么？", "是 A123。")

    history = get_history(conversation_id)
    assert [message.type for message in history] == ["human", "ai", "human", "ai"]
    assert [message.content for message in history] == [
        "我的订单是 A123",
        "收到，订单号是 A123。",
        "我刚才的订单号是什么？",
        "是 A123。",
    ]


def test_unknown_conversation_id_starts_a_new_conversation() -> None:
    new_id = get_or_create_conversation("unknown-id")

    assert new_id != "unknown-id"
    assert get_history(new_id) == []


def test_token_counter_uses_cl100k_base_and_message_overhead() -> None:
    encoding = tiktoken.get_encoding("cl100k_base")
    expected = 2 + 4 + len(encoding.encode("human")) + len(encoding.encode("hello"))

    assert count_message_tokens([HumanMessage(content="hello")]) == expected


def test_trim_history_drops_oldest_complete_turn_first() -> None:
    messages = [
        SystemMessage(content="客服规则"),
        HumanMessage(content="旧问题"),
        AIMessage(content="旧答复"),
        HumanMessage(content="最近问题"),
        AIMessage(content="最近答复"),
        HumanMessage(content="当前问题"),
    ]

    trimmed = trim_history(
        messages,
        token_budget=64,
        max_output_tokens=24,
        token_counter=lambda values: len(values) * 10,
    )

    assert [message.content for message in trimmed] == [
        "客服规则",
        "最近问题",
        "最近答复",
        "当前问题",
    ]


def test_trim_history_preserves_system_and_current_message() -> None:
    messages = [
        SystemMessage(content="客服规则"),
        HumanMessage(content="历史问题"),
        AIMessage(content="历史答复"),
        HumanMessage(content="当前问题"),
    ]

    trimmed = trim_history(
        messages,
        token_budget=44,
        max_output_tokens=24,
        token_counter=lambda values: len(values) * 10,
    )

    assert [message.content for message in trimmed] == ["客服规则", "当前问题"]


def test_trim_history_rejects_current_input_over_available_budget() -> None:
    messages = [
        SystemMessage(content="客服规则"),
        HumanMessage(content="当前问题"),
    ]

    with pytest.raises(InputTooLongError, match="available context budget"):
        trim_history(
            messages,
            token_budget=39,
            max_output_tokens=24,
            token_counter=lambda values: len(values) * 10,
        )
