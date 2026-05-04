"""FastAPI router — all RAG endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.pipeline import RAGPipeline, get_pipeline
from app.models.schemas import (
    IngestRequest, IngestResponse,
    QueryRequest, QueryResponse,
    CollectionStats, DeleteRequest,
)

router = APIRouter(prefix="/api/v1", tags=["RAG"])


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health", summary="Health check")
def health() -> dict:
    return {"status": "ok"}


# ── Ingest ─────────────────────────────────────────────────────────────────────

@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Layer 2 – Ingest documents into the vector store",
)
def ingest(
    body: IngestRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> IngestResponse:
    if not body.documents:
        raise HTTPException(status_code=400, detail="No documents provided.")
    return pipeline.ingest(body)


# ── Query ──────────────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Run the full 5-layer RAG pipeline",
)
def query(
    body: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResponse:
    try:
        return pipeline.query(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── Collection management ──────────────────────────────────────────────────────

@router.get(
    "/collection/stats",
    response_model=CollectionStats,
    summary="Get vector store statistics",
)
def collection_stats(
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> CollectionStats:
    return pipeline.stats()


@router.delete(
    "/collection",
    summary="Delete documents from the vector store",
)
def delete_documents(
    body: DeleteRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> dict:
    if not body.ids and not body.where:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'ids' or 'where' filter to delete.",
        )
    return pipeline.delete(body)
