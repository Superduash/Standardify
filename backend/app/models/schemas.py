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


# ── Phase 5.5: Compliance Gap Checker Schemas ────────────────────────────────

class GapCheckRequest(BaseModel):
    """Compliance gap check request payload containing product description or specs."""

    product_description: str = Field(
        ...,
        min_length=3,
        description="Detailed product description, materials, or specifications for compliance review",
        examples=["We manufacture 1-liter plastic drinking water bottles from virgin food-grade PET."],
    )


class GapCheckResponse(BaseModel):
    """Deterministic compliance gap analysis response with matched and missing requirements."""

    applicable_standards: List[str] = Field(
        ...,
        description="Indian Standards identified as applicable to the product",
    )
    matched_requirements: List[str] = Field(
        ...,
        description="Discrete technical requirements identified as satisfied or addressed in the description",
    )
    missing_requirements: List[str] = Field(
        ...,
        description="Mandatory or standard requirements not explicitly covered or missing from the description",
    )
    summary: str = Field(
        ...,
        description="Concise executive summary of compliance status and missing areas",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for applicable standard identification",
    )


# ── Phase 6.4: Standards Relationship Graph Schemas ──────────────────────────

class GraphNode(BaseModel):
    """Node in the standards relationship graph representing an Indian Standard."""

    id: str = Field(..., description="Standard number identifier (e.g. 'IS 374:2019')")
    label: str = Field(..., description="Display title or short name of the standard")
    status: str = Field(default="Active", description="Lifecycle status ('Active', 'Withdrawn', 'Superseded')")
    category: Optional[str] = Field(default=None, description="Industry or technical category")


class GraphEdge(BaseModel):
    """Directed edge in the standards relationship graph."""

    source: str = Field(..., description="Source standard identifier")
    target: str = Field(..., description="Target standard identifier")
    relation: str = Field(
        ...,
        description="Relationship type ('supersedes', 'references', 'same_category')",
    )


class GraphResponse(BaseModel):
    """Complete graph or localized subgraph network response."""

    nodes: List[GraphNode] = Field(..., description="List of graph nodes")
    edges: List[GraphEdge] = Field(..., description="List of directed relationship edges")
    total_nodes: Optional[int] = Field(default=None, description="Total nodes available in complete graph")
    total_edges: Optional[int] = Field(default=None, description="Total edges available in complete graph")


