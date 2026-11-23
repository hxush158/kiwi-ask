"""Keyless Azure clients: every client authenticates with Entra ID, never API keys."""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from kiwi_ask.common.config import get_settings


@lru_cache(maxsize=1)
def get_credential() -> DefaultAzureCredential:
    """One credential per process: az login locally, managed identity in Azure."""
    return DefaultAzureCredential()


def get_search_client() -> SearchClient:
    """Query and upload documents in the M1 index."""
    settings = get_settings()
    return SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index,
        credential=get_credential(),
    )


def get_index_client() -> SearchIndexClient:
    """Create or update index definitions (ingestion only)."""
    return SearchIndexClient(
        endpoint=get_settings().search_endpoint,
        credential=get_credential(),
    )
