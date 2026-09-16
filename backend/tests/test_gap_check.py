"""
End-to-end tests for POST /api/v1/gap-check (Phase 5).

Covers:
  - Demo product description returns correct applicable_standards
  - Deliberately-incomplete product description has non-empty missing_requirements
  - Same product description asked twice results in exactly one LLM call (cache)
  - Core gap logic (5.3) makes zero LLM calls

Phase 0 stub: test skeletons only — implemented in Phase 5.5.
"""
from __future__ import annotations
