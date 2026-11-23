"""Shared M1 data types, used by ingestion (T2), retrieval (T3) and the API (T4)."""

from typing import Literal

from pydantic import BaseModel

Agency = Literal["tenancy", "nhc"]

AGENCY_HOMEPAGES: dict[Agency, str] = {
    "tenancy": "https://www.tenancy.govt.nz/",
    "nhc": "https://www.naturalhazards.govt.nz/",
}


class RetrievedChunk(BaseModel):
    """One search result. Field names match the `kiwiask-m1` index (M1 spec)."""

    id: str
    doc_file: str
    agency: Agency
    title: str
    section: str
    content: str
    url: str
    licence: str
    retrieved: str
    page: int
    reranker_score: float | None = None
