"""
Standardify — Retrieval Engine Regression & Unit Tests (Phase 2.5).

Runs golden_qa.json against the indexed standards vector store and asserts
top-3 retrieval accuracy >= 80%, standard filtering, and confidence scoring.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.core.confidence import score as score_confidence
from app.core.embeddings import embed_query, embed_batch
from app.core.retrieval import retrieve, get_index, get_collection
from app.models.domain import Clause, RetrievedClause


@pytest.fixture(scope="module")
def golden_qa_data() -> list[dict]:
    """Load golden QA dataset."""
    qa_path = Path(__file__).parent / "golden_qa.json"
    with open(qa_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def test_embedding_singleton_shape_and_types() -> None:
    """Verify BGE-M3 returns 1024-dim normalized float vectors."""
    vec = embed_query("Indian Standards testing protocol")
    assert isinstance(vec, list)
    assert len(vec) == 1024
    assert all(isinstance(x, float) for x in vec)

    batch = embed_batch(["Query 1", "Query 2"])
    assert len(batch) == 2
    assert len(batch[0]) == 1024
    assert len(batch[1]) == 1024


def test_llama_index_integration() -> None:
    """Verify LlamaIndex VectorStoreIndex wrapper initializes without error."""
    index = get_index()
    assert index is not None


def test_golden_qa_top3_hit_rate(golden_qa_data: list[dict]) -> None:
    """
    Verify top-3 retrieval contains the expected standard with >= 80% accuracy.
    """
    assert len(golden_qa_data) >= 15, "Golden QA dataset should have at least 15 questions"

    hits = 0
    total = len(golden_qa_data)
    failures = []

    for item in golden_qa_data:
        q = item["question"]
        expected_std = item["expected_standard"]

        results = retrieve(q, top_k=3)
        retrieved_standards = [r.standard_no for r in results]

        if expected_std in retrieved_standards:
            hits += 1
        else:
            failures.append({
                "id": item.get("id"),
                "question": q,
                "expected": expected_std,
                "got": retrieved_standards,
            })

    hit_rate = hits / total
    print(f"\n[Golden QA Result] {hits}/{total} ({hit_rate * 100:.1f}%) hits in Top-3")
    if failures:
        print(f"Failures: {failures}")

    assert hit_rate >= 0.80, f"Top-3 hit rate was {hit_rate:.2%}, expected >= 80%"


def test_standard_filter_enforcement() -> None:
    """Verify standard_filter strictly excludes all other standards."""
    target_std = "IS 9001:2025"
    results = retrieve(
        "What are the safety and test requirements?",
        top_k=5,
        standard_filter=target_std,
    )
    assert len(results) > 0
    for r in results:
        assert r.standard_no == target_std, f"Expected {target_std}, got {r.standard_no}"


def test_confidence_scoring_logic() -> None:
    """Verify confidence scoring formulas and thresholds."""
    # 1. Empty retrieval -> evidence_found = False, score = 0
    empty_conf = score_confidence([])
    assert empty_conf.evidence_found is False
    assert empty_conf.value == 0.0
    assert empty_conf.label == "low"

    # 2. Strong relevant retrieval with consensus
    c1 = Clause(text="Requirement text", page_no=1, standard_no="IS 9001:2025")
    c2 = Clause(text="Test text", page_no=2, standard_no="IS 9001:2025")
    c3 = Clause(text="Drop text", page_no=3, standard_no="IS 9001:2025")

    retrieved = [
        RetrievedClause(clause=c1, similarity_score=0.85, dense_score=0.85),
        RetrievedClause(clause=c2, similarity_score=0.80, dense_score=0.80),
        RetrievedClause(clause=c3, similarity_score=0.75, dense_score=0.75),
    ]

    conf = score_confidence(retrieved)
    assert conf.evidence_found is True
    assert conf.label == "high"
    assert conf.value >= 0.85
    assert conf.agreement_count == 3

    # 3. Weak retrieval below floor -> evidence_found = False
    weak_retrieved = [
        RetrievedClause(clause=c1, similarity_score=0.20, dense_score=0.20),
    ]
    weak_conf = score_confidence(weak_retrieved)
    assert weak_conf.evidence_found is False


def test_retrieved_clause_metadata_preservation() -> None:
    """Verify RetrievedClause retains all required metadata fields."""
    results = retrieve("drop test for drinking water bottles", top_k=1)
    assert len(results) >= 1
    top = results[0]

    assert top.standard_no != ""
    assert top.text != ""
    assert top.page_no > 0
    assert 0.0 <= top.similarity_score <= 1.0
    assert top.retrieval_method in ["dense", "lexical", "hybrid"]
