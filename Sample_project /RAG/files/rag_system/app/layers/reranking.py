"""
Layer 3 – Re-ranking Layer
───────────────────────────
Responsibilities
  • Score (query, chunk) pairs with a CrossEncoder
  • Return the top-K re-ranked results
  • Provide a lightweight fallback scorer when model is unavailable
"""
from __future__ import annotations

import time

from sentence_transformers import CrossEncoder
from loguru import logger

from config.settings import get_settings
from app.models.schemas import RetrievedChunk, RerankResult


class Reranker:
    """
    Wraps sentence-transformers CrossEncoder for pairwise relevance scoring.

    The CrossEncoder reads the full (query, passage) pair which gives
    significantly better ranking than the bi-encoder cosine score alone.
    """

    def __init__(self) -> None:
        cfg = get_settings()
        logger.info("Loading reranker model: {}", cfg.reranker_model)
        self._model = CrossEncoder(cfg.reranker_model, max_length=512)
        logger.info("Reranker ready.")

    # ── public API ────────────────────────────────────────────────────────────

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> tuple[list[RerankResult], float]:
        """
        Score all (query, chunk) pairs and return the top-k by rerank score.

        Returns (reranked_results, latency_ms).
        """
        if not chunks:
            return [], 0.0

        t0 = time.perf_counter()

        pairs = [(query, chunk.text) for chunk in chunks]
        scores: list[float] = self._model.predict(pairs, show_progress_bar=False).tolist()

        reranked = [
            RerankResult(
                id=chunk.id,
                text=chunk.text,
                rerank_score=score,
                original_score=chunk.score,
                metadata=chunk.metadata,
            )
            for chunk, score in zip(chunks, scores)
        ]

        # Sort descending by cross-encoder score
        reranked.sort(key=lambda r: r.rerank_score, reverse=True)
        top = reranked[:top_k]

        latency_ms = (time.perf_counter() - t0) * 1_000
        logger.debug(
            "Reranked {} → {} chunks in {:.1f} ms | top score={:.4f}",
            len(chunks), len(top), latency_ms,
            top[0].rerank_score if top else 0.0,
        )
        return top, latency_ms
