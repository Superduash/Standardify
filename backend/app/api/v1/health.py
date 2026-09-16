"""
Standardify — GET /api/v1/health
              GET /api/v1/health/quota

/health returns basic liveness and readiness status.
/health/quota returns today's LLM call counts and cache hits per provider so the team
can monitor quota consumption during demonstrations.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.cache import get_quota_stats
from app.models.schemas import HealthResponse, QuotaResponse

router = APIRouter(prefix="/health", tags=["Health & Status"])


@router.get("", response_model=HealthResponse, summary="Service health check")
async def get_health() -> HealthResponse:
    """
    Check application health and liveness.

    Returns:
        HealthResponse: Status object indicating 'ok'.
    """
    return HealthResponse(status="ok")


@router.get("/quota", response_model=QuotaResponse, summary="LLM quota usage check")
async def get_quota() -> QuotaResponse:
    """
    Retrieve current day's LLM provider usage counts and cache statistics.

    Returns:
        QuotaResponse: Object containing provider call metrics and cache hits.
    """
    stats = get_quota_stats()
    return QuotaResponse(
        status="ok",
        groq_calls_today=stats.get("groq_calls_today", 0),
        gemini_calls_today=stats.get("gemini_calls_today", 0),
        cache_hits_today=stats.get("cache_hits_today", 0),
    )
