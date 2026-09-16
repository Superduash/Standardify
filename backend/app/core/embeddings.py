"""
Standardify — BGE-M3 embedding singleton wrapper.

Loads BAAI/bge-m3 exactly ONCE at process startup (not per-request).
Uses fp16 when a CUDA GPU is available, falls back to CPU fp32.

Exposes:
  embed_query(text: str) -> list[float]
  embed_batch(texts: list[str]) -> list[list[float]]

All embedding calls in the codebase go through this module — no other
file may instantiate a model directly (Golden Rule #3).

Phase 0 stub: no logic yet — implemented in Phase 2.1.
"""
from __future__ import annotations
