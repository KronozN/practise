"""
Layer 5 – Evaluation Layer
───────────────────────────
Responsibilities
  • Faithfulness  – is the answer grounded in retrieved context?
  • Answer Relevance – does the answer address the query?
  • Context Precision – are the top chunks actually relevant?
  • Context Recall (estimated) – does context cover the answer?
  • Latency tracking per layer

All metrics are scored 0 → 1 (higher is better).
The scorers are lightweight (no external calls) so they add minimal overhead.
A richer implementation can swap in an LLM-as-judge scorer.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.models.schemas import EvaluationMetrics, RerankResult


@dataclass
class LayerTimings:
    query_processing_ms: float = 0.0
    retrieval_ms: float = 0.0
    reranking_ms: float = 0.0
    generation_ms: float = 0.0
    evaluation_ms: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "query_processing": round(self.query_processing_ms, 2),
            "retrieval": round(self.retrieval_ms, 2),
            "reranking": round(self.reranking_ms, 2),
            "generation": round(self.generation_ms, 2),
            "evaluation": round(self.evaluation_ms, 2),
        }


class Evaluator:
    """
    Heuristic + embedding-based RAG evaluator.

    Faithfulness
      Sentence-level: what fraction of answer sentences are semantically
      entailed by at least one context chunk (cosine ≥ threshold)?

    Answer Relevance
      Cosine similarity between the query embedding and the answer embedding.

    Context Precision
      Mean rerank score of top-k chunks (already normalised by CrossEncoder).

    Context Recall (estimated)
      Fraction of answer tokens present in the concatenated context.
    """

    _SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
    _TOKEN_SPLIT = re.compile(r"\W+")
    _COSINE_THRESHOLD = 0.45
    _STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
        "to", "for", "of", "and", "or", "but", "it", "its", "this", "that",
        "these", "those", "be", "been", "being", "have", "has", "had",
    }

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2") -> None:
        logger.info("Loading evaluator embedding model: {}", embedding_model_name)
        self._embedder = SentenceTransformer(embedding_model_name)

    # ── public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        query: str,
        answer: str,
        context_chunks: list[RerankResult],
        timings: LayerTimings,
    ) -> EvaluationMetrics:
        t0 = time.perf_counter()

        faithfulness = self._faithfulness(answer, context_chunks)
        answer_relevance = self._answer_relevance(query, answer)
        context_precision = self._context_precision(context_chunks)
        context_recall = self._context_recall(answer, context_chunks)

        timings.evaluation_ms = (time.perf_counter() - t0) * 1_000

        metrics = EvaluationMetrics(
            faithfulness=round(faithfulness, 4),
            answer_relevance=round(answer_relevance, 4),
            context_precision=round(context_precision, 4),
            context_recall=round(context_recall, 4),
            latency_ms=timings.as_dict(),
        )
        logger.info(
            "Evaluation | faithfulness={:.3f} relevance={:.3f} "
            "precision={:.3f} recall={:.3f} | eval={:.1f} ms",
            faithfulness, answer_relevance, context_precision,
            context_recall, timings.evaluation_ms,
        )
        return metrics

    # ── private scorers ───────────────────────────────────────────────────────

    def _faithfulness(self, answer: str, chunks: list[RerankResult]) -> float:
        """Fraction of answer sentences entailed by ≥1 context chunk."""
        if not answer.strip() or not chunks:
            return 0.0

        sentences = [s.strip() for s in self._SENT_SPLIT.split(answer) if s.strip()]
        if not sentences:
            return 0.0

        context_texts = [c.text for c in chunks]
        all_texts = sentences + context_texts
        embeddings = self._embedder.encode(all_texts, show_progress_bar=False)

        sent_embs = embeddings[: len(sentences)]
        ctx_embs = embeddings[len(sentences):]

        entailed = 0
        for s_emb in sent_embs:
            sims = self._cosine_sim_batch(s_emb, ctx_embs)
            if sims.max() >= self._COSINE_THRESHOLD:
                entailed += 1

        return entailed / len(sentences)

    def _answer_relevance(self, query: str, answer: str) -> float:
        """Cosine similarity between query and answer embeddings."""
        if not answer.strip():
            return 0.0
        embs = self._embedder.encode([query, answer], show_progress_bar=False)
        return float(self._cosine_sim_batch(embs[0], embs[1:]).item())

    def _context_precision(self, chunks: list[RerankResult]) -> float:
        """Mean normalised rerank score of retrieved chunks."""
        if not chunks:
            return 0.0
        scores = np.array([c.rerank_score for c in chunks])
        # CrossEncoder logit → sigmoid to normalise to [0,1]
        normed = 1.0 / (1.0 + np.exp(-scores))
        return float(normed.mean())

    def _context_recall(self, answer: str, chunks: list[RerankResult]) -> float:
        """Fraction of meaningful answer tokens present in context."""
        if not answer.strip() or not chunks:
            return 0.0

        answer_tokens = {
            t.lower()
            for t in self._TOKEN_SPLIT.split(answer)
            if t and t.lower() not in self._STOP_WORDS and len(t) > 2
        }
        if not answer_tokens:
            return 1.0

        context_text = " ".join(c.text for c in chunks).lower()
        context_tokens = set(self._TOKEN_SPLIT.split(context_text))

        overlap = answer_tokens & context_tokens
        return len(overlap) / len(answer_tokens)

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _cosine_sim_batch(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
        mat_norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        mat_normed = matrix / mat_norms
        return mat_normed @ vec_norm
