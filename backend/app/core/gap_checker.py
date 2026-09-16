"""
Standardify — Compliance Gap-Check Business Logic (Phase 5).

Provides deterministic standard identification and requirement checklist verification
against cached BIS standards requirements, with optional cached LLM summary phrasing.

Exposes:
  find_applicable_standards(description: str) -> tuple[list[str], float]
  check_gaps(description: str, standard_nos: list[str], threshold: float = 0.52) -> tuple[list[dict], list[dict]]
  generate_gap_summary(description: str, applicable_standards: list[str], matched: list[dict], missing: list[dict]) -> str
  run_gap_check(description: str) -> GapCheckResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.cache import QuotaAwareCache
from app.core.embeddings import embed_batch, embed_query
from app.core.llm_client import generate_answer
from app.core.retrieval import retrieve
from app.ingestion.requirement_extractor import load_requirements_cache
from app.models.domain import LLMResult, LLMUnavailableError

logger = logging.getLogger(__name__)

# Default semantic cosine similarity threshold for requirement matching
DEFAULT_MATCH_THRESHOLD: float = 0.52

# Confidence floor for standard retrieval relevance
MIN_STANDARD_RELEVANCE: float = 0.35


@dataclass
class GapCheckResult:
    """Internal domain result for compliance gap analysis."""

    applicable_standards: List[str]
    matched_requirements: List[str]
    missing_requirements: List[str]
    summary: str
    confidence: float
    raw_matched: List[Dict[str, Any]] = field(default_factory=list)
    raw_missing: List[Dict[str, Any]] = field(default_factory=list)


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if len(vec_a) != len(vec_b) or not vec_a:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def find_applicable_standards(description: str, top_k: int = 6) -> Tuple[List[str], float]:
    """
    Identify applicable BIS standards for a product description using hybrid retrieval.
    Aggregates clause-level scores to standard-level and ranks them.
    No LLM call involved.

    Returns:
        (applicable_standards, confidence_score)
    """
    clean_desc = description.strip()
    if len(clean_desc) < 3:
        return [], 0.0

    retrieved = retrieve(clean_desc, top_k=top_k)
    if not retrieved:
        return [], 0.0

    # Aggregate scores by standard
    standard_scores: Dict[str, List[float]] = {}
    for rc in retrieved:
        std = rc.standard_no
        if std and std != "UNKNOWN":
            standard_scores.setdefault(std, []).append(rc.similarity_score)

    if not standard_scores:
        return [], 0.0

    # Score each standard by max clause score + small multi-clause bonus
    ranked: List[Tuple[str, float]] = []
    for std, scores in standard_scores.items():
        max_score = max(scores)
        # Bonus up to +0.05 for multiple relevant clauses
        clause_bonus = min(0.05, (len(scores) - 1) * 0.02)
        combined_score = min(1.0, max_score + clause_bonus)
        ranked.append((std, combined_score))

    ranked.sort(key=lambda x: x[1], reverse=True)

    top_std, top_score = ranked[0]
    if top_score < MIN_STANDARD_RELEVANCE:
        logger.info("Top standard '%s' score %.3f below floor %.3f — no match.", top_std, top_score, MIN_STANDARD_RELEVANCE)
        return [], 0.0

    # Select top 1-2 standards if second standard is also strongly relevant (>= 80% of top score)
    selected_standards: List[str] = [top_std]
    if len(ranked) > 1:
        second_std, second_score = ranked[1]
        if second_score >= MIN_STANDARD_RELEVANCE and second_score >= (top_score * 0.80):
            selected_standards.append(second_std)

    # Compute overall confidence
    confidence = round(min(1.0, top_score), 3)
    logger.info("Found %d applicable standard(s) for product: %s (confidence: %.3f)", len(selected_standards), selected_standards, confidence)
    return selected_standards, confidence


def check_gaps(
    description: str,
    standard_nos: List[str],
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Deterministic compliance requirement comparison using local BGE-M3 embeddings.
    Compares product description against pre-cached requirement checklists.
    NO LLM call.

    Returns:
        (matched_requirements, missing_requirements)
    """
    if not standard_nos or not description.strip():
        return [], []

    cache = load_requirements_cache()
    cached_standards = cache.get("standards", {})

    all_reqs: List[Dict[str, Any]] = []
    for std_no in standard_nos:
        std_reqs = cached_standards.get(std_no, [])
        for req in std_reqs:
            all_reqs.append({
                "standard_no": std_no,
                "clause_no": req.get("clause_no", "General"),
                "section_title": req.get("section_title", ""),
                "text": req.get("text", "").strip(),
            })

    if not all_reqs:
        logger.warning("No cached requirements found for standards: %s", standard_nos)
        return [], []

    # Local deterministic embedding matching
    desc_vec = embed_query(description.strip())
    req_texts = [r["text"] for r in all_reqs]
    req_vecs = embed_batch(req_texts)

    matched: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []

    for req, req_vec in zip(all_reqs, req_vecs):
        sim = _cosine_similarity(desc_vec, req_vec)
        req_entry = dict(req)
        req_entry["similarity"] = round(sim, 4)

        if sim >= threshold:
            matched.append(req_entry)
        else:
            missing.append(req_entry)

    # Sort matched by similarity descending
    matched.sort(key=lambda x: x["similarity"], reverse=True)
    # Sort missing by standard_no and clause_no
    missing.sort(key=lambda x: (x["standard_no"], str(x["clause_no"])))

    logger.info(
        "Deterministic gap check for %s: %d matched (>=%.2f), %d missing (<%.2f)",
        standard_nos, len(matched), threshold, len(missing), threshold,
    )
    return matched, missing


