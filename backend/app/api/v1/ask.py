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


def _detect_and_retrieve_multi_standard(
    question: str,
    initial_clauses: List[RetrievedClause],
) -> List[RetrievedClause]:
    """
    Evaluate multi-standard query heuristic and execute targeted per-standard retrieval.

    Triggered when top retrieval candidates span >= 2 distinct standards with comparable relevance.
    """
    if len(initial_clauses) < 2:
        return initial_clauses[:3]

    # Collect distinct standards from initial retrieval
    distinct_standards: list[str] = []
    for c in initial_clauses:
        if c.standard_no != "UNKNOWN" and c.standard_no not in distinct_standards:
            distinct_standards.append(c.standard_no)

    if len(distinct_standards) >= 2:
        top_std1 = distinct_standards[0]
        top_std2 = distinct_standards[1]

        score1 = next((c.similarity_score for c in initial_clauses if c.standard_no == top_std1), 0.0)
        score2 = next((c.similarity_score for c in initial_clauses if c.standard_no == top_std2), 0.0)

        # If secondary standard relevance is reasonably close to primary (delta <= 0.20)
        if abs(score1 - score2) <= 0.20:
            logger.info("Multi-standard reasoning triggered for '%s' and '%s'", top_std1, top_std2)
            clauses_std1 = retrieve(question, top_k=3, standard_filter=top_std1)
            clauses_std2 = retrieve(question, top_k=3, standard_filter=top_std2)

            combined = clauses_std1 + clauses_std2
            combined.sort(key=lambda x: x.similarity_score, reverse=True)
            return combined

    return initial_clauses[:3]


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Answer question grounded in BIS standards",
)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Grounded question-answering pipeline.

    Flow:
      1. Embed question and execute hybrid dense + BM25 retrieval.
      2. Evaluate evidence confidence (forces no-evidence return if below confidence floor).
      3. Perform exact and semantic cache check (serves hit without LLM call).
      4. If cache miss, generate grounded answer via Groq with Gemini fallback.
      5. Assemble response with authoritative citations and confidence rating.
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

    # 3. Quota-Aware Cache Lookup (Exact match -> Semantic match)
    cached_result = get_exact_cache(question)
    if cached_result is None:
        cached_result = get_semantic_cache(question, query_vector)

    citations = _build_citations(candidate_clauses)

    if cached_result is not None:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return AskResponse(
            answer=cached_result.text,
            evidence_found=True,
            confidence=confidence_result.value,
            confidence_label=confidence_result.label,
            citations=citations,
            warnings=[],
            provider_used="cache",
            latency_ms=elapsed_ms,
        )

    # 4. LLM Generation
    prompt = build_grounded_prompt(question, candidate_clauses)

    try:
        llm_result = generate_answer(prompt)
    except LLMUnavailableError as exc:
        logger.error("LLM generation failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI inference providers (Groq and Gemini) are currently unavailable.",
        ) from exc

    # 5. Store in Cache for Subsequent Runs
    set_cache(question, query_vector, llm_result)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return AskResponse(
        answer=llm_result.text,
        evidence_found=True,
        confidence=confidence_result.value,
        confidence_label=confidence_result.label,
        citations=citations,
        warnings=[],
        provider_used=llm_result.provider_used,  # type: ignore[arg-type]
        latency_ms=elapsed_ms,
    )
