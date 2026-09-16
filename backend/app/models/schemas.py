"""
Standardify — ALL Pydantic request/response models for every API endpoint.

Every route in app/api/v1/ uses models defined here — never a bare dict.
Models are added incrementally as each phase implements its endpoint.

Sections (added per-phase):
  Phase 0.3 — HealthResponse, QuotaResponse
  Phase 3.4 — AskRequest, AskResponse, CitedStandard
  Phase 5.5 — GapCheckRequest, GapCheckResponse
  Phase 6.4 — GraphResponse, GraphNode, GraphEdge
  Phase 7.3 — StatusResponse
  Phase 8.1 — SearchRequest, SearchResponse, SearchResult
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Phase 0.3: Health & Quota Schemas ─────────────────────────────────────────

class HealthResponse(BaseModel):
    """Liveness and readiness health check response."""

    status: str = Field(default="ok", description="Application health status")


class QuotaResponse(BaseModel):
    """LLM provider daily quota usage response."""

    status: str = Field(default="ok", description="Health status")
    groq_calls_today: int = Field(
        default=0,
        description="Number of Groq API calls made today",
    )
    gemini_calls_today: int = Field(
        default=0,
        description="Number of Gemini API calls made today",
    )
