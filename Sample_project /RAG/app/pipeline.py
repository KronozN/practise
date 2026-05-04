"""
RAG Pipeline Orchestrator
──────────────────────────
Wires all five layers into a single coherent pipeline:

  QueryProcessor → VectorRetriever → Reranker → Generator → Evaluator

A single RAGPipeline instance is created at startup and shared across requests.
"""
from __future__ import annotations

import time
from functools import lru_cache

from loguru import logger

from config.settings import get_settings
from app.layers.query_processing import QueryProcessor
from app.layers.vector_retrieval import VectorRetriever
from app.layers.reranking import Reranker
from app.layers.generation import Generator
from app.layers.evaluation import Evaluator, LayerTimings
from app.models.schemas import (
    QueryRequest, QueryResponse,
    IngestRequest, IngestResponse,
    CollectionStats, DeleteRequest,
)


class RAGPipeline:
    def __init__(self) -> None:
        cfg = get_settings()
        logger.info("Initialising RAG pipeline…")
        self.query_processor = QueryProcessor()
        self.retriever = VectorRetriever()
        self.reranker = Reranker()
        self.generator = Generator()
        self.evaluator = Evaluator(embedding_model_name=cfg.embedding_model)
        self._cfg = cfg
        logger.info("RAG pipeline ready ✓")

    # ── Main query entrypoint ──────────────────────────────────────────────────

    def query(self, request: QueryRequest) -> QueryResponse:
        total_start = time.perf_counter()
        timings = LayerTimings()
        cfg = self._cfg

        top_k_retrieval = request.top_k_retrieval or cfg.top_k_retrieval
        top_k_rerank = request.top_k_rerank or cfg.top_k_rerank

        # ── Layer 1: Query Processing ─────────────────────────────────────────
        t = time.perf_counter()
        processed = self.query_processor.process(request.query)
        timings.query_processing_ms = (time.perf_counter() - t) * 1_000

        # ── Layer 2: Vector Retrieval ─────────────────────────────────────────
        retrieved_chunks, timings.retrieval_ms = self.retriever.retrieve(
            processed, top_k=top_k_retrieval
        )

        # ── Layer 3: Re-ranking ───────────────────────────────────────────────
        reranked_chunks, timings.reranking_ms = self.reranker.rerank(
            processed.normalized, retrieved_chunks, top_k=top_k_rerank
        )

        # ── Layer 4: Generation ───────────────────────────────────────────────
        t = time.perf_counter()
        gen_result = self.generator.generate(processed.normalized, reranked_chunks)
        timings.generation_ms = (time.perf_counter() - t) * 1_000

        # ── Layer 5: Evaluation ───────────────────────────────────────────────
        evaluation = None
        if request.include_evaluation:
            evaluation = self.evaluator.evaluate(
                query=processed.normalized,
                answer=gen_result.answer,
                context_chunks=reranked_chunks,
                timings=timings,
            )

        total_ms = (time.perf_counter() - total_start) * 1_000
        logger.info("Pipeline complete in {:.1f} ms", total_ms)

        return QueryResponse(
            query=request.query,
            answer=gen_result.answer,
            retrieved_chunks=retrieved_chunks,
            reranked_chunks=reranked_chunks,
            evaluation=evaluation,
            total_latency_ms=round(total_ms, 2),
        )

    # ── Ingest ────────────────────────────────────────────────────────────────

    def ingest(self, request: IngestRequest) -> IngestResponse:
        ids = self.retriever.ingest(
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids,
        )
        return IngestResponse(indexed=len(ids), ids=ids)

    # ── Collection management ─────────────────────────────────────────────────

    def stats(self) -> CollectionStats:
        s = self.retriever.stats()
        return CollectionStats(**s)

    def delete(self, request: DeleteRequest) -> dict:
        self.retriever.delete(ids=request.ids, where=request.where)
        return {"status": "ok", "collection_size": self.retriever.stats()["document_count"]}


@lru_cache(maxsize=1)
def get_pipeline() -> RAGPipeline:
    """Return the singleton RAGPipeline (initialised once at first call)."""
    return RAGPipeline()
