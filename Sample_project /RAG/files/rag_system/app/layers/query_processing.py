"""
Layer 1 – Query Processing Layer
─────────────────────────────────
Responsibilities
  • Validate and normalise the raw query string
  • Expand the query (synonym expansion, HyDE optional)
  • Return a ProcessedQuery ready for the retrieval layer
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class ProcessedQuery:
    original: str
    normalized: str
    expanded_variants: list[str] = field(default_factory=list)
    processing_ms: float = 0.0

    @property
    def all_variants(self) -> list[str]:
        """Return all query variants including the normalised original."""
        return [self.normalized] + [v for v in self.expanded_variants if v != self.normalized]


class QueryProcessor:
    """
    Cleans, normalises, and optionally expands an incoming query.

    Expansion strategy (lightweight, no external calls):
    - Lower-case canonical form
    - Stop-word question prefix removal
    - Duplicate-token variant
    Additional expansion can be layered in (e.g. LLM-based HyDE) by
    calling `add_hyde_variant()` after construction.
    """

    _QUESTION_PREFIXES = re.compile(
        r"^(what is|what are|who is|who are|how do|how does|"
        r"why is|why are|when did|where is|tell me about|explain)\s+",
        re.IGNORECASE,
    )
    _WHITESPACE = re.compile(r"\s+")

    def process(self, raw_query: str) -> ProcessedQuery:
        t0 = time.perf_counter()

        if not raw_query or not raw_query.strip():
            raise ValueError("Query must not be empty.")

        normalized = self._normalize(raw_query)
        variants = self._expand(normalized)

        pq = ProcessedQuery(
            original=raw_query,
            normalized=normalized,
            expanded_variants=variants,
            processing_ms=(time.perf_counter() - t0) * 1_000,
        )
        logger.debug(
            "QueryProcessor | normalized='{}' | variants={}",
            pq.normalized,
            pq.expanded_variants,
        )
        return pq

    # ── private ───────────────────────────────────────────────────────────────

    def _normalize(self, text: str) -> str:
        text = text.strip()
        text = self._WHITESPACE.sub(" ", text)
        # Remove trailing punctuation that adds no semantic value
        text = text.rstrip("?.!")
        return text

    def _expand(self, normalized: str) -> list[str]:
        variants: list[str] = []

        # Strip question prefix to produce a keyword-style variant
        stripped = self._QUESTION_PREFIXES.sub("", normalized).strip()
        if stripped and stripped.lower() != normalized.lower():
            variants.append(stripped)

        return variants
