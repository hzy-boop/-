from langchain_openai import ChatOpenAI

from app.config import Settings


def build_chat_model(settings: Settings, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.model_name,
        base_url=settings.base_url,
        api_key=settings.api_key or "not-needed",
        max_tokens=settings.max_output_tokens,
        streaming=streaming,
    )
