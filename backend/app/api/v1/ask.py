"""
Standardify — POST /api/v1/ask endpoint (Phase 3.4 & 3.5).

Coordinates retrieval, evidence confidence evaluation, quota-aware caching,
multi-standard reasoning, and grounded LLM answer generation.
"""

from __future__ import annotations

import logging
import time
from typing import List

from fastapi import APIRouter, HTTPException

from app.core.cache import get_exact_cache, get_semantic_cache, set_cache
from app.core.confidence import score as score_confidence
from app.core.embeddings import embed_query
from app.core.llm_client import generate_answer
from app.core.prompts import build_grounded_prompt
from app.core.retrieval import retrieve
from app.core.status_tracker import get_status_warning
from app.models.domain import LLMResult, LLMUnavailableError, RetrievedClause
from app.models.schemas import AskRequest, AskResponse, CitedStandard

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Grounded Q&A"])


def _build_citations(clauses: List[RetrievedClause]) -> List[CitedStandard]:
    """Build unique CitedStandard citation list from retrieved clauses."""
    seen = set()
    citations: list[CitedStandard] = []

    for c in clauses:
        key = (c.standard_no, c.clause_no or "N/A")
        if key not in seen and c.standard_no != "UNKNOWN":
            seen.add(key)
            citations.append(
                CitedStandard(
                    standard_no=c.standard_no,
                    clause_no=c.clause_no or "N/A",
                    page=c.page_no,
                    title=c.section_title or c.document_title or "General Requirement",
                )
            )

    return citations


def _build_warnings(citations: List[CitedStandard]) -> List[str]:
    """Check lifecycle and amendment status of cited standards and assemble warnings."""
    warnings: list[str] = []
    seen_standards = set()

    for c in citations:
        std = c.standard_no
        if std not in seen_standards:
            seen_standards.add(std)
            warn = get_status_warning(std)
            if warn:
                warnings.append(warn)

    return warnings


def _detect_and_retrieve_multi_standard(
    question: str,
    initial_clauses: List[RetrievedClause],
) -> List[RetrievedClause]:
    """
    Detect multi-standard compound queries and perform targeted separate retrievals.
    """
    if not initial_clauses:
        return []

    # Heuristic 1: check distinct standards in top-3
    top3_standards = list(dict.fromkeys(c.standard_no for c in initial_clauses[:3] if c.standard_no != "UNKNOWN"))

    if len(top3_standards) >= 2:
        std_a, std_b = top3_standards[0], top3_standards[1]
        logger.info("Multi-standard heuristic triggered for standards: %s and %s", std_a, std_b)

        # Retrieve up to 3 clauses per candidate standard
        clauses_a = retrieve(question, top_k=3, standard_filter=std_a)
        clauses_b = retrieve(question, top_k=3, standard_filter=std_b)

        combined = clauses_a + clauses_b
        return combined if combined else initial_clauses

    return initial_clauses


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask questions grounded strictly in Indian Standards (BIS)",
    description=(
        "Retrieves relevant clauses from Indian Standards, computes confidence, "
        "checks cache, and generates grounded plain-language answers with exact citations."
    ),
)
async def ask_endpoint(request: AskRequest) -> AskResponse:
    """
    Primary Q&A pipeline:
      1. Retrieve top clauses via dense semantic + BM25 hybrid search.
      2. Evaluate evidence confidence (forces no-evidence return if below confidence floor).
      3. Perform exact and semantic cache check (serves hit without LLM call).
      4. If cache miss, generate grounded answer via Groq with Gemini fallback.
      5. Assemble response with authoritative citations, status warnings, and confidence rating.
    """
    start_time = time.time()
    question = request.question.strip()

    # 1. Hybrid Retrieval & Multi-Standard Detection
    query_vector = embed_query(question)
    initial_clauses = retrieve(question, top_k=6)
    candidate_clauses = _detect_and_retrieve_multi_standard(question, initial_clauses)

    # 2. Confidence Scoring
    confidence_result = score_confidence(candidate_clauses)

    # If evidence is absent or below confidence floor, return safely without LLM call
    if not confidence_result.evidence_found:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AskResponse(
            answer="The information requested is not covered in the retrieved Indian Standards.",
            evidence_found=False,
            confidence=confidence_result.value,
            confidence_label=confidence_result.label,
            citations=[],
            warnings=[],
            provider_used="none",
            latency_ms=elapsed_ms,
        )

    # 3. Assemble citations & lifecycle status warnings
    citations = _build_citations(candidate_clauses)
    warnings = _build_warnings(citations)

    # 4. Quota-Aware Cache Lookup (Exact match -> Semantic match)
    cached_result = get_exact_cache(question)
    hit_type = "exact" if cached_result else None
    if cached_result is None:
        cached_result = get_semantic_cache(question, query_vector)
        if cached_result is not None:
            hit_type = "semantic"

    if cached_result is not None:
        logger.info("Ask API cache_hit: true (%s)", hit_type)
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AskResponse(
            answer=cached_result.text,
            evidence_found=True,
            confidence=confidence_result.value,
            confidence_label=confidence_result.label,
            citations=citations,
            warnings=warnings,
            provider_used="cache",
            latency_ms=elapsed_ms,
        )

    logger.info("Ask API cache_hit: false")


    # 5. LLM Generation
    prompt = build_grounded_prompt(question, candidate_clauses)

    try:
        llm_result = generate_answer(prompt)
    except LLMUnavailableError as exc:
        logger.error("LLM generation failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI inference providers (Groq and Gemini) are currently unavailable.",
        ) from exc

    # 6. Store in Cache for Subsequent Runs
    set_cache(question, query_vector, llm_result)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return AskResponse(
        answer=llm_result.text,
        evidence_found=True,
        confidence=confidence_result.value,
        confidence_label=confidence_result.label,
        citations=citations,
        warnings=warnings,
        provider_used=llm_result.provider_used,  # type: ignore[arg-type]
        latency_ms=elapsed_ms,
    )
