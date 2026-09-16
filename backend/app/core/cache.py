"""
Standardify — Quota-aware diskcache layer.

Implements two-level caching before every LLM call:
  1. Exact-match cache  — normalised question hash → cached LLMResult (TTL=24h default)
  2. Semantic near-duplicate cache — cosine similarity ≥ 0.92 against cached
     question embeddings reuses a previous answer without calling the LLM.

Also maintains a per-provider call counter exposed by GET /api/v1/health/quota.

Phase 0 stub: no logic yet — implemented in Phase 3.3.
"""
from __future__ import annotations
