from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = Field(validation_alias="LLM_BASE_URL")
    model_name: str = Field(validation_alias="LLM_MODEL")
    api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    context_token_budget: int = Field(
        default=8192,
        gt=0,
        validation_alias="CONTEXT_TOKEN_BUDGET",
    )
    max_output_tokens: int = Field(
        default=1024,
        gt=0,
        validation_alias="MAX_OUTPUT_TOKENS",
    )

    @model_validator(mode="after")
    def validate_token_budgets(self) -> Self:
        if self.max_output_tokens >= self.context_token_budget:
            raise ValueError(
                "max_output_tokens must be less than context_token_budget"
            )
        return self
