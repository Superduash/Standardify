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


@dataclass
class RetrievedClause:
    """
    Clause chunk retrieved via dense or hybrid search enriched with scoring metrics.

    Attributes:
        clause: The underlying Clause domain object.
        similarity_score: Combined normalized relevance score in [0.0, 1.0].
        dense_score: Dense semantic similarity score (cosine or 1 - distance).
        lexical_score: Normalized BM25/lexical match score.
        retrieval_method: Strategy used ('dense', 'lexical', 'hybrid').
    """

    clause: Clause
    similarity_score: float
    dense_score: float = 0.0
    lexical_score: float = 0.0
    retrieval_method: str = "hybrid"

    @property
    def text(self) -> str:
        """Alias for clause text."""
        return self.clause.text

    @property
    def standard_no(self) -> str:
        """Alias for clause standard_no."""
        return self.clause.standard_no

    @property
    def clause_no(self) -> Optional[str]:
        """Alias for clause clause_no."""
        return self.clause.clause_no

    @property
    def page_no(self) -> int:
        """Alias for clause page_no."""
        return self.clause.page_no

    @property
    def section_title(self) -> Optional[str]:
        """Alias for clause section_title."""
        return self.clause.section_title

    @property
    def document_title(self) -> Optional[str]:
        """Alias for clause document_title."""
        return self.clause.document_title

    @property
    def category(self) -> Optional[str]:
        """Alias for clause category."""
        return self.clause.category


@dataclass
class ConfidenceResult:
    """
    Evidence confidence evaluation for a set of retrieved clauses.

    Attributes:
        value: Numerical confidence score in range [0.0, 1.0].
        label: Qualitative confidence tier ('high', 'medium', 'low').
        evidence_found: True if confidence meets or exceeds settings.confidence_floor.
        top_similarity: Similarity score of the top-1 ranked clause.
        agreement_count: Number of top retrieved chunks agreeing on the top standard.
    """

    value: float
    label: str  # 'high' | 'medium' | 'low'
    evidence_found: bool
    top_similarity: float = 0.0
    agreement_count: int = 1
