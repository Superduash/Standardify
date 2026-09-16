"""
Standardify — Standards API: Search, Autocomplete & Lifecycle Status (Phase 7.3, 8.1, 8.2).

Provides:
  - GET /api/v1/standards/search: Combined exact, FTS5 keyword, and title semantic search.
  - GET /api/v1/standards/suggest: Lightweight prefix/keyword autocomplete suggestions.
  - GET /api/v1/standards/{standard_no}/status: Official lifecycle and amendment status tracking.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Tuple
from fastapi import APIRouter, HTTPException, Query, status

from app.core.embeddings import embed_batch, embed_query
from app.core.status_tracker import get_status
from app.models.schemas import (
    SearchResponse,
    SearchResult,
    StatusResponse,
    SuggestItem,
    SuggestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/standards", tags=["Standards Discovery & Status"])

DB_PATH = Path("./data/registry.db")

# In-memory title embedding cache for lightweight semantic search over standard titles
_TITLE_EMBEDDING_CACHE: Optional[List[Tuple[str, str, Optional[str], str, List[float]]]] = None


def _get_db() -> sqlite3.Connection:
    """Create SQLite database connection and ensure FTS5 virtual table is ready."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_fts(conn: sqlite3.Connection) -> None:
    """Initialize SQLite FTS5 table if not already present."""
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS standards_fts USING fts5(
                standard_no, title, category, content=standards, content_rowid=rowid
            )
        """)
        conn.commit()
    except Exception as exc:
        logger.warning("FTS5 table initialization notice: %s", exc)


def _cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_title_embeddings() -> List[Tuple[str, str, Optional[str], str, List[float]]]:
    """Load and cache standard titles along with their BGE-M3 embedding vectors."""
    global _TITLE_EMBEDDING_CACHE
    if _TITLE_EMBEDDING_CACHE is not None:
        return _TITLE_EMBEDDING_CACHE

    with _get_db() as conn:
        rows = conn.execute("SELECT standard_no, title, category, status FROM standards").fetchall()

    if not rows:
        return []

    records = [(r["standard_no"], r["title"], r["category"], r["status"]) for r in rows]
    titles_to_embed = [f"{std} {title} {cat or ''}" for std, title, cat, _ in records]
    vectors = embed_batch(titles_to_embed)

    _TITLE_EMBEDDING_CACHE = [
        (std, title, cat, status_val, vec)
        for (std, title, cat, status_val), vec in zip(records, vectors)
    ]
    logger.info("Indexed %d standard titles for semantic title search.", len(_TITLE_EMBEDDING_CACHE))
    return _TITLE_EMBEDDING_CACHE


# ── Phase 8.1: Search Endpoint ───────────────────────────────────────────────

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search Indian Standards (BIS)",
    description=(
        "Search standards by number, product, or keyword using exact matching, "
        "SQLite FTS5 full-text search, and title semantic similarity."
    ),
)
async def search_standards_endpoint(
    q: str = Query(..., min_length=1, description="Search query term or standard number"),
) -> SearchResponse:
    """
    Execute multi-tier search combining exact standard number matches, FTS5 keyword hits,
    and BGE-M3 semantic title similarities.
    """
    clean_q = q.strip()
    if not clean_q:
        return SearchResponse(query=q, total_results=0, results=[])

    scored_candidates: Dict[str, SearchResult] = {}

    with _get_db() as conn:
        _ensure_fts(conn)

        # 1. Exact / Number Prefix Match (Highest Priority)
        # Normalize: 'is 374' -> '374', 'is374' -> '374'
        std_num_match = re.search(r'\b(?:IS\s*)?(\d{3,5}(?::\d{4})?)\b', clean_q, re.IGNORECASE)
        if std_num_match:
            raw_num = std_num_match.group(1)
            exact_rows = conn.execute(
                """
                SELECT standard_no, title, category, status
                FROM standards
                WHERE standard_no LIKE ? OR standard_no LIKE ?
                """,
                (f"%{raw_num}%", f"IS {raw_num}%"),
            ).fetchall()

            for r in exact_rows:
                std_no = r["standard_no"]
                # Exact full match gets 1.0, partial gets 0.95
                score = 1.0 if clean_q.lower() == std_no.lower() or f"is {raw_num}".lower() in std_no.lower() else 0.95
                scored_candidates[std_no] = SearchResult(
                    standard_no=std_no,
                    title=r["title"],
                    category=r["category"],
                    status=r["status"] or "Active",
                    relevance_score=score,
                )

        # 2. SQLite FTS5 Keyword Search
        tokens = [t for t in re.findall(r'\b\w+\b', clean_q) if len(t) > 1]
        if tokens:
            fts_query = " OR ".join(f'"{t}"*' for t in tokens)
            try:
                fts_rows = conn.execute(
                    """
                    SELECT s.standard_no, s.title, s.category, s.status, bm25(standards_fts) AS rank
                    FROM standards_fts f
                    JOIN standards s ON s.rowid = f.rowid
                    WHERE standards_fts MATCH ?
                    ORDER BY rank ASC
                    LIMIT 10
                    """,
                    (fts_query,),
                ).fetchall()

                for r in fts_rows:
                    std_no = r["standard_no"]
                    fts_score = round(max(0.60, min(0.90, 0.85 - (r["rank"] * 0.05))), 3)
                    if std_no not in scored_candidates or fts_score > scored_candidates[std_no].relevance_score:
                        scored_candidates[std_no] = SearchResult(
                            standard_no=std_no,
                            title=r["title"],
                            category=r["category"],
                            status=r["status"] or "Active",
                            relevance_score=fts_score,
                        )
            except Exception as exc:
                logger.warning("FTS5 query failed for '%s': %s", fts_query, exc)

    # 3. Lightweight Semantic Search Over Standard Titles
    query_vector = embed_query(clean_q)
    title_entries = _get_title_embeddings()

    for std_no, title, cat, status_val, title_vec in title_entries:
        sim = _cosine_similarity(query_vector, title_vec)
        if sim >= 0.40:
            sem_score = round(sim, 3)
            if std_no not in scored_candidates or sem_score > scored_candidates[std_no].relevance_score:
                scored_candidates[std_no] = SearchResult(
                    standard_no=std_no,
                    title=title,
                    category=cat,
                    status=status_val or "Active",
                    relevance_score=sem_score,
                )

    # 4. Rank and Sort Results
    ranked_results = list(scored_candidates.values())
    ranked_results.sort(key=lambda x: x.relevance_score, reverse=True)

    return SearchResponse(
        query=clean_q,
        total_results=len(ranked_results),
        results=ranked_results,
    )


# ── Phase 8.2: Autocomplete / Suggest Endpoint ───────────────────────────────

@router.get(
    "/suggest",
    response_model=SuggestResponse,
    summary="Get autocomplete suggestions for standard titles",
    description="Returns up to 5 fast title and standard number prefix suggestions for frontend typeahead (<100ms).",
)
async def suggest_standards_endpoint(
    q: str = Query(..., min_length=1, description="Query prefix for autocomplete"),
) -> SuggestResponse:
    """
    Lightweight autocomplete endpoint querying standard titles and numbers.
    """
    clean_q = q.strip()
    if not clean_q:
        return SuggestResponse(query=q, suggestions=[])

    suggestions: List[SuggestItem] = []
    seen = set()

    with _get_db() as conn:
        # Prefix lookup
        rows = conn.execute(
            """
            SELECT standard_no, title
            FROM standards
            WHERE standard_no LIKE ? OR title LIKE ?
            LIMIT 5
            """,
            (f"{clean_q}%", f"%{clean_q}%"),
        ).fetchall()

        for r in rows:
            std_no = r["standard_no"]
            if std_no not in seen:
                seen.add(std_no)
                suggestions.append(SuggestItem(standard_no=std_no, title=r["title"]))

    return SuggestResponse(query=clean_q, suggestions=suggestions[:5])


# ── Phase 7.3: Lifecycle Status Endpoint ──────────────────────────────────────

@router.get(
    "/{standard_no}/status",
    response_model=StatusResponse,
    summary="Get lifecycle and amendment status for an Indian Standard",
    description="Returns current lifecycle status (Active, Superseded, Withdrawn, Under Revision), successor standard, and last amended date.",
)
async def get_standard_status_endpoint(standard_no: str) -> StatusResponse:
    """
    Retrieve lifecycle and amendment status for the given standard number.
    """
    clean_std = standard_no.strip()
    if not clean_std:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Standard number parameter cannot be empty.",
        )

    info = get_status(clean_std)
    if not info:
        logger.warning("Standard status lookup failed for unknown standard: '%s'", clean_std)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{clean_std}' was not found in the BIS standards registry.",
        )

    return StatusResponse(
        standard_no=info.standard_no,
        status=info.status,
        superseded_by=info.superseded_by,
        last_amended_date=info.last_amended_date,
    )
