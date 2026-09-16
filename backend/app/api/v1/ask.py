"""
Standardify — POST /api/v1/ask

Receives a natural-language question, runs hybrid retrieval, scores
confidence, checks the cache, calls the LLM if needed, injects
amendment/withdrawal warnings for cited standards, and returns a
fully-grounded, cited answer.

Phase 0 stub: route not yet implemented — wired in Phase 3.4.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
