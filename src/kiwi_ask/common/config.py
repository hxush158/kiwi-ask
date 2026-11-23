"""Settings from environment variables (.env locally, app settings in Azure)."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    azure_openai_endpoint: str
    chat_deployment: str
    embed_deployment: str
    search_endpoint: str
    search_index: str
    # Only ingestion needs Document Intelligence; the API does not.
    docintel_endpoint: str | None
    min_reranker_score: float


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable {name} (see README: Run it).")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        azure_openai_endpoint=_required("AZURE_OPENAI_ENDPOINT"),
        chat_deployment=_required("CHAT_DEPLOYMENT"),
        embed_deployment=_required("EMBED_DEPLOYMENT"),
        search_endpoint=_required("SEARCH_ENDPOINT"),
        search_index=os.environ.get("SEARCH_INDEX", "kiwiask-m1"),
        docintel_endpoint=os.environ.get("DOCINTEL_ENDPOINT") or None,
        min_reranker_score=float(os.environ.get("MIN_RERANKER_SCORE", "1.5")),
    )
