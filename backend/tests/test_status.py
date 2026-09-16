"""
Tests for amendment and withdrawal status tracking (Phase 7).

Covers:
  - status_tracker.get_status() returns correct curated data for all demo standards
  - GET /api/v1/standards/{standard_no}/status returns expected schema
  - Unknown standard_no → 404
  - /ask response for a superseded standard includes a non-empty warnings list

Phase 0 stub: test skeletons only — implemented in Phase 7.3.
"""
from __future__ import annotations
