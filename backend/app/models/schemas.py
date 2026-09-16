"""
Standardify — ALL Pydantic request/response models for every API endpoint.

Every route in app/api/v1/ uses models defined here — never a bare dict.
Models are added incrementally as each phase implements its endpoint.

Sections:
  Phase 0.3 — HealthResponse, QuotaResponse
  Phase 3.4 — CitedStandard, AskRequest, AskResponse
  Phase 5.5 — GapCheckRequest, GapCheckResponse
  Phase 6.4 — GraphResponse, GraphNode, GraphEdge
  Phase 7.3 — StatusResponse
  Phase 8.1 — SearchRequest, SearchResponse, SearchResult
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ── Phase 0.3: Health & Quota Schemas ─────────────────────────────────────────

class HealthResponse(BaseModel):
    """Liveness and readiness health check response."""

    status: str = Field(default="ok", description="Application health status")


class QuotaResponse(BaseModel):
    """LLM provider daily quota usage and cache metrics response."""

    status: str = Field(default="ok", description="Health status")
    groq_calls_today: int = Field(
        default=0,
        description="Number of Groq API calls made today",
    )
    gemini_calls_today: int = Field(
        default=0,
        description="Number of Gemini API calls made today",
    )
    cache_hits_today: int = Field(
        default=0,
        description="Number of requests served via exact/semantic cache today",
    )


# ── Phase 3.4: Ask & Citation Schemas ─────────────────────────────────────────

class CitedStandard(BaseModel):
    """Authoritative standard clause citation supporting a generated answer."""

    standard_no: str = Field(..., description="Indian Standard identifier (e.g. 'IS 9001:2025')")
    clause_no: str = Field(..., description="Clause number (e.g. '4.1', '5.2')")
    page: int = Field(..., description="1-indexed source document page number")
    title: str = Field(..., description="Section or document title of the clause")


class AskRequest(BaseModel):
    """Inquiry request payload for standard compliance and Q&A."""

    question: str = Field(
        ...,
        min_length=2,
        description="Natural language question about Indian Standards (BIS)",
        examples=["What are the drop test requirements for plastic water bottles?"],
    )


class AskResponse(BaseModel):
    """Grounded Q&A answer response with full citations and confidence."""

    answer: str = Field(..., description="Authoritative plain-language answer grounded in evidence")
    evidence_found: bool = Field(..., description="True if sufficient evidence was found in retrieved standards")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Numerical confidence score between 0.0 and 1.0")
    confidence_label: Literal["high", "medium", "low"] = Field(..., description="Qualitative confidence rating")
    citations: List[CitedStandard] = Field(default_factory=list, description="List of authoritative citations referenced")
    warnings: List[str] = Field(default_factory=list, description="Amendment or lifecycle status warnings")
    provider_used: Literal["groq", "gemini", "cache", "none"] = Field(..., description="Inference source or cache status")
    latency_ms: int = Field(..., ge=0, description="End-to-end processing latency in milliseconds")
