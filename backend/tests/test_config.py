import pytest
from pydantic import ValidationError

from app.config import Settings


def clear_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "LLM_BASE_URL",
        "LLM_MODEL",
        "LLM_API_KEY",
        "CONTEXT_TOKEN_BUDGET",
        "MAX_OUTPUT_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_settings_require_base_url_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings(monkeypatch)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_read_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings(monkeypatch)
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen3")
    monkeypatch.setenv("LLM_API_KEY", "ollama")
    monkeypatch.setenv("CONTEXT_TOKEN_BUDGET", "4096")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "512")

    settings = Settings(_env_file=None)

    assert settings.base_url == "http://localhost:11434/v1"
    assert settings.model_name == "qwen3"
    assert settings.api_key == "ollama"
    assert settings.context_token_budget == 4096
    assert settings.max_output_tokens == 512


@pytest.mark.parametrize(
    ("context_budget", "max_output", "expected_error"),
    [
        ("0", "128", "greater than 0"),
        ("512", "512", "max_output_tokens must be less than context_token_budget"),
    ],
)
def test_settings_reject_invalid_budgets(
    monkeypatch: pytest.MonkeyPatch,
    context_budget: str,
    max_output: str,
    expected_error: str,
) -> None:
    clear_settings(monkeypatch)
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "example-chat")
    monkeypatch.setenv("CONTEXT_TOKEN_BUDGET", context_budget)
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", max_output)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    assert expected_error in str(exc_info.value)