def format_requirement_str(req: Dict[str, Any]) -> str:
    """Format a requirement item into a traceable string representation."""
    std = req.get("standard_no", "IS")
    clause = req.get("clause_no", "General")
    text = req.get("text", "")
    return f"[{std} Clause {clause}] {text}"


def generate_gap_summary(
    description: str,
    applicable_standards: List[str],
    matched: List[Dict[str, Any]],
    missing: List[Dict[str, Any]],
) -> str:
    """
    Generate a concise executive summary of the gap analysis using cached LLM inference.
    If LLM is unavailable or cache hit occurs, returns without unneeded API calls.
    """
    if not applicable_standards:
        return "No applicable Indian Standards found for the provided product description."

    n_matched = len(matched)
    n_missing = len(missing)
    std_str = ", ".join(applicable_standards)

    # Deterministic fallback summary
    fallback_summary = (
        f"Compliance assessment against {std_str}: {n_matched} requirement(s) addressed in product specification, "
        f"{n_missing} requirement(s) missing or requiring verification."
    )

    # Check cache
    cache = QuotaAwareCache()
    cache_key = f"gap_summary:{description.strip().lower()}"
    cached_res = cache.get_exact_llm_result(cache_key)
    if cached_res:
        logger.info("Gap summary cache_hit: true (exact)")
        return cached_res.text

    logger.info("Gap summary cache_hit: false")

    # Build prompt for LLM
    matched_lines = [f"- {format_requirement_str(m)}" for m in matched[:5]] or ["(None specified)"]
    missing_lines = [f"- {format_requirement_str(m)}" for m in missing[:5]] or ["(None - all requirements addressed)"]

    prompt = (
        f"You are a BIS Standards Compliance Assessor. Provide a concise, professional 2-3 sentence executive "
        f"compliance summary for the product based on the evaluated requirements below.\n\n"
        f"APPLICABLE STANDARDS: {std_str}\n"
        f"PRODUCT DESCRIPTION: {description.strip()}\n\n"
        f"MATCHED SPECIFICATIONS ({n_matched}):\n" + "\n".join(matched_lines) + "\n\n"
        f"MISSING / UNVERIFIED REQUIREMENTS ({n_missing}):\n" + "\n".join(missing_lines) + "\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Summarize which standards apply and what specifications are satisfied.\n"
        f"2. Clearly highlight key missing parameters or tests that require laboratory verification.\n"
        f"3. Do NOT invent new requirements or change whether an item was matched/missing.\n"
        f"4. Keep the summary under 100 words."
    )

    try:
        result = generate_answer(prompt)
        summary_text = result.text.strip()
        # Save to cache
        cache.set_exact_llm_result(cache_key, LLMResult(
            text=summary_text,
            provider_used=result.provider_used,
            latency_ms=result.latency_ms,
        ))
        return summary_text
    except (LLMUnavailableError, Exception) as exc:
        logger.warning("LLM gap summary generation failed (%s), using deterministic fallback.", exc)
        return fallback_summary


def run_gap_check(
    description: str,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> GapCheckResult:
    """
    Execute end-to-end compliance gap analysis pipeline:
    1. Identify applicable standards (Phase 2 hybrid retrieval, deterministic).
    2. Load cached requirements checklist and perform local embedding cosine comparison.
    3. Calculate standard match confidence.
    4. Generate cached/fallback executive summary.
    """
    clean_desc = description.strip()
    if len(clean_desc) < 3:
        return GapCheckResult(
            applicable_standards=[],
            matched_requirements=[],
            missing_requirements=[],
            summary="Please provide a more detailed product description for compliance analysis.",
            confidence=0.0,
        )

    applicable_standards, confidence = find_applicable_standards(clean_desc)
    if not applicable_standards:
        return GapCheckResult(
            applicable_standards=[],
            matched_requirements=[],
            missing_requirements=[],
            summary="No applicable Indian Standards found for the provided product description.",
            confidence=0.0,
        )

    raw_matched, raw_missing = check_gaps(clean_desc, applicable_standards, threshold=threshold)

    matched_strs = [format_requirement_str(m) for m in raw_matched]
    missing_strs = [format_requirement_str(m) for m in raw_missing]

    summary = generate_gap_summary(clean_desc, applicable_standards, raw_matched, raw_missing)

    return GapCheckResult(
        applicable_standards=applicable_standards,
        matched_requirements=matched_strs,
        missing_requirements=missing_strs,
        summary=summary,
        confidence=confidence,
        raw_matched=raw_matched,
        raw_missing=raw_missing,
    )
