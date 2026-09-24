from collections.abc import Callable, Sequence
from uuid import uuid4

import tiktoken
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


class InputTooLongError(ValueError):
    """The system prompt and current user message exceed the input budget."""


_conversations: dict[str, list[BaseMessage]] = {}
_encoding = tiktoken.get_encoding("cl100k_base")


def get_or_create_conversation(conversation_id: str | None) -> str:
    if conversation_id and conversation_id in _conversations:
        return conversation_id

    new_id = str(uuid4())
    _conversations[new_id] = []
    return new_id


def get_history(conversation_id: str) -> list[BaseMessage]:
    return list(_conversations.get(conversation_id, []))


def append_turn(
    conversation_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    if conversation_id not in _conversations:
        raise KeyError(f"unknown conversation_id: {conversation_id}")
    _conversations[conversation_id].extend(
        [HumanMessage(content=user_message), AIMessage(content=assistant_message)]
    )


def count_message_tokens(messages: Sequence[BaseMessage]) -> int:
    """Estimate message tokens using cl100k_base for all compatible providers."""
    total = 2
    for message in messages:
        content = message.content
        if not isinstance(content, str):
            content = " ".join(
                str(block.get("text", "")) if isinstance(block, dict) else str(block)
                for block in content
            )
        total += 4
        total += len(_encoding.encode(message.type, disallowed_special=()))
        total += len(_encoding.encode(content, disallowed_special=()))
    return total


def trim_history(
    messages: Sequence[BaseMessage],
    token_budget: int,
    max_output_tokens: int,
    token_counter: Callable[[Sequence[BaseMessage]], int] = count_message_tokens,
) -> list[BaseMessage]:
    if len(messages) < 2 or not isinstance(messages[0], SystemMessage):
        raise ValueError("messages must start with a system message and end with the current user message")
    if not isinstance(messages[-1], HumanMessage):
        raise ValueError("messages must end with the current user message")

    input_budget = token_budget - max_output_tokens
    if input_budget <= 0:
        raise InputTooLongError("available context budget is not positive")

    system_message = messages[0]
    current_message = messages[-1]
    history = list(messages[1:-1])
    if len(history) % 2 != 0:
        raise ValueError("conversation history must contain complete user/assistant turns")

    required = [system_message, current_message]
    if token_counter(required) > input_budget:
        raise InputTooLongError("system prompt and current message exceed available context budget")

    retained_history: list[BaseMessage] = []
    for index in range(len(history) - 2, -1, -2):
        turn = history[index : index + 2]
        candidate_history = [*turn, *retained_history]
        if token_counter([system_message, *candidate_history, current_message]) > input_budget:
            break
        retained_history = candidate_history

    return [system_message, *retained_history, current_message]
