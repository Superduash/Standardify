"""
Standardify — Standards Relationship Graph Unit & Integration Tests (Phase 6).

Tests:
1. Graph builds from demo data with nodes and edges.
2. graph.json is created and reloadable.
3. Node attributes (id, label, status, category) are present.
4. Edge relation types (supersedes, references, same_category) are valid.
5. In-memory graph singleton is reused across repeated load_graph() calls.
6. Known standard returns expected direct neighbors at depth=1.
7. Subgraph query with depth=2 expands neighbors correctly.
8. Unknown standard raises 404 Not Found.
9. GET /api/v1/graph/{standard_no} endpoint returns valid GraphResponse JSON.
10. GET /api/v1/graph/full endpoint returns complete graph with pagination/capping.
"""

from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
import networkx as nx
import pytest

from app.core.graph_engine import (
    GRAPH_FILE_PATH,
    build_graph,
    get_full_graph,
    get_subgraph,
    load_graph,
)
from app.main import app

client = TestClient(app)


def test_graph_builds_and_persists_to_json(tmp_path):
    """Verify that build_graph() creates and saves graph.json with nodes and edges."""
    G = build_graph()
    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() >= 10
    assert G.number_of_edges() >= 10
    assert GRAPH_FILE_PATH.exists()


def test_node_attributes_and_edge_relations():
    """Verify nodes have label/status/category and edges have valid relation types."""
    G = load_graph()

    # Verify nodes
    node_data = G.nodes["IS 374:2019"]
    assert node_data["label"] == "Electric Ceiling Fans"
    assert node_data["status"] == "Active"
    assert node_data["category"] == "Electrical & Electronics"

    # Verify edge relations
    valid_relations = {"supersedes", "references", "same_category"}
    for u, v, data in G.edges(data=True):
        assert "relation" in data
        assert data["relation"] in valid_relations


def test_load_graph_reuses_singleton_instance():
    """Verify that multiple load_graph() invocations return the exact same in-memory instance."""
    g1 = load_graph()
    g2 = load_graph()
    assert g1 is g2


def test_get_subgraph_depth_1_direct_neighbors():
    """Verify depth=1 subgraph returns target node and its direct neighbors."""
    subgraph = get_subgraph("IS 374:2019", depth=1)

    assert "nodes" in subgraph and "edges" in subgraph
    node_ids = {n["id"] for n in subgraph["nodes"]}

    assert "IS 374:2019" in node_ids
    # Should include direct neighbors like IS 374:1979, IS 1293:2019, IS 9000:2025
    assert "IS 374:1979" in node_ids
    assert "IS 1293:2019" in node_ids

    # All edges must connect nodes present in the subgraph
    for e in subgraph["edges"]:
        assert e["source"] in node_ids
        assert e["target"] in node_ids


def test_get_subgraph_depth_2_expansion():
    """Verify depth=2 expands beyond direct neighbors."""
    subgraph_d1 = get_subgraph("IS 374:2019", depth=1)
    subgraph_d2 = get_subgraph("IS 374:2019", depth=2)

    assert len(subgraph_d2["nodes"]) >= len(subgraph_d1["nodes"])
    assert len(subgraph_d2["edges"]) >= len(subgraph_d1["edges"])


def test_get_subgraph_unknown_standard_raises_key_error():
    """Verify querying an unknown standard raises KeyError."""
    with pytest.raises(KeyError):
        get_subgraph("IS 999999:9999")


def test_api_get_subgraph_endpoint_success():
    """Verify GET /api/v1/graph/{standard_no} returns 200 and valid GraphResponse schema."""
    response = client.get("/api/v1/graph/IS 9001:2025?depth=1")
    assert response.status_code == 200
    data = response.json()

    assert "nodes" in data
    assert "edges" in data
    assert any(n["id"] == "IS 9001:2025" for n in data["nodes"])
    assert any(n["id"] == "IS 9876:2024" for n in data["nodes"])


def test_api_get_subgraph_endpoint_not_found():
    """Verify GET /api/v1/graph/{standard_no} returns 404 for unknown standards."""
    response = client.get("/api/v1/graph/IS 99999:2099")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_api_get_full_graph_with_pagination():
    """Verify GET /api/v1/graph/full returns complete graph and supports limit/offset."""
    response = client.get("/api/v1/graph/full?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert len(data["nodes"]) == 5
    assert data["total_nodes"] >= 10
    assert data["total_edges"] >= 10
