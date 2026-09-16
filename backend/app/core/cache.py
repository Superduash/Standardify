"""
Standardify — Quota-Aware Multi-Tier Cache (Phase 3.3).

Implements exact-match string hashing and semantic cosine near-duplicate
caching using diskcache. Preserves API rate limits and maintains daily
provider quota telemetry.
"""

from __future__ import annotations

from datetime import date
import hashlib
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import diskcache

from app.config import settings
from app.models.domain import LLMResult

logger = logging.getLogger(__name__)

CACHE_DIR = Path("./data/cache")
SEMANTIC_SIMILARITY_THRESHOLD = 0.92


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class QuotaAwareCache:
    """
    Persistent diskcache managing exact and semantic near-duplicate answer caching.
    """

    _instance: Optional[QuotaAwareCache] = None

    def __new__(cls) -> QuotaAwareCache:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_cache()
        return cls._instance

    def _init_cache(self) -> None:
        """Initialize diskcache storage."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.cache = diskcache.Cache(str(CACHE_DIR))
        self.ttl = settings.cache_ttl_seconds
        logger.info("Initialized diskcache at '%s' (TTL=%ds)", CACHE_DIR, self.ttl)

    def _get_exact_key(self, question: str) -> str:
        """Normalize question text and return MD5 hash key."""
        normalized = " ".join(question.strip().lower().split())
        return "exact_" + hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def get_exact(self, question: str) -> Optional[LLMResult]:
        """
        Check exact-match cache for the query string.

        Args:
            question: Normalized user query.

        Returns:
            Optional[LLMResult]: Cached result on hit, or None on miss.
        """
        key = self._get_exact_key(question)
        cached_data = self.cache.get(key)
        if cached_data is not None:
            self.record_cache_hit()
            logger.info("Exact cache HIT for query '%s'", question[:40])
            return LLMResult(
                text=cached_data["text"],
                provider_used="cache",
                latency_ms=cached_data.get("latency_ms", 15),
                used_clause_ids=cached_data.get("used_clause_ids", []),
            )
        return None

    def get_semantic(
        self,
        question: str,
        query_embedding: list[float],
        threshold: float = SEMANTIC_SIMILARITY_THRESHOLD,
    ) -> Optional[LLMResult]:
        """
        Compare query embedding against recent cached embeddings using cosine similarity.

        Args:
            question: User inquiry text.
            query_embedding: Dense embedding vector generated for retrieval.
            threshold: Cosine similarity cutoff (default: 0.92).

        Returns:
            Optional[LLMResult]: Cached result on hit, or None on miss.
        """
        index_entries: list[dict[str, Any]] = self.cache.get("semantic_index", default=[])

        best_score = 0.0
        best_entry: Optional[dict[str, Any]] = None

        for entry in index_entries:
            cached_emb = entry.get("embedding")
            if not cached_emb:
                continue

            sim = _cosine_similarity(query_embedding, cached_emb)
            if sim > best_score:
                best_score = sim
                best_entry = entry

        if best_entry and best_score >= threshold:
            self.record_cache_hit()
            logger.info(
                "Semantic cache HIT (score=%.4f >= %.2f) for query '%s' against cached '%s'",
                best_score,
                threshold,
                question[:40],
                best_entry.get("question", "")[:40],
            )
            return LLMResult(
                text=best_entry["text"],
                provider_used="cache",
                latency_ms=best_entry.get("latency_ms", 25),
                used_clause_ids=best_entry.get("used_clause_ids", []),
            )

        return None

    def set(
        self,
        question: str,
        query_embedding: list[float],
        result: LLMResult,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store LLM output into exact and semantic cache stores.

        Args:
            question: User inquiry string.
            query_embedding: Dense vector embedding.
            result: LLMResult instance from inference.
            ttl: Time-to-live in seconds (defaults to settings.cache_ttl_seconds).
        """
        expire_time = ttl or self.ttl
        payload = {
            "text": result.text,
            "provider_used": result.provider_used,
            "latency_ms": result.latency_ms,
            "used_clause_ids": result.used_clause_ids,
            "question": question,
        }

        # 1. Store exact match
        exact_key = self._get_exact_key(question)
        self.cache.set(exact_key, payload, expire=expire_time)

        # 2. Update semantic index (retain top 100 recent queries)
        index_entries: list[dict[str, Any]] = self.cache.get("semantic_index", default=[])
        new_entry = {
            "question": question,
            "embedding": query_embedding,
            "text": result.text,
            "latency_ms": result.latency_ms,
            "used_clause_ids": result.used_clause_ids,
        }
        index_entries.append(new_entry)
        if len(index_entries) > 100:
            index_entries = index_entries[-100:]

        self.cache.set("semantic_index", index_entries, expire=expire_time)

    def record_llm_call(self, provider: str) -> None:
        """Increment daily API call count for the specified provider."""
        today_key = f"quota_{date.today().isoformat()}_{provider.lower()}"
        current = self.cache.get(today_key, default=0)
        self.cache.set(today_key, current + 1, expire=86400 * 7)

    def record_cache_hit(self) -> None:
        """Increment daily cache hit counter."""
        today_key = f"quota_{date.today().isoformat()}_cache_hits"
        current = self.cache.get(today_key, default=0)
        self.cache.set(today_key, current + 1, expire=86400 * 7)

    def get_quota_stats(self) -> Dict[str, int]:
        """Retrieve today's provider call metrics and cache hits."""
        today_str = date.today().isoformat()
        groq_key = f"quota_{today_str}_groq"
        gemini_key = f"quota_{today_str}_gemini"
        cache_key = f"quota_{today_str}_cache_hits"

        return {
            "groq_calls_today": int(self.cache.get(groq_key, default=0)),
            "gemini_calls_today": int(self.cache.get(gemini_key, default=0)),
            "cache_hits_today": int(self.cache.get(cache_key, default=0)),
        }


def get_cache() -> QuotaAwareCache:
    """Retrieve singleton QuotaAwareCache instance."""
    return QuotaAwareCache()


def get_exact_cache(question: str) -> Optional[LLMResult]:
    """Check exact match cache."""
    return get_cache().get_exact(question)


def get_semantic_cache(
    question: str,
    query_embedding: list[float],
    threshold: float = SEMANTIC_SIMILARITY_THRESHOLD,
) -> Optional[LLMResult]:
    """Check semantic near-duplicate cache."""
    return get_cache().get_semantic(question, query_embedding, threshold=threshold)


def set_cache(
    question: str,
    query_embedding: list[float],
    result: LLMResult,
    ttl: Optional[int] = None,
) -> None:
    """Write LLM result to cache."""
    get_cache().set(question, query_embedding, result, ttl=ttl)


def record_llm_call(provider: str) -> None:
    """Record LLM call in telemetry store."""
    get_cache().record_llm_call(provider)


def get_quota_stats() -> Dict[str, int]:
    """Get quota and cache telemetry."""
    return get_cache().get_quota_stats()
