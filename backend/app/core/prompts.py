"""
Standardify — Grounded Prompt Builder (Phase 3.1).

Constructs compact, evidence-grounded prompts for LLM inference.
Enforces strict adherence to retrieved BIS standard clauses without hallucination.
"""

from __future__ import annotations

from typing import Sequence
from app.models.domain import RetrievedClause


SYSTEM_PROMPT = """You are Standardify, the authoritative AI assistant for the Bureau of Indian Standards (BIS).
Your role is to answer user inquiries strictly and accurately using ONLY the provided authoritative standard clauses.

CRITICAL INSTRUCTIONS:
1. Grounding: Answer solely based on the provided evidence clauses below. Do NOT extrapolate, invent facts, or assume requirements not explicitly stated.
2. Missing Information: If the provided clauses do not contain enough information to answer the question, state:
   "Not covered in the retrieved standards."
3. Format:
   - Provide a clear, professional plain-language explanation.
   - Conclude your answer with a citation tag listing ONLY the clauses actually used, e.g.:
     [CITATIONS: IS_NUMBER::CLAUSE_NUMBER]
"""


def build_grounded_prompt(
    question: str,
    clauses: Sequence[RetrievedClause],
) -> str:
    """
    Construct a grounded prompt containing evidence clauses and user question.

    Args:
        question: User inquiry text.
        clauses: Top retrieved clauses (typically 3 clauses, up to 6 for multi-standard).

    Returns:
        str: Fully formatted prompt ready for LLM generation.
    """
    evidence_blocks: list[str] = []

    for idx, item in enumerate(clauses, start=1):
        std_no = item.standard_no
        cl_no = item.clause_no or "N/A"
        page = item.page_no
        title = item.section_title or item.document_title or "General"

        block = (
            f"[Evidence {idx}] Standard: {std_no} | Clause: {cl_no} | Page: {page} | Title: {title}\n"
            f"{item.text.strip()}"
        )
        evidence_blocks.append(block)

    joined_evidence = "\n\n".join(evidence_blocks)

    user_content = (
        f"EVIDENCE CLAUSES:\n"
        f"----------------------------------------\n"
        f"{joined_evidence}\n"
        f"----------------------------------------\n\n"
        f"USER QUESTION: {question.strip()}\n\n"
        f"ANSWER:"
    )

    return f"{SYSTEM_PROMPT}\n\n{user_content}"
