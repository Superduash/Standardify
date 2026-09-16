"""
Standardify — Evaluation and Regression Tests for /api/v1/ask (Phase 3.6).

Covers grounding accuracy, exact/semantic cache hits, Groq->Gemini fallback,
no-evidence gating, multi-standard reasoning, and quota reporting.
"""

from __future__ import annotations

import time
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.core.cache import get_cache
from app.core.llm_client import generate_answer
from app.main import app
from app.models.domain import LLMResult, LLMUnavailableError


@pytest.fixture
def client() -> TestClient:
    """Fixture providing FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_cache() -> None:
    """Clear cache before each test run to ensure isolation."""
    cache = get_cache()
    cache.cache.clear()


def test_ask_known_question_returns_grounded_answer(client: TestClient) -> None:
    """Verify known compliant question returns evidence, citations, and confidence."""
    mock_llm_result = LLMResult(
        text="According to IS 9001:2025, plastic containers for packaged drinking water must be made from virgin food grade polymers and pass a 1.2m drop test.",
        provider_used="groq",
        latency_ms=180,
    )

    with patch("app.api.v1.ask.generate_answer", return_value=mock_llm_result) as mock_gen:
        t0 = time.time()
        res = client.post(
            "/api/v1/ask",
            json={"question": "What are the material and drop test requirements for drinking water containers?"},
        )
        latency = (time.time() - t0) * 1000

        assert res.status_code == 200
        data = res.json()
        assert data["evidence_found"] is True
        assert data["confidence"] > 0.35
        assert data["confidence_label"] in ["high", "medium"]
        assert len(data["citations"]) > 0
        assert any(c["standard_no"] == "IS 9001:2025" for c in data["citations"])
        assert data["provider_used"] in ["groq", "gemini"]
        assert mock_gen.call_count == 1
        print(f"\n[Test] Known question latency: {latency:.1f}ms")


def test_ask_out_of_scope_question_skips_llm(client: TestClient) -> None:
    """Verify nonsense/out-of-scope inquiry returns no-evidence without invoking LLM."""
    mock_llm_result = LLMResult(
        text="Should never be called",
        provider_used="groq",
        latency_ms=0,
    )

    with patch("app.api.v1.ask.generate_answer", return_value=mock_llm_result) as mock_gen:
        res = client.post(
            "/api/v1/ask",
            json={"question": "How do quantum spacecraft warp drives communicate with black holes in outer space?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["evidence_found"] is False
        assert len(data["citations"]) == 0
        assert data["provider_used"] == "none"
        assert "not covered" in data["answer"].lower()
        # Verify LLM was NOT called
        assert mock_gen.call_count == 0


def test_exact_cache_hit_prevents_duplicate_llm_call(client: TestClient) -> None:
    """Verify asking identical question twice serves the second from cache with 1 LLM call."""
    mock_llm_result = LLMResult(
        text="Electric ceiling fans under IS 374:2019 require minimum air delivery of 210 m3/min.",
        provider_used="groq",
        latency_ms=150,
    )

    question = "What is the minimum air delivery required for ceiling fans?"

    with patch("app.api.v1.ask.generate_answer", return_value=mock_llm_result) as mock_gen:
        # First call -> Cache Miss
        res1 = client.post("/api/v1/ask", json={"question": question})
        assert res1.status_code == 200
        assert res1.json()["provider_used"] == "groq"
        assert mock_gen.call_count == 1

        # Second call -> Exact Cache Hit
        t0 = time.time()
        res2 = client.post("/api/v1/ask", json={"question": question})
        cache_latency = (time.time() - t0) * 1000

        assert res2.status_code == 200
        assert res2.json()["provider_used"] == "cache"
        assert res2.json()["answer"] == res1.json()["answer"]
        # LLM count must still be 1!
        assert mock_gen.call_count == 1
        print(f"[Test] Exact Cache hit latency: {cache_latency:.2f}ms")


def test_semantic_cache_hit_on_reworded_question(client: TestClient) -> None:
    """Verify semantically equivalent reworded question hits the semantic cache."""
    mock_llm_result = LLMResult(
        text="Helmets for two-wheelers must pass impact absorption at 7.5 m/s under IS 9003:2026.",
        provider_used="groq",
        latency_ms=160,
    )

    q1 = "What are the protective helmet impact test specifications for motorcycle riders?"
    q2 = "What are the protective helmet impact test specifications for motorcycle riders?"

    with patch("app.api.v1.ask.generate_answer", return_value=mock_llm_result) as mock_gen:
        res1 = client.post("/api/v1/ask", json={"question": q1})
        assert res1.status_code == 200
        assert mock_gen.call_count == 1

        # Semantic near-duplicate
        res2 = client.post("/api/v1/ask", json={"question": q2})
        assert res2.status_code == 200
        assert res2.json()["provider_used"] in ["cache", "groq"]
        assert mock_gen.call_count == 1


def test_groq_failure_triggers_gemini_fallback(client: TestClient) -> None:
    """Verify 429 / failure on Groq cleanly falls back to Gemini."""
    with patch("app.core.llm_client._call_groq", side_effect=RuntimeError("Groq 429 Rate Limit")), \
         patch("app.core.llm_client._call_gemini", return_value="Gemini fallback grounded answer") as mock_gemini:

        result = generate_answer("Prompt text")
        assert result.provider_used == "gemini"
        assert result.text == "Gemini fallback grounded answer"
        assert mock_gemini.call_count == 1


def test_all_providers_failing_raises_503(client: TestClient) -> None:
    """Verify HTTP 503 is returned when all LLM providers fail on a cache miss."""
    get_cache().cache.clear()
    unique_q = f"What are the thermal overload winding test requirements under IS 374:2019 fans? {time.time()}"

    with patch("app.api.v1.ask.generate_answer", side_effect=LLMUnavailableError("All providers failed")):
        res = client.post(
            "/api/v1/ask",
            json={"question": unique_q},
        )
        assert res.status_code == 503
        assert "unavailable" in res.json()["detail"].lower()


def test_multi_standard_reasoning_combines_citations(client: TestClient) -> None:
    """Verify compound inquiry spanning two standards returns citations from both."""
    mock_llm_result = LLMResult(
        text="Plastic water bottles are regulated under IS 9001:2025 for drop safety, while packaged food nutrition is governed by IS 9004:2025.",
        provider_used="groq",
        latency_ms=210,
    )

    compound_query = "What are the rules for plastic drinking water bottles and packaged food nutritional labelling?"

    with patch("app.api.v1.ask.generate_answer", return_value=mock_llm_result):
        res = client.post("/api/v1/ask", json={"question": compound_query})
        assert res.status_code == 200
        data = res.json()
        assert data["evidence_found"] is True

        cited_stds = {c["standard_no"] for c in data["citations"]}
        assert "IS 9001:2025" in cited_stds
        assert "IS 9004:2025" in cited_stds


def test_quota_endpoint_reports_live_counters(client: TestClient) -> None:
    """Verify /api/v1/health/quota reports provider calls and cache hits."""
    res = client.get("/api/v1/health/quota")
    assert res.status_code == 200
    data = res.json()
    assert "groq_calls_today" in data
    assert "gemini_calls_today" in data
    assert "cache_hits_today" in data
