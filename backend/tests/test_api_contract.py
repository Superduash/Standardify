"""
Standardify — API Versioning & OpenAPI Contract Audit Tests (Phase 9.4).

Verifies that:
1. All application endpoints strictly reside under /api/v1/ prefix.
2. All 8 required core endpoints are present in the OpenAPI schema.
3. Every endpoint specifies summary, description, and typed response definitions.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.main import app

client = TestClient(app)


def test_openapi_schema_generated():
    """Verify OpenAPI JSON schema is generated cleanly."""
    schema = app.openapi()
    assert schema is not None
    assert schema["info"]["title"] == "Standardify API"
    assert "paths" in schema


def test_all_routes_use_api_v1_prefix():
    """Verify that all application API paths start with /api/v1/."""
    schema = app.openapi()
    paths = schema["paths"]

    for path in paths:
        # Ignore OpenAPI internal paths
        if path in ("/docs", "/redoc", "/openapi.json"):
            continue
        assert path.startswith("/api/v1/"), f"Route '{path}' does not use /api/v1/ prefix!"


def test_all_required_endpoints_exist():
    """Verify all 8 core functional endpoints exist in OpenAPI schema."""
    schema = app.openapi()
    paths = schema["paths"]

    expected_endpoints = {
        "/api/v1/ask": ["post"],
        "/api/v1/gap-check": ["post"],
        "/api/v1/graph/{standard_no}": ["get"],
        "/api/v1/graph/full": ["get"],
        "/api/v1/standards/search": ["get"],
        "/api/v1/standards/suggest": ["get"],
        "/api/v1/standards/{standard_no}/status": ["get"],
        "/api/v1/health": ["get"],
        "/api/v1/health/quota": ["get"],
    }

    for endpoint, methods in expected_endpoints.items():
        assert endpoint in paths, f"Required endpoint '{endpoint}' missing from API schema!"
        for m in methods:
            assert m in paths[endpoint], f"HTTP method '{m.upper()}' missing for '{endpoint}'!"


def test_every_endpoint_has_metadata_and_responses():
    """Verify every route has summary, description, and response definitions."""
    schema = app.openapi()
    paths = schema["paths"]

    for path, path_item in paths.items():
        for method, op in path_item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            assert "summary" in op and op["summary"], f"Missing summary for {method.upper()} {path}"
            assert "description" in op and op["description"], f"Missing description for {method.upper()} {path}"
            assert "responses" in op and op["responses"], f"Missing responses for {method.upper()} {path}"
            assert "200" in op["responses"] or "201" in op["responses"], f"Missing 200/201 response for {method.upper()} {path}"
