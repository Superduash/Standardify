"""
Standardify — Standard Search & Autocomplete Unit & Integration Tests (Phase 8).

Tests:
1. Exact standard-number query ("IS 374") returns exact match first with top relevance.
2. Exact number match outranks fuzzy matches.
3. Product search ("fan safety") returns relevant fan standard.
4. Keyword search over category/title works via FTS5.
5. Semantic fuzzy title match works without exact keyword tokens.
6. Merged results are deduplicated.
7. /api/v1/standards/suggest returns at most 5 results.
8. Suggestion latency is fast (<100ms).
9. Unknown query returns safe empty results list.
"""

from __future__ import annotations

import time
from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_exact_standard_number_search_ranked_first():
    """Verify exact standard number search ('IS 374') returns IS 374:2019 first with highest score."""
    response = client.get("/api/v1/standards/search?q=IS 374")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] > 0
    top_result = data["results"][0]
    assert "IS 374" in top_result["standard_no"]
    assert top_result["relevance_score"] >= 0.95


def test_exact_number_search_not_outranked_by_fuzzy():
    """Verify number query '9001' prioritizes IS 9001:2025."""
    response = client.get("/api/v1/standards/search?q=9001")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] > 0
    top_result = data["results"][0]
    assert top_result["standard_no"] == "IS 9001:2025"
    assert top_result["relevance_score"] >= 0.95


def test_product_keyword_search_returns_relevant_standard():
    """Verify product query 'ceiling fan' returns electric ceiling fans standard."""
    response = client.get("/api/v1/standards/search?q=ceiling fan")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] > 0
    matched_stds = [r["standard_no"] for r in data["results"]]
    assert "IS 374:2019" in matched_stds


def test_category_keyword_search():
    """Verify search by category term 'Packaging' returns plastic water container standard."""
    response = client.get("/api/v1/standards/search?q=Packaging")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] > 0
    matched_stds = [r["standard_no"] for r in data["results"]]
    assert "IS 9001:2025" in matched_stds


def test_semantic_fuzzy_title_search():
    """Verify semantic search matches conceptually related terms without exact keyword overlap."""
    response = client.get("/api/v1/standards/search?q=head protection motorcycle gear")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] > 0
    matched_stds = [r["standard_no"] for r in data["results"]]
    assert "IS 9003:2026" in matched_stds


def test_search_results_are_deduplicated():
    """Verify no duplicate standard numbers appear in search results."""
    response = client.get("/api/v1/standards/search?q=electric ceiling fans")
    assert response.status_code == 200
    data = response.json()

    std_numbers = [r["standard_no"] for r in data["results"]]
    assert len(std_numbers) == len(set(std_numbers))


def test_suggest_endpoint_returns_at_most_5():
    """Verify /api/v1/standards/suggest returns at most 5 results."""
    response = client.get("/api/v1/standards/suggest?q=IS")
    assert response.status_code == 200
    data = response.json()

    assert "suggestions" in data
    assert len(data["suggestions"]) <= 5
    assert len(data["suggestions"]) > 0
    assert all("standard_no" in item and "title" in item for item in data["suggestions"])


def test_suggest_endpoint_latency_fast():
    """Verify /api/v1/standards/suggest responds rapidly (<100ms)."""
    start = time.time()
    response = client.get("/api/v1/standards/suggest?q=fan")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 100.0


def test_unknown_query_returns_safe_empty():
    """Verify searching for gibberish returns 0 results cleanly."""
    response = client.get("/api/v1/standards/search?q=xyz987qwe123gibberishnonexistent")
    assert response.status_code == 200
    data = response.json()

    assert data["total_results"] == 0
    assert data["results"] == []
