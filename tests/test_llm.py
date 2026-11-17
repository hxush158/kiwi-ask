import pytest

from kiwi_ask.common import llm


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.openai.azure.com",
        "https://example.openai.azure.com/",
    ],
)
def test_get_chat_client_builds_v1_base_url(
    monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    # No .env, no real credential, no network: everything Azure-related is stubbed.
    monkeypatch.setattr(llm, "load_dotenv", lambda: None)
    monkeypatch.setattr(llm, "DefaultAzureCredential", lambda: object())
    monkeypatch.setattr(
        llm, "get_bearer_token_provider", lambda *_args: lambda: "fake-token"
    )
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", endpoint)

    client = llm.get_chat_client()

    assert str(client.base_url) == "https://example.openai.azure.com/openai/v1/"
