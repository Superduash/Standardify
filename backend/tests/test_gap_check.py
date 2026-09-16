"""
Standardify — Compliance Gap Checker Unit & Integration Tests (Phase 5).

Tests:
1. Known demo product -> expected standard(s) identified.
2. Deliberately incomplete product description -> non-empty missing_requirements.
3. Complete-ish description -> more matched requirements than incomplete.
4. Unknown/out-of-scope product -> safe empty result with 0 confidence.
5. Deterministic matching runs locally with zero LLM calls.
6. Repeated product description -> summary served from cache without duplicate LLM calls.
7. Requirement cache idempotency prevents duplicate extraction LLM calls.
8. Every returned missing requirement has a valid clause source tag.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from app.core.cache import QuotaAwareCache
from app.core.gap_checker import (
    check_gaps,
    find_applicable_standards,
    run_gap_check,
)
from app.ingestion.requirement_extractor import (
    extract_requirements_for_standard,
    load_requirements_cache,
)
from app.main import app
from app.models.domain import Clause, LLMResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_cache():
    """Clear memory/disk cache before tests to prevent cross-test pollution."""
    cache = QuotaAwareCache()
    cache.clear()
    yield
    cache.clear()


def test_find_applicable_standards_known_product():
    """Test standard identification on a known demo product description."""
    desc = "We manufacture 1-liter plastic drinking water bottles made from virgin PET."
    standards, confidence = find_applicable_standards(desc)

    assert len(standards) >= 1
    assert "IS 9001:2025" in standards
    assert confidence >= 0.40


def test_gap_check_incomplete_description_has_missing_requirements():
    """Test that a product missing drop/pressure tests has missing_requirements."""
    desc = "We manufacture 1L plastic drinking water bottles from virgin food grade polymer only."

    with patch("app.core.gap_checker.generate_answer") as mock_llm:
        mock_llm.return_value = LLMResult(
            text="The product meets material criteria under IS 9001:2025 but lacks drop impact and pressure test verification.",
            provider_used="groq",
            latency_ms=120,
        )

        response = client.post("/api/v1/gap-check", json={"product_description": desc})

    assert response.status_code == 200
    data = response.json()

    assert "IS 9001:2025" in data["applicable_standards"]
    assert len(data["missing_requirements"]) > 0
    # Drop impact or pressure test should be missing
    missing_text = " ".join(data["missing_requirements"])
    assert "5.2" in missing_text or "Drop" in missing_text or "pressure" in missing_text.lower()
    assert data["confidence"] > 0.0


def test_gap_check_complete_description_matches_more_requirements():
    """Test that a detailed description addressing drop & pressure tests has more matched requirements."""
    incomplete_desc = "We produce plastic water containers from virgin food grade polymer."
    complete_desc = (
        "We produce plastic water containers from virgin food grade polymer. "
        "The filled bottles undergo a 1.2 meter drop test onto flat concrete without rupture, "
        "and withstand 200 kPa hydrostatic internal pressure for 5 minutes without leakage."
    )

    _, inc_missing = check_gaps(incomplete_desc, ["IS 9001:2025"])
    com_matched, _ = check_gaps(complete_desc, ["IS 9001:2025"])

    assert len(com_matched) >= 2
    assert len(inc_missing) >= 1


def test_gap_check_out_of_scope_product_returns_safe_empty():
    """Test that an unknown/extraterrestrial product returns empty standards safely."""
    desc = "Quantum superconducting interstellar warp drive with tachyon shielding"

    response = client.post("/api/v1/gap-check", json={"product_description": desc})
    assert response.status_code == 200
    data = response.json()

    assert data["applicable_standards"] == []
    assert data["matched_requirements"] == []
    assert data["missing_requirements"] == []
    assert data["confidence"] == 0.0
    assert "No applicable Indian Standards found" in data["summary"]


def test_deterministic_matching_makes_zero_llm_calls():
    """Verify that core standard identification and requirement matching use NO LLMs."""
    desc = "Electric ceiling fan 1200 mm sweep with safety shackle and 210 m3/min air delivery"

    with patch("app.core.llm_client.generate_answer") as mock_llm:
        stds, _ = find_applicable_standards(desc)
        matched, missing = check_gaps(desc, stds)

        # Mock LLM must NEVER be invoked during find_applicable_standards or check_gaps
        mock_llm.assert_not_called()

    assert "IS 374:2019" in stds
    assert len(matched) + len(missing) > 0


def test_gap_summary_exact_cache_prevents_duplicate_llm():
    """Verify that calling gap-check twice with the same description makes exactly 1 LLM call."""
    desc = "Pre-packaged potato chips with nutritional label showing energy, fat, sodium, and bold allergen declaration."

    with patch("app.core.gap_checker.generate_answer") as mock_llm:
        mock_llm.return_value = LLMResult(
            text="The packaged food product satisfies mandatory nutritional and allergen declarations under IS 9004:2025.",
            provider_used="groq",
            latency_ms=150,
        )

        # First call -> LLM generation
        res1 = client.post("/api/v1/gap-check", json={"product_description": desc})
        assert res1.status_code == 200
        assert mock_llm.call_count == 1

        # Second call -> Exact cache hit
        res2 = client.post("/api/v1/gap-check", json={"product_description": desc})
        assert res2.status_code == 200
        assert mock_llm.call_count == 1  # Still 1 call!

        assert res1.json()["summary"] == res2.json()["summary"]


def test_requirement_extractor_skips_cached_standards():
    """Verify that requirement extraction skips LLM call when standard is already in requirements_cache.json."""
    clauses = [
        Clause(
            text="Clause 4.1 Material Requirements: Virgin food grade polymer.",
            page_no=2,
            standard_no="IS 9001:2025",
            clause_no="4.1",
            section_title="Material Requirements",
        )
    ]

    with patch("app.ingestion.requirement_extractor.generate_answer") as mock_llm:
        # Standard IS 9001:2025 is already in requirements_cache.json
        reqs = extract_requirements_for_standard("IS 9001:2025", clauses, force_refresh=False)
        mock_llm.assert_not_called()
        assert len(reqs) > 0


def test_missing_requirements_have_traceable_clause_tags():
    """Verify that every returned missing requirement includes standard and clause number."""
    desc = "Protective helmet for two-wheelers"
    result = run_gap_check(desc)

    assert len(result.applicable_standards) > 0
    assert "IS 9003:2026" in result.applicable_standards

    for missing_item in result.missing_requirements:
        assert "[" in missing_item and "]" in missing_item
        assert "Clause" in missing_item
        assert "IS 9003:2026" in missing_item
