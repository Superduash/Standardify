"""GET /api/health"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.services.vector_store import get_vector_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    vs = get_vector_store()
    doc_count = vs.document_count

    # Determine available LLM mode
    if settings.groq_api_key:
        llm_mode = "groq"
    elif settings.gemini_api_key:
        llm_mode = "gemini"
    else:
        llm_mode = "extractive"

    llm_available = llm_mode in ("groq", "gemini")

    return HealthResponse(
        status="ok",
        index_loaded=doc_count > 0,
        llm_available=llm_available,
        llm_mode=llm_mode,
        document_count=doc_count,
    )
