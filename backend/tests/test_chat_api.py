import json

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.main import app
from app.memory import get_history


class FakeStreamingModel:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls = []

    async def astream(self, messages):
        self.calls.append(messages)
        if self.fail:
            raise RuntimeError("upstream unavailable")
        yield AIMessageChunk(content="答复")
        yield AIMessageChunk(content="完成")


def parse_sse_events(body: str):
    events = []
    for block in body.strip().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line.startswith("event: "):
                fields["event"] = line[7:]
            elif line.startswith("data: "):
                fields["data"] = line[6:]
        if fields:
            events.append(fields)
    return events


def test_stream_emits_tokens_then_done_with_conversation_id(monkeypatch):
    from app.services import chat

    model = FakeStreamingModel()
    monkeypatch.setattr(chat, "build_chat_model", lambda settings, streaming=True: model)
    with TestClient(app) as client:
        response = client.post(
            "/api/chat/stream", json={"conversation_id": None, "message": "你好"}
        )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert [(item["event"], item["data"]) for item in events[:2]] == [
        ("token", "答复"),
        ("token", "完成"),
    ]
    assert events[-1]["event"] == "done"
    assert json.loads(events[-1]["data"])["conversation_id"]


def test_two_requests_reuse_context(monkeypatch):
    from app.services import chat

    model = FakeStreamingModel()
    monkeypatch.setattr(chat, "build_chat_model", lambda settings, streaming=True: model)
    with TestClient(app) as client:
        first = parse_sse_events(
            client.post(
                "/api/chat/stream", json={"message": "我的订单号是 A123"}
            ).text
        )
        conversation_id = json.loads(first[-1]["data"])["conversation_id"]
        client.post(
            "/api/chat/stream",
            json={"conversation_id": conversation_id, "message": "订单号是什么？"},
        )

    second_messages = model.calls[1]
    assert any(isinstance(message, HumanMessage) and "A123" in message.content for message in second_messages)
    assert any(isinstance(message, AIMessage) and "答复完成" in message.content for message in second_messages)


def test_upstream_error_emits_error_without_done_or_partial_history(monkeypatch):
    from app.services import chat

    model = FakeStreamingModel(fail=True)
    monkeypatch.setattr(chat, "build_chat_model", lambda settings, streaming=True: model)
    with TestClient(app) as client:
        events = parse_sse_events(
            client.post("/api/chat/stream", json={"message": "你好"}).text
        )

    assert events[-1]["event"] == "error"
    assert all(event["event"] != "done" for event in events)
    payload = json.loads(events[-1]["data"])
    assert payload["code"] == "UPSTREAM_ERROR"
    assert get_history(payload["conversation_id"]) == []


def test_blank_message_is_rejected_with_422():
    with TestClient(app) as client:
        response = client.post("/api/chat/stream", json={"message": "  "})
    assert response.status_code == 422


def test_after_sales_endpoint_returns_fixed_fields_and_uses_json_mode(monkeypatch):
    from app.services import after_sales
    from app.schemas import AfterSalesExtraction

    class FakeStructuredModel:
        async def ainvoke(self, prompt):
            assert "JSON" in prompt
            return AfterSalesExtraction(
                order_id="A123",
                request_type="退款",
                preferred_resolution="退款",
            )

    class FakeModel:
        def with_structured_output(self, schema, method):
            assert schema is AfterSalesExtraction
            assert method == "json_mode"
            return FakeStructuredModel()

    monkeypatch.setattr(after_sales, "build_chat_model", lambda settings: FakeModel())
    with TestClient(app) as client:
        response = client.post(
            "/api/after-sales/extract",
            json={"description": "订单 A123 商品破损，希望退款"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "order_id": "A123",
        "request_type": "退款",
        "preferred_resolution": "退款",
    }


def test_after_sales_upstream_parse_error_is_explicit_502(monkeypatch):
    from app.services import after_sales

    class FakeModel:
        def with_structured_output(self, schema, method):
            raise ValueError("malformed json")

    monkeypatch.setattr(after_sales, "build_chat_model", lambda settings: FakeModel())
    with TestClient(app) as client:
        response = client.post(
            "/api/after-sales/extract", json={"description": "商品有问题"}
        )
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "STRUCTURED_OUTPUT_ERROR"


def test_blank_extraction_description_is_rejected_with_422():
    with TestClient(app) as client:
        response = client.post(
            "/api/after-sales/extract", json={"description": "  "}
        )
    assert response.status_code == 422
