"""
Tests for the retrieval engine (Phase 2).

Covers:
  - golden_qa.json hit-rate ≥ 80% at top-3
  - standard_no metadata filter returns only matching standard
  - confidence.score() thresholds and evidence_found logic
  - Embedding model loads exactly once (singleton check)

Phase 0 stub: test skeletons only — implemented in Phase 2.5.
"""
from __future__ import annotations
