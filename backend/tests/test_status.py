"""
Standardify — Amendment & Withdrawal Status Tracker Unit & Integration Tests (Phase 7).

Tests:
1. Active demo standard returns status='Active' with no warnings.
2. Superseded standard returns status='Superseded' and correct superseded_by value.
3. Amended standard returns correct last_amended_date.
4. Unknown standard returns None / 404 Not Found.
5. /ask endpoint adds warning if a cited standard is superseded or withdrawn.
6. Active cited standards generate no unnecessary warnings in /ask.
7. GET /api/v1/standards/{standard_no}/status returns valid StatusResponse.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from app.core.status_tracker import get_status, get_status_warning
from app.main import app
from app.models.domain import Clause, LLMResult, RetrievedClause

client = TestClient(app)


def test_get_status_active_standard():
    """Verify active standard returns Active status and no successor."""
    info = get_status("IS 9001:2025")
    assert info is not None
    assert info.standard_no == "IS 9001:2025"
    assert info.status == "Active"
    assert info.superseded_by is None


def test_get_status_superseded_standard():
    """Verify superseded standard returns Superseded status and successor standard."""
    info = get_status("IS 374:1979")
    assert info is not None
    assert info.status == "Superseded"
    assert info.superseded_by == "IS 374:2019"

    warning = get_status_warning("IS 374:1979")
    assert warning is not None
    assert "superseded by IS 374:2019" in warning


def test_get_status_amended_standard():
    """Verify amended standard returns last_amended_date."""
    info = get_status("IS 374:2019")
    assert info is not None
    assert info.last_amended_date == "2024-06-15"


def test_get_status_unknown_standard():
    """Verify unknown standard returns None."""
    info = get_status("IS 88888:9999")
    assert info is None

    warning = get_status_warning("IS 88888:9999")
    assert warning is None


def test_api_get_standard_status_endpoint_success():
    """Verify GET /api/v1/standards/{standard_no}/status returns 200 and typed StatusResponse."""
    response = client.get("/api/v1/standards/IS 9001:2025/status")
    assert response.status_code == 200
    data = response.json()

    assert data["standard_no"] == "IS 9001:2025"
    assert data["status"] == "Active"
    assert data["superseded_by"] is None


def test_api_get_standard_status_endpoint_superseded():
    """Verify GET /api/v1/standards/{standard_no}/status returns superseded information."""
    response = client.get("/api/v1/standards/IS 1293:2005/status")
    assert response.status_code == 200
    data = response.json()

    assert data["standard_no"] == "IS 1293:2005"
    assert data["status"] == "Superseded"
    assert data["superseded_by"] == "IS 1293:2019"


def test_api_get_standard_status_endpoint_not_found():
    """Verify GET /api/v1/standards/{standard_no}/status returns 404 for unknown standards."""
    response = client.get("/api/v1/standards/IS 99999:2099/status")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_ask_endpoint_injects_superseded_warning():
    """Verify that /ask adds a warning when a cited standard has superseded status."""
    superseded_clause = RetrievedClause(
        clause=Clause(
            text="Electric ceiling fans shall deliver 210 m3/min air delivery.",
            page_no=3,
            standard_no="IS 374:1979",
            clause_no="5.1",
            section_title="Air Delivery",
            document_title="Electric Ceiling Fans",
        ),
        similarity_score=0.88,
    )

    with patch("app.api.v1.ask.retrieve", return_value=[superseded_clause]), \
         patch("app.api.v1.ask.score_confidence") as mock_conf, \
         patch("app.api.v1.ask.generate_answer") as mock_llm:

        mock_conf.return_value = MagicMock(value=0.88, label="high", evidence_found=True)
        mock_llm.return_value = LLMResult(
            text="The required air delivery is 210 m3/min under IS 374:1979.",
            provider_used="groq",
            latency_ms=100,
        )

        response = client.post("/api/v1/ask", json={"question": "What was the fan air delivery in IS 374:1979?"})

    assert response.status_code == 200
    data = response.json()

    assert data["evidence_found"] is True
    assert len(data["warnings"]) >= 1
    assert any("superseded by IS 374:2019" in w for w in data["warnings"])


def test_ask_endpoint_active_standard_has_no_warnings():
    """Verify that /ask does not generate warnings for active standards."""
    active_clause = RetrievedClause(
        clause=Clause(
            text="Plastic containers must be made from virgin food grade polymers.",
            page_no=2,
            standard_no="IS 9001:2025",
            clause_no="4.1",
            section_title="Material Requirements",
            document_title="Plastic Containers for Packaged Water",
        ),
        similarity_score=0.92,
    )

    with patch("app.api.v1.ask.retrieve", return_value=[active_clause]), \
         patch("app.api.v1.ask.score_confidence") as mock_conf, \
         patch("app.api.v1.ask.generate_answer") as mock_llm:

        mock_conf.return_value = MagicMock(value=0.92, label="high", evidence_found=True)
        mock_llm.return_value = LLMResult(
            text="Plastic containers must be made from virgin polymers.",
            provider_used="groq",
            latency_ms=90,
        )

        response = client.post("/api/v1/ask", json={"question": "What are water container material requirements?"})

    assert response.status_code == 200
    data = response.json()
    assert data["warnings"] == []
