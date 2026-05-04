"""
Layer 2 – Vector Retrieval Layer
──────────────────────────────────
Responsibilities
  • Maintain a ChromaDB collection
  • Embed queries with SentenceTransformers
  • Retrieve top-K candidates
  • Expose ingest / delete helpers
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from loguru import logger

from config.settings import get_settings
from app.layers.query_processing import ProcessedQuery
from app.models.schemas import RetrievedChunk


class VectorRetriever:
    """
    Singleton-friendly wrapper around ChromaDB + SentenceTransformers.

    Usage
    -----
    retriever = VectorRetriever()
    retriever.ingest(docs, metadatas)
    chunks = retriever.retrieve(processed_query, top_k=20)
    """

    def __init__(self) -> None:
        cfg = get_settings()
        logger.info("Loading embedding model: {}", cfg.embedding_model)
        self._embedder = SentenceTransformer(cfg.embedding_model)

        logger.info("Initialising ChromaDB at {}", cfg.chroma_persist_dir)
        self._client = chromadb.PersistentClient(
            path=cfg.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=cfg.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Collection '{}' ready — {} docs",
            cfg.chroma_collection,
            self._collection.count(),
        )

    # ── public API ────────────────────────────────────────────────────────────

    def ingest(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Embed and upsert documents into ChromaDB."""
        if not documents:
            return []

        ids = ids or [str(uuid.uuid4()) for _ in documents]
        metadatas = metadatas or [{} for _ in documents]

        logger.info("Embedding {} documents…", len(documents))
        embeddings = self._embedder.encode(documents, show_progress_bar=False).tolist()

        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Upserted {} documents. Collection size: {}", len(documents), self._collection.count())
        return ids

    def retrieve(self, processed_query: ProcessedQuery, top_k: int) -> tuple[list[RetrievedChunk], float]:
        """
        Query ChromaDB using the normalised query (+ variants averaged).
        Returns (chunks, latency_ms).
        """
        t0 = time.perf_counter()

        # Embed all variants and average → richer query vector
        variants = processed_query.all_variants
        raw_embeddings = self._embedder.encode(variants, show_progress_bar=False)
        query_embedding = raw_embeddings.mean(axis=0).tolist()

        n_results = min(top_k, self._collection.count() or 1)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "distances", "metadatas"],
        )

        chunks: list[RetrievedChunk] = []
        docs = results["documents"][0]
        distances = results["distances"][0]
        metas = results["metadatas"][0]
        ids = results["ids"][0]

        for doc_id, text, dist, meta in zip(ids, docs, distances, metas):
            # ChromaDB cosine distance → similarity score
            score = 1.0 - dist
            chunks.append(RetrievedChunk(id=doc_id, text=text, score=score, metadata=meta or {}))

        latency_ms = (time.perf_counter() - t0) * 1_000
        logger.debug("Retrieved {} chunks in {:.1f} ms", len(chunks), latency_ms)
        return chunks, latency_ms

    def delete(self, ids: list[str] | None = None, where: dict | None = None) -> None:
        kwargs: dict[str, Any] = {}
        if ids:
            kwargs["ids"] = ids
        if where:
            kwargs["where"] = where
        self._collection.delete(**kwargs)
        logger.info("Deleted documents. Collection size now: {}", self._collection.count())

    def stats(self) -> dict[str, Any]:
        cfg = get_settings()
        return {
            "collection_name": cfg.chroma_collection,
            "document_count": self._collection.count(),
            "embedding_model": cfg.embedding_model,
        }
