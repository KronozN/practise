"""
cli_demo.py – smoke-test the pipeline end-to-end without a running server.

Usage:
  python cli_demo.py
"""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

console = Console()


def main() -> None:
    console.rule("[bold cyan]RAG System – CLI Demo")

    # ── Sample corpus ──────────────────────────────────────────────────────────
    documents = [
        "Retrieval-Augmented Generation (RAG) is a technique that combines retrieval "
        "from a knowledge base with large language model generation to produce grounded answers.",
        "ChromaDB is an open-source vector database designed for storing and querying "
        "high-dimensional embeddings efficiently.",
        "SentenceTransformers provides pre-trained models for computing dense vector "
        "representations of sentences for semantic search.",
        "Cross-encoder models re-rank candidate passages by scoring each (query, passage) "
        "pair jointly, achieving higher accuracy than bi-encoder cosine similarity.",
        "FastAPI is a modern Python web framework that offers automatic OpenAPI documentation "
        "and high performance via async/await.",
        "Faithfulness in RAG evaluation measures whether the generated answer is supported "
        "by the retrieved context passages.",
        "Context precision measures the quality of retrieved documents — a high score means "
        "the top-K passages are genuinely relevant to the query.",
        "OpenAI-compatible APIs allow developers to swap in any LLM backend (local or hosted) "
        "without changing application code.",
    ]

    console.print(Panel(
        f"[green]Indexing {len(documents)} documents into ChromaDB…[/]",
        title="Layer 2 – Vector Retrieval (Ingest)",
    ))

    from app.pipeline import RAGPipeline
    from app.models.schemas import IngestRequest, QueryRequest

    pipeline = RAGPipeline()

    ingest_resp = pipeline.ingest(IngestRequest(documents=documents))
    console.print(f"  ✓ Indexed [bold]{ingest_resp.indexed}[/] documents")

    # ── Query ──────────────────────────────────────────────────────────────────
    query_text = "How does cross-encoder re-ranking improve RAG?"
    console.print(Panel(
        f"[yellow]{query_text}[/]",
        title="Query",
    ))

    resp = pipeline.query(QueryRequest(query=query_text, include_evaluation=True))

    # ── Answer ─────────────────────────────────────────────────────────────────
    console.print(Panel(resp.answer, title="[bold green]Generated Answer (Layer 4)"))

    # ── Retrieved chunks ───────────────────────────────────────────────────────
    tbl = Table(box=box.SIMPLE, title="Retrieved Chunks (Layer 2 → Layer 3)")
    tbl.add_column("Rank", style="bold")
    tbl.add_column("Rerank Score", justify="right")
    tbl.add_column("Vector Score", justify="right")
    tbl.add_column("Text snippet")

    for i, c in enumerate(resp.reranked_chunks, 1):
        tbl.add_row(
            str(i),
            f"{c.rerank_score:.4f}",
            f"{c.original_score:.4f}",
            c.text[:80] + "…",
        )
    console.print(tbl)

    # ── Evaluation ─────────────────────────────────────────────────────────────
    if resp.evaluation:
        ev = resp.evaluation
        tbl2 = Table(box=box.SIMPLE, title="Evaluation Metrics (Layer 5)")
        tbl2.add_column("Metric")
        tbl2.add_column("Score", justify="right")
        for metric, val in [
            ("Faithfulness", ev.faithfulness),
            ("Answer Relevance", ev.answer_relevance),
            ("Context Precision", ev.context_precision),
            ("Context Recall", ev.context_recall),
        ]:
            colour = "green" if val >= 0.7 else "yellow" if val >= 0.4 else "red"
            tbl2.add_row(metric, f"[{colour}]{val:.4f}[/]")
        console.print(tbl2)

        lat = Table(box=box.SIMPLE, title="Layer Latencies (ms)")
        lat.add_column("Layer")
        lat.add_column("ms", justify="right")
        for layer, ms in ev.latency_ms.items():
            lat.add_row(layer, f"{ms:.1f}")
        lat.add_row("[bold]Total[/]", f"[bold]{resp.total_latency_ms:.1f}[/]")
        console.print(lat)

    console.rule("[bold cyan]Done")


if __name__ == "__main__":
    main()
