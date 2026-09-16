"""
Standardify — Tests for Health and Status API endpoints.

Covers GET /api/v1/health and GET /api/v1/health/quota.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a FastAPI test client."""
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/health returns 200 OK and expected status schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_quota_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/health/quota returns 200 OK with quota metrics."""
    response = client.get("/api/v1/health/quota")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "groq_calls_today" in data
    assert "gemini_calls_today" in data
