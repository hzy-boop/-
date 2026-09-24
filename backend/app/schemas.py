from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class AfterSalesRequest(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def description_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must not be blank")
        return value


class AfterSalesExtraction(BaseModel):
    order_id: str | None
    request_type: str | None
    preferred_resolution: str | None
