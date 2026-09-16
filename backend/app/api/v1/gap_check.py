"""
Standardify — POST /api/v1/gap-check

Accepts a product description, identifies applicable BIS standards,
compares the description against cached requirement checklists, and
returns matched/missing requirements with an optional LLM summary.

Phase 0 stub: route not yet implemented — wired in Phase 5.5.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
