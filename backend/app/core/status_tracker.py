"""
Standardify — Amendment and withdrawal status tracker.

Reads from the SQLite registry (data/registry.db) which is populated
during ingestion (Phase 1.4) and hand-curated for the demo corpus.

Exposes:
  get_status(standard_no: str) -> StatusInfo(status, superseded_by, last_amended_date)

Used by app/api/v1/ask.py to inject warnings when a cited standard is
superseded or withdrawn (Phase 7.2).

Phase 0 stub: no logic yet — implemented in Phase 7.1.
"""
from __future__ import annotations
