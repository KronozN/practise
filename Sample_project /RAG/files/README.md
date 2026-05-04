# RAG System

A production-ready **Retrieval-Augmented Generation** system built in Python, organised as five clean, independently-testable layers.

```
Query Processing → Vector Retrieval → Re-ranking → Generation → Evaluation
```

---

## Tech Stack

| Component | Library |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Vector store | ChromaDB (persistent) |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| Re-ranking | CrossEncoder (`ms-marco-MiniLM-L-6-v2`) |
| LLM | Any OpenAI-compatible API |

---

## Project Structure

```
rag_system/
├── main.py                    # Uvicorn entry point
├── cli_demo.py                # End-to-end smoke test (no server needed)
├── requirements.txt
├── .env.example               # Copy to .env and configure
│
├── config/
│   └── settings.py            # Pydantic-settings config
│
├── app/
│   ├── pipeline.py            # Orchestrator — wires all 5 layers
│   │
│   ├── layers/
│   │   ├── query_processing.py   # Layer 1
│   │   ├── vector_retrieval.py   # Layer 2
│   │   ├── reranking.py          # Layer 3
│   │   ├── generation.py         # Layer 4
│   │   └── evaluation.py         # Layer 5
│   │
│   ├── api/
│   │   └── routes.py          # FastAPI router
│   │
│   └── models/
│       └── schemas.py         # Pydantic request/response models
│
└── tests/
    └── test_layers.py         # Unit tests for all 5 layers
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
```

### 3a. Run the API server

```bash
python main.py
# → http://localhost:8000/docs  (Swagger UI)
```

### 3b. Run the CLI demo (no server required)

```bash
python cli_demo.py
```

### 4. Run tests

```bash
pytest tests/ -v
```

---

## API Reference

### `POST /api/v1/ingest`

Index documents into the vector store.

```json
{
  "documents": ["Text chunk one", "Text chunk two"],
  "metadatas": [{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
}
```

### `POST /api/v1/query`

Run the full 5-layer RAG pipeline.

```json
{
  "query": "How does cross-encoder re-ranking work?",
  "top_k_retrieval": 20,
  "top_k_rerank": 5,
  "include_evaluation": true
}
```

**Response:**

```json
{
  "query": "…",
  "answer": "…",
  "retrieved_chunks": […],
  "reranked_chunks": […],
  "evaluation": {
    "faithfulness": 0.87,
    "answer_relevance": 0.91,
    "context_precision": 0.78,
    "context_recall": 0.83,
    "latency_ms": {
      "query_processing": 0.4,
      "retrieval": 12.1,
      "reranking": 45.3,
      "generation": 1203.7,
      "evaluation": 38.2
    }
  },
  "total_latency_ms": 1302.1
}
```

### `GET /api/v1/collection/stats`
### `DELETE /api/v1/collection`

---

## Layer Details

### Layer 1 – Query Processing (`query_processing.py`)
- Normalises whitespace, strips trailing punctuation
- Expands the query by stripping question prefixes to generate a keyword variant
- Returns a `ProcessedQuery` with all variants for multi-vector retrieval

### Layer 2 – Vector Retrieval (`vector_retrieval.py`)
- Embeds documents with `SentenceTransformer` at ingest time
- Averages embeddings across query variants for richer query vectors
- Queries ChromaDB with cosine similarity, returns top-K `RetrievedChunk`s

### Layer 3 – Re-ranking (`reranking.py`)
- Scores every (query, passage) pair with `CrossEncoder`
- Sorts by rerank score, returns top-K `RerankResult`s
- CrossEncoder achieves ~15-20% better ranking than bi-encoder cosine alone

### Layer 4 – Generation (`generation.py`)
- Builds a numbered context prompt from the re-ranked chunks
- Calls an OpenAI-compatible LLM with a grounding system prompt
- Returns the answer + token usage

### Layer 5 – Evaluation (`evaluation.py`)
- **Faithfulness**: fraction of answer sentences semantically entailed by context (embedding cosine ≥ 0.45)
- **Answer Relevance**: cosine similarity between query and answer embeddings
- **Context Precision**: mean sigmoid-normalised rerank score
- **Context Recall**: token overlap between answer and context

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `LLM_API_KEY` | — | API key |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformers model |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | CrossEncoder model |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB persistence path |
| `TOP_K_RETRIEVAL` | `20` | Candidates fetched from vector DB |
| `TOP_K_RERANK` | `5` | Chunks passed to generation |
| `MAX_TOKENS` | `1024` | LLM max output tokens |
| `TEMPERATURE` | `0.2` | LLM temperature |
