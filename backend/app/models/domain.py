"""
Standardify — Internal domain dataclasses (not exposed via API directly).

These are the internal representations that flow between the ingestion
pipeline and the core retrieval/scoring layers.

Classes (added per-phase):
  Phase 1.3 — StandardMeta, Clause
  Phase 2.3 — RetrievedClause (Clause + similarity_score)
  Phase 2.4 — ConfidenceResult (value, label, evidence_found)
  Phase 3.2 — LLMResult (text, provider_used, latency_ms), LLMUnavailableError
  Phase 7.1 — StatusInfo (status, superseded_by, last_amended_date)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StandardMeta:
    """
    Metadata representation for a complete Indian Standard (BIS) document.

    Attributes:
        standard_no: Unique standard identifier (e.g., 'IS 374:2019', 'IS 9001:2025').
        title: Official title or product scope of the standard.
        category: Broad industry/product classification category.
        status: Current lifecycle status ('Active', 'Under Revision', 'Withdrawn', 'Superseded').
        superseded_by: Standard identifier replacing this document if withdrawn/superseded.
        last_amended_date: Date of most recent amendment or gazette notification.
        source_url: Link to official BIS portal or document source.
    """

    standard_no: str
    title: str
    category: Optional[str] = None
    status: str = "Active"
    superseded_by: Optional[str] = None
    last_amended_date: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class Clause:
    """
    Structured clause chunk enriched with standard and document-level metadata.

    Attributes:
        text: Normalized clause text content.
        page_no: 1-indexed page number where the chunk originates.
        standard_no: Standard number identifier (e.g. 'IS 374:2019').
        clause_no: Specific clause number (e.g. '4.2', '5.1.3') or None.
        section_title: Heading/title associated with this clause section.
        document_title: Full title of the parent standard document.
        category: Broad category name associated with the standard.
        needs_review: Flag indicating missing/ambiguous metadata requiring review.
    """

    text: str
    page_no: int
    standard_no: str = "UNKNOWN"
    clause_no: Optional[str] = None
    section_title: Optional[str] = None
    document_title: Optional[str] = None
    category: Optional[str] = None
    needs_review: bool = False

    @property
    def approx_clause_no(self) -> Optional[str]:
        """Backward compatibility alias for clause_no."""
        return self.clause_no
