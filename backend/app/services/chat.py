import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from starlette.responses import StreamingResponse

from app.config import Settings
from app.llm import build_chat_model
from app.memory import InputTooLongError, append_turn, get_history, get_or_create_conversation, trim_history
from app.prompts import build_chat_prompt
from app.schemas import ChatRequest

router = APIRouter()


def _sse(event: str, data: str) -> str:
    lines = data.splitlines() or [""]
    return "".join(f"{field}\n" for field in [f"event: {event}", *(f"data: {line}" for line in lines)]) + "\n"


@router.post("/api/chat/stream")
async def stream_chat(request: ChatRequest) -> StreamingResponse:
    conversation_id = get_or_create_conversation(request.conversation_id)

    async def generate() -> AsyncIterator[str]:
        try:
            settings = Settings()
            history = get_history(conversation_id)
            messages = build_chat_prompt().invoke(
                {"history": [*history, HumanMessage(content=request.message)]}
            ).to_messages()
            messages = trim_history(
                messages,
                token_budget=settings.context_token_budget,
                max_output_tokens=settings.max_output_tokens,
            )
            model = build_chat_model(settings, streaming=True)
            parts: list[str] = []
            async for chunk in model.astream(messages):
                text = getattr(chunk, "text", "")
                if not text and isinstance(getattr(chunk, "content", None), str):
                    text = chunk.content
                if text:
                    parts.append(text)
                    yield _sse("token", text)
            answer = "".join(parts)
            append_turn(conversation_id, request.message, answer)
            yield _sse("done", json.dumps({"conversation_id": conversation_id}, ensure_ascii=False))
        except InputTooLongError as exc:
            yield _sse("error", json.dumps({"code": "INPUT_TOO_LONG", "message": str(exc), "conversation_id": conversation_id}, ensure_ascii=False))
        except Exception:
            yield _sse("error", json.dumps({"code": "UPSTREAM_ERROR", "message": "上游模型请求失败，请稍后重试。", "conversation_id": conversation_id}, ensure_ascii=False))

    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
