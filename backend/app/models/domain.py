"""
Standardify — Internal domain dataclasses (not exposed via API directly).

These are the internal representations that flow between the ingestion
pipeline and the core retrieval/scoring layers.

Classes (added per-phase):
  Phase 1.3 — StandardMeta, Clause (with standard_no, clause_no, page_no, title)
  Phase 2.3 — RetrievedClause (Clause + similarity_score)
  Phase 2.4 — ConfidenceResult (value, label, evidence_found)
  Phase 3.2 — LLMResult (text, provider_used, latency_ms), LLMUnavailableError
  Phase 7.1 — StatusInfo (status, superseded_by, last_amended_date)

Phase 0 stub: placeholder comment blocks only — dataclasses added per-phase.
"""
from __future__ import annotations
