"""
Standardify — ONE-TIME offline LLM-assisted requirement checklist extractor.

For each of the 8–12 demo standards, makes EXACTLY ONE LLM call asking
it to extract a structured list of discrete, checkable requirements from
that standard's clauses. Results are cached permanently to
data/requirements_cache.json keyed by standard_no.

This script runs ONLY during ingestion (never at request time). It is
idempotent — safe to re-run; skips any standard_no already present in
the cache file.

Exposes:
  extract_requirements(standard_no: str, clauses: list[Clause]) -> list[Requirement]
    Requirement: { clause_no, text }  (short, discrete, checkable)

Phase 0 stub: no logic yet — implemented in Phase 5.1.
"""
from __future__ import annotations
