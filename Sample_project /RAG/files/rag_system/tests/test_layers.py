"""
Tests for all 5 RAG layers.
Run with: pytest tests/ -v
"""
from __future__ import annotations

import sys
import os
import math
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np
import pytest

# Make sure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────────────
# Layer 1 – Query Processing
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryProcessor:
    def setup_method(self):
        from app.layers.query_processing import QueryProcessor
        self.processor = QueryProcessor()

    def test_basic_normalisation(self):
        pq = self.processor.process("  What is machine learning?  ")
        assert pq.normalized == "What is machine learning"
        assert pq.original == "  What is machine learning?  "

    def test_question_prefix_stripped(self):
        pq = self.processor.process("What is deep learning?")
        assert "deep learning" in pq.expanded_variants[0]

    def test_empty_query_raises(self):
        with pytest.raises(ValueError):
            self.processor.process("   ")

    def test_all_variants_includes_normalized(self):
        pq = self.processor.process("How does transformer work")
        assert pq.normalized in pq.all_variants

    def test_processing_ms_positive(self):
        pq = self.processor.process("hello world")
        assert pq.processing_ms >= 0


# ─────────────────────────────────────────────────────────────────────────────
# Layer 2 – Vector Retrieval (mocked ChromaDB + SentenceTransformer)
# ─────────────────────────────────────────────────────────────────────────────

class TestVectorRetriever:
    def setup_method(self):
        # Patch heavy dependencies before import
        self.mock_st = MagicMock()
        self.mock_st.encode.return_value = np.random.rand(1, 384)

        self.mock_collection = MagicMock()
        self.mock_collection.count.return_value = 3
        self.mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["doc one", "doc two"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"src": "a"}, {"src": "b"}]],
        }

        self.mock_chroma_client = MagicMock()
        self.mock_chroma_client.get_or_create_collection.return_value = self.mock_collection

        patches = [
            patch("app.layers.vector_retrieval.SentenceTransformer", return_value=self.mock_st),
            patch("app.layers.vector_retrieval.chromadb.PersistentClient", return_value=self.mock_chroma_client),
        ]
        for p in patches:
            p.start()
        self._patches = patches

        from app.layers.vector_retrieval import VectorRetriever
        self.retriever = VectorRetriever()

    def teardown_method(self):
        for p in self._patches:
            p.stop()

    def test_ingest_returns_ids(self):
        ids = self.retriever.ingest(["doc a", "doc b"])
        assert len(ids) == 2

    def test_retrieve_returns_chunks(self):
        from app.layers.query_processing import QueryProcessor
        pq = QueryProcessor().process("machine learning")
        self.mock_st.encode.return_value = np.random.rand(len(pq.all_variants), 384)
        chunks, latency = self.retriever.retrieve(pq, top_k=5)
        assert len(chunks) == 2
        assert chunks[0].score == pytest.approx(0.9, abs=0.01)
        assert latency > 0

    def test_stats(self):
        s = self.retriever.stats()
        assert s["document_count"] == 3


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 – Re-ranking
# ─────────────────────────────────────────────────────────────────────────────

class TestReranker:
    def setup_method(self):
        self.mock_ce = MagicMock()
        self.mock_ce.predict.return_value = np.array([0.9, 0.4, 0.7])

        with patch("app.layers.reranking.CrossEncoder", return_value=self.mock_ce):
            from app.layers.reranking import Reranker
            self.reranker = Reranker()

        from app.models.schemas import RetrievedChunk
        self.chunks = [
            RetrievedChunk(id=f"id{i}", text=f"passage {i}", score=0.8 - i * 0.1, metadata={})
            for i in range(3)
        ]

    def test_rerank_sorts_by_score(self):
        results, latency = self.reranker.rerank("query", self.chunks, top_k=3)
        scores = [r.rerank_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self):
        results, _ = self.reranker.rerank("query", self.chunks, top_k=2)
        assert len(results) == 2

    def test_empty_chunks(self):
        results, latency = self.reranker.rerank("query", [], top_k=5)
        assert results == []
        assert latency == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 – Generation
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerator:
    def setup_method(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Generated answer."
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = mock_response

        with patch("app.layers.generation.OpenAI", return_value=mock_openai):
            from app.layers.generation import Generator
            self.generator = Generator()

        from app.models.schemas import RerankResult
        self.chunks = [
            RerankResult(id="1", text="Context text.", rerank_score=0.9, original_score=0.8, metadata={})
        ]

    def test_generate_returns_answer(self):
        result = self.generator.generate("What is AI?", self.chunks)
        assert result.answer == "Generated answer."

    def test_token_counts(self):
        result = self.generator.generate("query", self.chunks)
        assert result.prompt_tokens == 100
        assert result.completion_tokens == 50

    def test_latency_positive(self):
        result = self.generator.generate("query", self.chunks)
        assert result.latency_ms >= 0


# ─────────────────────────────────────────────────────────────────────────────
# Layer 5 – Evaluation
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluator:
    def setup_method(self):
        self.mock_embedder = MagicMock()
        # Return predictable embeddings
        def fake_encode(texts, **_):
            n = len(texts)
            vecs = np.eye(n, 384)  # orthogonal unit vectors
            return vecs

        self.mock_embedder.encode.side_effect = fake_encode

        with patch("app.layers.evaluation.SentenceTransformer", return_value=self.mock_embedder):
            from app.layers.evaluation import Evaluator, LayerTimings
            self.evaluator = Evaluator()
            self.LayerTimings = LayerTimings

        from app.models.schemas import RerankResult
        self.chunks = [
            RerankResult(id="1", text="AI is machine learning.", rerank_score=0.8, original_score=0.7, metadata={})
        ]

    def test_evaluation_returns_all_metrics(self):
        metrics = self.evaluator.evaluate(
            "What is AI?",
            "AI refers to machine learning systems.",
            self.chunks,
            self.LayerTimings(),
        )
        assert 0.0 <= metrics.faithfulness <= 1.0
        assert 0.0 <= metrics.answer_relevance <= 1.0
        assert 0.0 <= metrics.context_precision <= 1.0
        assert 0.0 <= metrics.context_recall <= 1.0

    def test_latency_dict_has_all_layers(self):
        metrics = self.evaluator.evaluate("q", "a", self.chunks, self.LayerTimings())
        assert set(metrics.latency_ms.keys()) == {
            "query_processing", "retrieval", "reranking", "generation", "evaluation"
        }

    def test_empty_answer_faithfulness_zero(self):
        metrics = self.evaluator.evaluate("q", "", self.chunks, self.LayerTimings())
        assert metrics.faithfulness == 0.0

    def test_context_recall_full_overlap(self):
        from app.models.schemas import RerankResult
        chunks = [RerankResult(id="1", text="machine learning deep neural networks", rerank_score=0.9, original_score=0.8, metadata={})]
        metrics = self.evaluator.evaluate(
            "query",
            "machine learning and neural networks",
            chunks,
            self.LayerTimings(),
        )
        # "machine", "learning", "neural", "networks" are all in context
        assert metrics.context_recall > 0.5
