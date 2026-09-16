"""
Standardify — GET /api/v1/standards/{standard_no}/status (Phase 7.3).

Provides lifecycle and amendment status tracking for Indian Standards (BIS),
verifying whether a document is Active, Superseded, Withdrawn, or Under Revision.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status

from app.core.status_tracker import get_status
from app.models.schemas import StatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/standards", tags=["Standards Status & Lifecycle"])


@router.get(
    "/{standard_no}/status",
    response_model=StatusResponse,
    summary="Get lifecycle and amendment status for an Indian Standard",
    description="Returns current lifecycle status (Active, Superseded, Withdrawn, Under Revision), successor standard, and last amended date.",
)
async def get_standard_status_endpoint(standard_no: str) -> StatusResponse:
    """
    Retrieve lifecycle and amendment status for the given standard number.
    """
    clean_std = standard_no.strip()
    if not clean_std:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Standard number parameter cannot be empty.",
        )

    info = get_status(clean_std)
    if not info:
        logger.warning("Standard status lookup failed for unknown standard: '%s'", clean_std)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{clean_std}' was not found in the BIS standards registry.",
        )

    return StatusResponse(
        standard_no=info.standard_no,
        status=info.status,
        superseded_by=info.superseded_by,
        last_amended_date=info.last_amended_date,
    )
