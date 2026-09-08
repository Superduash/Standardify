"""GET /api/search?q=&category=&limit="""
from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from app.models.schemas import SearchResponse, SearchResultItem
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_standards(
    q: str = Query(default="", description="Search query (keyword or natural language)"),
    category: str = Query(default="", description="Filter by category string (partial match)"),
    limit: int = Query(default=10, ge=1, le=50),
) -> SearchResponse:
    vector_store = get_vector_store()

    if not q.strip():
        return SearchResponse(query=q, results=[], total=0)

    raw_results = vector_store.keyword_search(q.strip(), top_k=limit * 2)

    items: list[SearchResultItem] = []
    seen_ids: set[str] = set()

    for r in raw_results:
        meta = r.get("metadata", {})
        doc_id = r.get("id", "")

        # Deduplicate by standard+clause pair
        dedup_key = f"{meta.get('standard_no', '')}:{meta.get('clause_no', '')}:{doc_id}"
        if dedup_key in seen_ids:
            continue
        seen_ids.add(dedup_key)

        # Category filter
        if category:
            # We don't store category in chunk metadata, so match on title/standard_no
            cat_lower = category.lower()
            if cat_lower not in meta.get("title", "").lower() and cat_lower not in meta.get("standard_no", "").lower():
                continue

        snippet = r.get("document", "")
        # Trim snippet for display
        snippet = snippet[:250].strip()
        if len(r.get("document", "")) > 250:
            snippet += "…"

        items.append(
            SearchResultItem(
                standard_no=meta.get("standard_no", "Unknown"),
                title=meta.get("title", ""),
                clause_no=meta.get("clause_no") or None,
                snippet=snippet,
                score=round(r.get("score", 0.0), 4),
            )
        )

        if len(items) >= limit:
            break

    return SearchResponse(query=q, results=items, total=len(items))
