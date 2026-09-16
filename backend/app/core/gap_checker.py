"""
Standardify — Compliance gap-check business logic.

Exposes:
  find_applicable_standards(description: str) -> list[str]
    Reuses app/core/retrieval.py (no new tech) — aggregates clause-level
    hits to standard-level and returns the top 1–2 matching standard_no values.

  check_gaps(description, standard_nos) -> GapResult(matched, missing)
    Deterministic, no LLM call at request time. Compares description text
    against the pre-cached requirement checklist (data/requirements_cache.json)
    for each applicable standard using embedding similarity per requirement item.
    "matched" if similarity ≥ threshold, else "missing".

Phase 0 stub: no logic yet — implemented in Phases 5.2 and 5.3.
"""
from __future__ import annotations
