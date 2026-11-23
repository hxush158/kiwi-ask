import pytest

from kiwi_ask.common import config

REQUIRED = {
    "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
    "CHAT_DEPLOYMENT": "chat-mini",
    "EMBED_DEPLOYMENT": "embed-small",
    "SEARCH_ENDPOINT": "https://example.search.windows.net",
}


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Never read the developer's real .env in tests.
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    for name in [*REQUIRED, "SEARCH_INDEX", "DOCINTEL_ENDPOINT", "MIN_RERANKER_SCORE"]:
        monkeypatch.delenv(name, raising=False)
    config.get_settings.cache_clear()


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED.items():
        monkeypatch.setenv(name, value)

    settings = config.get_settings()

    assert settings.search_index == "kiwiask-m1"
    assert settings.docintel_endpoint is None
    assert settings.min_reranker_score == 1.5


def test_missing_required_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED.items():
        if name != "SEARCH_ENDPOINT":
            monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match="SEARCH_ENDPOINT"):
        config.get_settings()
