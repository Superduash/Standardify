"""
Standardify — Retrieval confidence scoring.

Exposes:
  score(retrieved_clauses) -> ConfidenceResult(value, label, evidence_found)

Formula (documented here — no buried magic numbers):
  - Top-1 similarity score is weighted most heavily.
  - Small additive bonus if ≥2 chunks agree on the same standard_no.
  - Any score below settings.CONFIDENCE_FLOOR forces evidence_found=False
    regardless of the other components.

Labels: value ≥ 0.70 → "high", ≥ 0.45 → "medium", else → "low".
evidence_found=False skips the LLM call entirely in /ask.

Phase 0 stub: no logic yet — implemented in Phase 2.4.
"""
from __future__ import annotations
