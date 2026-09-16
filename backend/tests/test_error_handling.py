"""
Standardify — Global Structured Error Handling & Rate Limiting Tests (Phase 9.2 & 9.3).

Tests:
1. Every response contains X-Request-ID correlation header.
2. Validation errors return HTTP 422 with structured {"error": "validation_error", "detail": ..., "request_id": ...}.
3. LLMUnavailableError returns HTTP 503 with structured {"error": "llm_unavailable", "detail": ..., "request_id": ...}.
4. Unhandled server errors return HTTP 500 with structured envelope without leaking stack traces.
5. Per-IP rate limiting enforces 429 on /api/v1/ask when limit is exceeded.
6. Per-IP rate limiting enforces 429 on /api/v1/gap-check when limit is exceeded.
7. Health endpoints are not subject to rate limits.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from app.config import settings
from app.main import _RATE_LIMIT_STORE, app
from app.models.domain import LLMUnavailableError

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clear rate limit tracking store before each test."""
    _RATE_LIMIT_STORE.clear()
    yield
    _RATE_LIMIT_STORE.clear()


def test_request_id_header_in_responses():
    """Verify that every API response includes an X-Request-ID header."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 8


def test_validation_error_returns_structured_422():
    """Verify invalid payloads return structured error with detail and request_id."""
    # Invalid ask request (question too short / empty)
    response = client.post("/api/v1/ask", json={"question": "a"})
    assert response.status_code == 422
    data = response.json()

    assert data["error"] == "validation_error"
    assert "detail" in data
    assert "request_id" in data
    assert "X-Request-ID" in response.headers


def test_llm_unavailable_error_returns_structured_503():
    """Verify LLMUnavailableError returns clean HTTP 503 structured response."""
    with patch("app.api.v1.ask.retrieve") as mock_ret, \
         patch("app.api.v1.ask.score_confidence") as mock_conf, \
         patch("app.api.v1.ask.get_exact_cache", return_value=None), \
         patch("app.api.v1.ask.get_semantic_cache", return_value=None), \
         patch("app.api.v1.ask.generate_answer", side_effect=LLMUnavailableError("All providers failed")):

        mock_ret.return_value = [
            MagicMock(standard_no="IS 374:2019", clause_no="5.1", page_no=3, section_title="Fan", document_title="Fans", text="Text", similarity_score=0.85)
        ]
        mock_conf.return_value = MagicMock(value=0.85, label="high", evidence_found=True)

        response = client.post("/api/v1/ask", json={"question": "What is the airflow for electric ceiling fans?"})

    assert response.status_code == 503
    data = response.json()
    assert data["error"] == "http_error" or data["error"] == "llm_unavailable"
    assert "request_id" in data
    assert "X-Request-ID" in response.headers


def test_unhandled_exception_returns_safe_500_without_traceback():
    """Verify unhandled 500 error returns safe envelope without exposing tracebacks."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    with patch("app.api.v1.standards.get_status", side_effect=RuntimeError("Database disk corruption! /var/secret")):
        response = safe_client.get("/api/v1/standards/IS 9001:2025/status")

    assert response.status_code == 500
    data = response.json()


    assert data["error"] == "internal_server_error"
    assert "detail" in data
    assert "Database disk corruption" not in data["detail"]  # No internal traceback leak
    assert "request_id" in data


def test_rate_limiting_on_ask_endpoint():
    """Verify exceeding request limit triggers 429 on /api/v1/ask."""
    with patch.object(settings, "rate_limit_requests", 3), \
         patch.object(settings, "rate_limit_window_seconds", 60), \
         patch("app.api.v1.ask.retrieve", return_value=[]), \
         patch("app.api.v1.ask.score_confidence") as mock_conf:

        mock_conf.return_value = MagicMock(value=0.0, label="low", evidence_found=False)

        # 3 allowed requests
        for _ in range(3):
            res = client.post("/api/v1/ask", json={"question": "What is the standard for fan airflow?"})
            assert res.status_code == 200

        # 4th request exceeds limit -> 429
        res_blocked = client.post("/api/v1/ask", json={"question": "What is the standard for fan airflow?"})
        assert res_blocked.status_code == 429
        data = res_blocked.json()
        assert data["error"] == "rate_limit_exceeded"
        assert "Retry-After" in res_blocked.headers


def test_rate_limiting_on_gap_check_endpoint():
    """Verify exceeding request limit triggers 429 on /api/v1/gap-check."""
    with patch.object(settings, "rate_limit_requests", 2), \
         patch.object(settings, "rate_limit_window_seconds", 60), \
         patch("app.core.gap_checker.find_applicable_standards", return_value=([], 0.0)):

        # 2 allowed requests
        for _ in range(2):
            res = client.post("/api/v1/gap-check", json={"product_description": "We make plastic drinking bottles."})
            assert res.status_code == 200

        # 3rd request exceeds limit -> 429
        res_blocked = client.post("/api/v1/gap-check", json={"product_description": "We make plastic drinking bottles."})
        assert res_blocked.status_code == 429
        data = res_blocked.json()
        assert data["error"] == "rate_limit_exceeded"


def test_health_endpoints_not_rate_limited():
    """Verify health endpoints are not throttled even under burst traffic."""
    with patch.object(settings, "rate_limit_requests", 1):
        for _ in range(5):
            res = client.get("/api/v1/health")
            assert res.status_code == 200
