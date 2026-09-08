"""POST /api/gap-check"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import GapCheckRequest, GapCheckResponse, ApplicableStandard, GapItem
from app.services.gap_check_service import run_gap_check
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/gap-check", response_model=GapCheckResponse)
def gap_check(request: GapCheckRequest) -> GapCheckResponse:
    vector_store = get_vector_store()
    if vector_store.document_count == 0:
        raise HTTPException(
            status_code=503,
            detail="Vector index is empty. Please run ingestion first (python ingest.py).",
        )

    result = run_gap_check(request.product_description)

    return GapCheckResponse(
        applicable_standards=[ApplicableStandard(**s) for s in result["applicable_standards"]],
        gaps=[GapItem(**g) for g in result["gaps"]],
        mode=result["mode"],
    )
