"""
Standardify — Retrieval Confidence Scoring Formula.

Evaluates evidence sufficiency and reliability across retrieved standard clauses.

Scoring Formula and Thresholds:
  1. Primary Signal (Weight: Top-1 Score):
     The similarity score of the highest-ranked retrieved clause (top-1) serves
     as the foundational evidence baseline.

  2. Cross-Clause Consensus Agreement Bonus:
     - If >= 2 chunks in the top results originate from the same standard: +0.05 bonus.
     - If >= 3 chunks originate from the same standard: +0.10 bonus.
     - Total score is capped at 1.0.

  3. Qualitative Tiers:
     - High Confidence:   score >= 0.70 (Strong, corroborated evidence).
     - Medium Confidence: 0.50 <= score < 0.70 (Moderate evidence, single strong match).
     - Low Confidence:    score < 0.50 (Weak or ambiguous evidence).

  4. Confidence Floor & Evidence Decision:
     If the calculated score is strictly below `settings.confidence_floor` (default: 0.35),
     or if the retrieved clause list is empty, `evidence_found` is forced to `False`.
"""

from __future__ import annotations

from typing import Sequence

from app.config import settings
from app.models.domain import ConfidenceResult, RetrievedClause

# Explicit threshold constants
HIGH_CONFIDENCE_THRESHOLD: float = 0.70
MEDIUM_CONFIDENCE_THRESHOLD: float = 0.50


def score(retrieved_clauses: Sequence[RetrievedClause]) -> ConfidenceResult:
    """
    Compute evidence confidence evaluation for a retrieved clause set.

    Args:
        retrieved_clauses: Sequence of ranked RetrievedClause items from hybrid retrieval.

    Returns:
        ConfidenceResult: Structured evaluation with numeric value, qualitative label,
                          and evidence_found boolean decision.
    """
    if not retrieved_clauses:
        return ConfidenceResult(
            value=0.0,
            label="low",
            evidence_found=False,
            top_similarity=0.0,
            agreement_count=0,
        )

    # 1. Top-1 primary relevance signal
    top_clause = retrieved_clauses[0]
    top_similarity = max(0.0, min(1.0, float(top_clause.similarity_score)))
    top_standard = top_clause.standard_no

    # 2. Compute standard consensus agreement count across top candidates
    matching_standards = [
        c for c in retrieved_clauses
        if c.standard_no == top_standard and c.standard_no != "UNKNOWN"
    ]
    agreement_count = len(matching_standards)

    # Apply agreement bonus
    agreement_bonus = 0.0
    if agreement_count >= 3:
        agreement_bonus = 0.10
    elif agreement_count >= 2:
        agreement_bonus = 0.05

    final_score = min(1.0, top_similarity + agreement_bonus)
    final_score = round(final_score, 4)

    # 3. Determine qualitative label
    if final_score >= HIGH_CONFIDENCE_THRESHOLD:
        label = "high"
    elif final_score >= MEDIUM_CONFIDENCE_THRESHOLD:
        label = "medium"
    else:
        label = "low"

    # 4. Enforce confidence floor
    evidence_found = bool(final_score >= settings.confidence_floor)

    return ConfidenceResult(
        value=final_score,
        label=label,
        evidence_found=evidence_found,
        top_similarity=top_similarity,
        agreement_count=agreement_count,
    )
