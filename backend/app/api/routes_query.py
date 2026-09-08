"""POST /api/query"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.models.schemas import QueryRequest, QueryResponse
from app.services.embeddings_service import get_embeddings_service
from app.services.llm_service import generate_answer
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_standards(request: QueryRequest) -> QueryResponse:
    settings = get_settings()
    emb_service = get_embeddings_service()
    vector_store = get_vector_store()

    if vector_store.document_count == 0:
        raise HTTPException(
            status_code=503,
            detail="Vector index is empty. Please run ingestion first (python ingest.py).",
        )

    query_embedding = emb_service.encode_single(request.question)
    chunks = vector_store.query(query_embedding, top_k=settings.top_k)

    result = generate_answer(
        question=request.question,
        retrieved_chunks=chunks,
        similarity_threshold=settings.similarity_threshold,
    )

    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        confidence=result["confidence"],
        mode=result["mode"],
    )
