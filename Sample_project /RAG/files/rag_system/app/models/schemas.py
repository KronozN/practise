"""Shared Pydantic models used across all layers."""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    documents: list[str] = Field(..., description="Raw text chunks to index")
    metadatas: list[dict[str, Any]] | None = Field(
        default=None, description="Optional per-doc metadata dicts"
    )
    ids: list[str] | None = Field(
        default=None, description="Optional stable IDs; auto-generated when omitted"
    )


class IngestResponse(BaseModel):
    indexed: int
    ids: list[str]


# ── Query ─────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k_retrieval: int | None = Field(default=None, ge=1, le=100)
    top_k_rerank: int | None = Field(default=None, ge=1, le=50)
    include_evaluation: bool = True


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = {}


class RerankResult(BaseModel):
    id: str
    text: str
    rerank_score: float
    original_score: float
    metadata: dict[str, Any] = {}


class EvaluationMetrics(BaseModel):
    faithfulness: float = Field(description="0-1: answer grounded in context")
    answer_relevance: float = Field(description="0-1: answer addresses the query")
    context_precision: float = Field(description="0-1: retrieved context quality")
    context_recall: float = Field(description="0-1: context coverage estimate")
    latency_ms: dict[str, float] = Field(description="Per-layer latency breakdown")


class QueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    reranked_chunks: list[RerankResult]
    evaluation: EvaluationMetrics | None = None
    total_latency_ms: float


# ── Collection management ──────────────────────────────────────────────────────

class CollectionStats(BaseModel):
    collection_name: str
    document_count: int
    embedding_model: str


class DeleteRequest(BaseModel):
    ids: list[str] | None = None
    where: dict[str, Any] | None = None
