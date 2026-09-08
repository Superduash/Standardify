"""
Standardify — Gap Check Service.

1. Embeds the product description.
2. Retrieves top-k relevant standard chunks from Chroma.
3. Groups chunks by standard_no to find applicable standards.
4. For each applicable standard, uses LLM (or extractive fallback) to identify
   which clauses the product description does NOT address.
5. Returns applicable_standards[] + gaps[].
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any

from app.core.config import get_settings
from app.models.schemas import ApplicableStandard, GapItem
from app.services.embeddings_service import get_embeddings_service
from app.services.llm_service import generate_answer, _try_groq, _try_gemini, _build_citations
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def _gap_prompt(product_description: str, standard_no: str, clauses_text: str) -> str:
    return f"""You are a BIS compliance expert.

A manufacturer describes their product as follows:
\"\"\"
{product_description}
\"\"\"

Below are the key clauses from {standard_no}:
\"\"\"
{clauses_text}
\"\"\"

List only the clauses that the product description does NOT clearly address or satisfy.
Format your response as a numbered list of gaps, e.g.:
1. Clause 4.2 — [brief reason why it is not addressed]
2. Clause 5.1 — [brief reason]

If all clauses appear to be addressed, respond with "No gaps identified."
"""


def _extract_gaps_from_text(gap_text: str, standard_no: str) -> list[GapItem]:
    """Parse numbered list from LLM response into GapItem objects."""
    gaps: list[GapItem] = []
    pattern = re.compile(r"^\s*\d+\.\s*(Clause\s+[\d.]+(?:\.\d+)*)\s*[—\-–]\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    for match in pattern.finditer(gap_text):
        clause = match.group(1).strip()
        description = match.group(2).strip()
        gaps.append(GapItem(standard_no=standard_no, clause_no=clause, description=description))
    return gaps


def _extractive_gaps(chunks: list[dict[str, Any]], standard_no: str) -> list[GapItem]:
    """Fallback: list matched clause identifiers as potential gaps (no fabrication)."""
    gaps: list[GapItem] = []
    for chunk in chunks[:3]:
        meta = chunk.get("metadata", {})
        clause = meta.get("clause_no", "")
        if clause:
            gaps.append(
                GapItem(
                    standard_no=standard_no,
                    clause_no=clause,
                    description="[AI unavailable — clause listed for manual review]",
                )
            )
    return gaps


def run_gap_check(product_description: str) -> dict[str, Any]:
    """
    Main entry point.
    Returns: { applicable_standards, gaps, mode }
    """
    settings = get_settings()
    emb_service = get_embeddings_service()
    vector_store = get_vector_store()

    # 1. Embed the product description
    query_embedding = emb_service.encode_single(product_description)

    # 2. Retrieve top chunks
    chunks = vector_store.query(query_embedding, top_k=settings.top_k * 2)

    # 3. Filter by threshold
    threshold = settings.similarity_threshold
    usable = [c for c in chunks if c.get("score", 0.0) >= threshold]

    if not usable:
        return {
            "applicable_standards": [],
            "gaps": [],
            "mode": "no_match",
        }

    # 4. Group by standard
    by_standard: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in usable:
        std_no = chunk.get("metadata", {}).get("standard_no", "Unknown")
        by_standard[std_no].append(chunk)

    # 5. Build applicable standards list
    applicable: list[ApplicableStandard] = []
    for std_no, std_chunks in by_standard.items():
        avg_score = sum(c.get("score", 0.0) for c in std_chunks) / len(std_chunks)
        matched_clauses = list(
            dict.fromkeys(  # deduplicate preserving order
                c.get("metadata", {}).get("clause_no", "") for c in std_chunks
                if c.get("metadata", {}).get("clause_no")
            )
        )
        title = std_chunks[0].get("metadata", {}).get("title", "")
        applicable.append(
            ApplicableStandard(
                standard_no=std_no,
                title=title,
                similarity_score=round(avg_score, 4),
                matched_clauses=matched_clauses,
            )
        )

    # Sort by score descending
    applicable.sort(key=lambda x: x.similarity_score, reverse=True)

    # 6. Gap analysis for top 3 applicable standards
    all_gaps: list[GapItem] = []
    mode: str = "extractive"

    for std in applicable[:3]:
        std_chunks = by_standard[std.standard_no]
        clauses_text = "\n\n".join(
            f"{c.get('metadata', {}).get('clause_no', 'Clause')}: {c.get('document', '')[:400]}"
            for c in std_chunks
        )
        prompt = _gap_prompt(product_description, std.standard_no, clauses_text)

        gap_text: str | None = _try_groq(prompt)
        if gap_text:
            mode = "groq"
        else:
            gap_text = _try_gemini(prompt)
            if gap_text:
                mode = "gemini"

        if gap_text and "no gaps identified" not in gap_text.lower():
            parsed = _extract_gaps_from_text(gap_text, std.standard_no)
            if parsed:
                all_gaps.extend(parsed)
            else:
                # LLM responded but couldn't be parsed — include raw as single gap
                all_gaps.append(
                    GapItem(
                        standard_no=std.standard_no,
                        clause_no="General",
                        description=gap_text[:300],
                    )
                )
        elif not gap_text:
            # Extractive fallback — list clause IDs for manual review
            all_gaps.extend(_extractive_gaps(std_chunks, std.standard_no))

    return {
        "applicable_standards": [s.model_dump() for s in applicable],
        "gaps": [g.model_dump() for g in all_gaps],
        "mode": mode,
    }
