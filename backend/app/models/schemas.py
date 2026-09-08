"""
Standardify — Pydantic request/response schemas for every API route.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class Citation(BaseModel):
    standard_no: str
    title: str
    clause_no: Optional[str] = None
    page: Optional[int] = None
    chunk_text: Optional[str] = None


# ── /api/query ────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: Literal["high", "medium", "low"]
    mode: Literal["groq", "gemini", "extractive", "no_match"]


# ── /api/gap-check ────────────────────────────────────────────────────────────

class GapCheckRequest(BaseModel):
    product_description: str = Field(..., min_length=10, max_length=5000)


class ApplicableStandard(BaseModel):
    standard_no: str
    title: str
    similarity_score: float
    matched_clauses: list[str]


class GapItem(BaseModel):
    standard_no: str
    clause_no: str
    description: str


class GapCheckResponse(BaseModel):
    applicable_standards: list[ApplicableStandard]
    gaps: list[GapItem]
    mode: Literal["groq", "gemini", "extractive", "no_match"]


# ── /api/search ───────────────────────────────────────────────────────────────

class SearchResultItem(BaseModel):
    standard_no: str
    title: str
    clause_no: Optional[str] = None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int


# ── /api/graph ────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    standard_no: str
    title: str
    category: str
    year: int


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    label: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphEdge]


# ── /api/health ───────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    index_loaded: bool
    llm_available: bool
    llm_mode: Literal["groq", "gemini", "extractive"]
    document_count: int
