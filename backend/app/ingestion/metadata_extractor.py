"""
Standardify — Deterministic regex & rule-based metadata extractor.

Extracts per-chunk and document-level metadata from raw BIS standard text:
  - standard_no     (e.g. "IS 374:2019", "IS 9001:2025")
  - clause_no       (e.g. "4.2", "5.1.3")
  - section_title   (e.g. "Material Requirements")
  - document_title  (e.g. "Safety of Toys — Specification")
  - category        (mapped via curated category lookup table)
  - page_no         (preserved from 1.1/1.2)

Untaggable or incomplete chunks are flagged `needs_review=True`.
"""

from __future__ import annotations

import re
from typing import Optional

from app.models.domain import Clause, StandardMeta

# Robust regex to match BIS standard numbers
# Matches e.g. "IS 374:2019", "IS 9001:2025", "IS 1293 : 2019", "IS/IEC 60335-1", "IS 9000"
STANDARD_NO_REGEX = re.compile(
    r'\b('
    r'IS(?:\s*[\/]\s*[A-Z0-9]+)?'               # "IS" or "IS/IEC"
    r'\s+\d+(?:(?:\s*[-–]\s*\d+)*(?:\s*\(Part\s*\d+\))?)?' # e.g. "374", "9001", "60335-1"
    r'(?:\s*[:\.]\s*\d{4})?'                     # optional ":2019", ":2025"
    r')\b',
    re.IGNORECASE,
)

# Curated catalog mapping for standard demo standards (Standard No -> (Title, Category, Status))
DEMO_CATALOG: dict[str, tuple[str, str, str]] = {
    "IS 374:2019": (
        "Electric Ceiling Fans — Specification",
        "Electrical & Electronics",
        "Active",
    ),
    "IS 1293:2019": (
        "Plugs and Socket-Outlets for Household and Similar Purposes",
        "Electrical & Electronics",
        "Active",
    ),
    "IS 9000:2025": (
        "Household Electrical Appliances — Safety Specification",
        "Electrical & Electronics",
        "Active",
    ),
    "IS 9001:2025": (
        "Plastic Containers for Packaged Drinking Water — Specification",
        "Plastics & Packaging",
        "Active",
    ),
    "IS 9002:2025": (
        "Safety of Toys — Mechanical and Physical Properties",
        "Consumer Products",
        "Active",
    ),
    "IS 9003:2026": (
        "Protective Helmets for Two-Wheeler Riders — Specification",
        "Automotive & Safety",
        "Active",
    ),
    "IS 9004:2025": (
        "Packaged Food Products — Nutritional and Safety Labelling",
        "Food & Agriculture",
        "Active",
    ),
    "IS 9005:2025": (
        "Domestic Pressure Cookers — Safety and Performance",
        "Mechanical & Consumer Goods",
        "Active",
    ),
    "IS 9876:2024": (
        "Packaged Drinking Water — Quality and Labelling Specification",
        "Water & Environment",
        "Active",
    ),
    "IS 9999:2026": (
        "LED Lighting Systems for Domestic Use — Safety and Photobiological Specifications",
        "Electrical & Electronics",
        "Active",
    ),
}


def normalize_standard_no(raw_standard_no: str) -> str:
    """
    Standardize format of a detected standard identifier.

    Args:
        raw_standard_no: Raw matched string (e.g. 'is  374 : 2019').

    Returns:
        Standardized identifier string (e.g. 'IS 374:2019').
    """
    clean = " ".join(raw_standard_no.strip().split())
    # Standardize 'IS' prefix casing
    clean = re.sub(r'^(is)\b', 'IS', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^(is\s*\/\s*iec)\b', 'IS/IEC', clean, flags=re.IGNORECASE)
    # Standardize colon spacing e.g. "IS 374 : 2019" -> "IS 374:2019"
    clean = re.sub(r'\s*[:\.]\s*(\d{4})$', r':\1', clean)
    return clean


def extract_standard_no(text: str) -> Optional[str]:
    """
    Extract the first occurrence of a BIS standard number from text.

    Args:
        text: Text string to search.

    Returns:
        Normalized standard identifier or None if no match is found.
    """
    match = STANDARD_NO_REGEX.search(text)
    if match:
        return normalize_standard_no(match.group(1))
    return None


def extract_section_title(text: str, clause_no: Optional[str] = None) -> Optional[str]:
    """
    Extract heading or section title text from a clause chunk.

    Args:
        text: Text content of the chunk.
        clause_no: Optional clause number (e.g. '4.2') to locate header line.

    Returns:
        Extracted section title string or None.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return None

    first_line = lines[0]

    # If first line begins with clause number, extract the remainder
    if clause_no:
        pattern = rf'^(?:(?:CLAUSE|Clause|SECTION|Section)\s+)?{re.escape(clause_no)}[\.\:\s\-]*(.*)$'
        match = re.match(pattern, first_line, flags=re.IGNORECASE)
        if match:
            title_part = match.group(1).strip()
            if title_part:
                return title_part

    # Check for general title line (e.g. "1 SCOPE" or "GENERAL REQUIREMENTS")
    match = re.match(r'^(?:\d+(?:\.\d+)*\s+)?([A-Z][A-Za-z0-9\s,\-\–\(\)]+)$', first_line)
    if match:
        candidate = match.group(1).strip()
        if len(candidate.split()) <= 10:  # Reasonable title length
            return candidate

    return None


def extract_standard_meta(header_text: str, fallback_standard_no: Optional[str] = None) -> StandardMeta:
    """
    Extract document-level metadata from header or preamble text.

    Args:
        header_text: Document header / title page text.
        fallback_standard_no: Optional default standard number if not found in text.

    Returns:
        StandardMeta instance with extracted attributes.
    """
    std_no = extract_standard_no(header_text) or fallback_standard_no or "UNKNOWN"

    # Look up in curated demo catalog if available
    if std_no in DEMO_CATALOG:
        title, category, status = DEMO_CATALOG[std_no]
        return StandardMeta(
            standard_no=std_no,
            title=title,
            category=category,
            status=status,
        )

    # Generic extraction fallback
    lines = [line.strip() for line in header_text.split("\n") if line.strip()]
    doc_title = lines[0] if lines else f"Indian Standard {std_no}"

    return StandardMeta(
        standard_no=std_no,
        title=doc_title,
        category="General",
        status="Active",
    )


def tag_chunk(
    chunk: Clause,
    document_meta: Optional[StandardMeta] = None,
) -> Clause:
    """
    Enrich a raw clause chunk with document and section metadata.

    Args:
        chunk: Clause instance from chunk_document().
        document_meta: Optional parent document StandardMeta context.

    Returns:
        Enriched Clause instance with all metadata fields populated.
    """
    standard_no = (
        extract_standard_no(chunk.text)
        or (document_meta.standard_no if document_meta else "UNKNOWN")
    )

    clause_no = chunk.clause_no or chunk.approx_clause_no
    section_title = extract_section_title(chunk.text, clause_no=clause_no)

    doc_title = document_meta.title if document_meta else None
    category = document_meta.category if document_meta else None

    # Determine if chunk needs manual review (missing standard number or empty text)
    needs_review = bool(
        standard_no == "UNKNOWN"
        or not chunk.text.strip()
    )

    return Clause(
        text=chunk.text,
        page_no=chunk.page_no,
        standard_no=standard_no,
        clause_no=clause_no,
        section_title=section_title,
        document_title=doc_title,
        category=category,
        needs_review=needs_review,
    )
