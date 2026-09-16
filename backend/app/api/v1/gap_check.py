"""
Standardify — POST /api/v1/gap-check (Phase 5.5).

Evaluates a product description against applicable Indian Standards (BIS), identifies
discrete requirement gaps deterministically, and provides an executive compliance summary.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from app.core.gap_checker import run_gap_check
from app.models.schemas import GapCheckRequest, GapCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compliance Gap Checker"])


@router.post(
    "/gap-check",
    response_model=GapCheckResponse,
    summary="Evaluate product compliance gaps against Indian Standards",
    description=(
        "Accepts a product description or specification, identifies applicable BIS standards, "
        "and deterministically compares requirements to return matched and missing compliance items."
    ),
)
async def gap_check_endpoint(request: GapCheckRequest) -> GapCheckResponse:
    """
    Execute compliance gap analysis for the provided product description.
    """
    clean_desc = request.product_description.strip()
    if not clean_desc or len(clean_desc) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product description must contain at least 3 non-whitespace characters.",
        )

    try:
        result = run_gap_check(clean_desc)
        return GapCheckResponse(
            applicable_standards=result.applicable_standards,
            matched_requirements=result.matched_requirements,
            missing_requirements=result.missing_requirements,
            summary=result.summary,
            confidence=result.confidence,
        )
    except Exception as exc:
        logger.error("Error executing gap check for query '%s': %s", clean_desc[:40], exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gap analysis failed: {exc}",
        ) from exc
