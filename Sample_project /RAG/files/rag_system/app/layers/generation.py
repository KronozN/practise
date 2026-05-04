"""
Layer 4 – Generation Layer
───────────────────────────
Responsibilities
  • Build a grounded prompt from the re-ranked context chunks
  • Call an OpenAI-compatible LLM endpoint
  • Return the generated answer and token usage
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from openai import OpenAI
from loguru import logger

from config.settings import get_settings
from app.models.schemas import RerankResult


SYSTEM_PROMPT = """\
You are a precise and helpful assistant. Answer the user's question using ONLY
the provided context passages. If the context does not contain enough information
to answer fully, say so clearly. Do not fabricate facts.

Format your answer in clear, well-structured prose. Cite context passage numbers
(e.g. [1], [2]) where applicable."""


@dataclass
class GenerationResult:
    answer: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class Generator:
    """Calls an OpenAI-compatible LLM with a RAG prompt."""

    def __init__(self) -> None:
        cfg = get_settings()
        self._client = OpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)
        self._model = cfg.llm_model
        self._max_tokens = cfg.max_tokens
        self._temperature = cfg.temperature
        logger.info("Generator ready → model={}", self._model)

    # ── public API ────────────────────────────────────────────────────────────

    def generate(
        self,
        query: str,
        context_chunks: list[RerankResult],
    ) -> GenerationResult:
        """Generate an answer grounded in the provided context chunks."""
        t0 = time.perf_counter()

        user_message = self._build_prompt(query, context_chunks)
        logger.debug("Calling LLM | model={} | context_chunks={}", self._model, len(context_chunks))

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        answer = response.choices[0].message.content or ""
        usage = response.usage

        result = GenerationResult(
            answer=answer,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=(time.perf_counter() - t0) * 1_000,
        )
        logger.info(
            "Generation complete | {:.1f} ms | {} prompt + {} completion tokens",
            result.latency_ms, result.prompt_tokens, result.completion_tokens,
        )
        return result

    # ── private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(query: str, chunks: list[RerankResult]) -> str:
        context_block = "\n\n".join(
            f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(chunks)
        )
        return (
            f"CONTEXT PASSAGES:\n{context_block}\n\n"
            f"QUESTION: {query}\n\n"
            "Answer based solely on the context above."
        )
