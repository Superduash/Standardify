"""
Standardify — GET /api/v1/standards/search
              GET /api/v1/standards/{standard_no}
              GET /api/v1/standards/{standard_no}/status

Provides keyword + semantic standard search (SQLite FTS5 + BGE-M3),
individual standard detail, and amendment/withdrawal status lookups
from the registry.db SQLite database.

Phase 0 stub: routes not yet implemented — wired in Phases 7.3 and 8.1.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
