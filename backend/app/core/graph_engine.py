"""
Standardify — Standards Relationship Graph Engine (Phase 6.2 & 6.3).

Maintains a persistent NetworkX DiGraph representing inter-standard relationships
(supersedes, references, same_category). Loaded once at startup and reused in memory.

Exposes:
  build_graph() -> nx.DiGraph
  load_graph(force_reload: bool = False) -> nx.DiGraph
  get_subgraph(standard_no: str, depth: int = 1) -> dict[str, Any]
  get_full_graph(limit: int = 100, offset: int = 0) -> dict[str, Any]
"""

from __future__ import annotations

from collections import deque
import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from app.ingestion.relationship_extractor import get_curated_relationships

logger = logging.getLogger(__name__)

GRAPH_FILE_PATH = Path("./data/graph.json")

# In-memory graph singleton
_GRAPH_INSTANCE: Optional[nx.DiGraph] = None


def build_graph() -> nx.DiGraph:
    """
    Construct NetworkX DiGraph from curated demo relationships and persist to data/graph.json.
    """
    nodes, edges = get_curated_relationships()
    G = nx.DiGraph()

    for node in nodes:
        node_id = node["id"]
        G.add_node(
            node_id,
            label=node.get("label", node_id),
            status=node.get("status", "Active"),
            category=node.get("category"),
        )

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        relation = edge["relation"]
        # Ensure target node exists even if not in explicit nodes list
        if not G.has_node(target):
            G.add_node(target, label=target, status="Active", category=None)
        G.add_edge(source, target, relation=relation)

    save_graph(G)
    logger.info("Built standards relationship graph with %d nodes and %d edges.", G.number_of_nodes(), G.number_of_edges())
    return G


def save_graph(G: nx.DiGraph) -> None:
    """
    Atomically save NetworkX DiGraph to data/graph.json in node-link format.
    """
    GRAPH_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = nx.node_link_data(G)

    temp_dir = GRAPH_FILE_PATH.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name

    try:
        os.replace(temp_name, GRAPH_FILE_PATH)
        logger.info("Saved graph to %s", GRAPH_FILE_PATH)
    except Exception as exc:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise IOError(f"Failed to atomically write graph.json: {exc}") from exc


def load_graph(force_reload: bool = False) -> nx.DiGraph:
    """
    Load graph from data/graph.json into singleton memory cache.
    Builds graph if file does not exist.
    """
    global _GRAPH_INSTANCE

    if _GRAPH_INSTANCE is not None and not force_reload:
        return _GRAPH_INSTANCE

    if not GRAPH_FILE_PATH.exists() or force_reload:
        _GRAPH_INSTANCE = build_graph()
        return _GRAPH_INSTANCE

    try:
        with open(GRAPH_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _GRAPH_INSTANCE = nx.node_link_graph(data)
        logger.info(
            "Loaded in-memory standards graph: %d nodes, %d edges from %s",
            _GRAPH_INSTANCE.number_of_nodes(),
            _GRAPH_INSTANCE.number_of_edges(),
            GRAPH_FILE_PATH,
        )
        return _GRAPH_INSTANCE
    except Exception as exc:
        logger.error("Failed to load graph from %s (%s). Rebuilding fresh...", GRAPH_FILE_PATH, exc)
        _GRAPH_INSTANCE = build_graph()
        return _GRAPH_INSTANCE


def get_subgraph(standard_no: str, depth: int = 1) -> Dict[str, Any]:
    """
    Extract a localized subgraph around standard_no using BFS up to the given depth.
    Depth is clamped between 1 and 3.

    Returns:
        {
            "nodes": [{"id": ..., "label": ..., "status": ..., "category": ...}],
            "edges": [{"source": ..., "target": ..., "relation": ...}],
            "total_nodes": int,
            "total_edges": int
        }
    """
    G = load_graph()
    clean_std = standard_no.strip()

    # Case-insensitive or normalized lookup if needed
    matched_node = None
    if G.has_node(clean_std):
        matched_node = clean_std
    else:
        for n in G.nodes():
            if n.lower() == clean_std.lower():
                matched_node = n
                break

    if not matched_node:
        raise KeyError(f"Standard '{standard_no}' not found in standards relationship graph.")

    depth = max(1, min(depth, 3))

    # BFS exploration in undirected sense (both successors and predecessors)
    visited_nodes: Set[str] = {matched_node}
    queue: deque[Tuple[str, int]] = deque([(matched_node, 0)])

    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue

        neighbors = set(G.successors(current)) | set(G.predecessors(current))
        for neighbor in neighbors:
            if neighbor not in visited_nodes:
                visited_nodes.add(neighbor)
                queue.append((neighbor, current_depth + 1))

    # Build node and edge list for the visited nodes
    subgraph_nodes: List[Dict[str, Any]] = []
    for node_id in visited_nodes:
        attrs = G.nodes[node_id]
        subgraph_nodes.append({
            "id": node_id,
            "label": attrs.get("label", node_id),
            "status": attrs.get("status", "Active"),
            "category": attrs.get("category"),
        })

    subgraph_edges: List[Dict[str, str]] = []
    for u, v, data in G.edges(data=True):
        if u in visited_nodes and v in visited_nodes:
            subgraph_edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "references"),
            })

    return {
        "nodes": subgraph_nodes,
        "edges": subgraph_edges,
        "total_nodes": len(subgraph_nodes),
        "total_edges": len(subgraph_edges),
    }


def get_full_graph(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Return the complete standards graph with pagination/capping support.
    """
    G = load_graph()

    all_node_ids = list(G.nodes())
    total_nodes = len(all_node_ids)
    paginated_node_ids = set(all_node_ids[offset : offset + limit])

    nodes: List[Dict[str, Any]] = []
    for node_id in paginated_node_ids:
        attrs = G.nodes[node_id]
        nodes.append({
            "id": node_id,
            "label": attrs.get("label", node_id),
            "status": attrs.get("status", "Active"),
            "category": attrs.get("category"),
        })

    edges: List[Dict[str, str]] = []
    for u, v, data in G.edges(data=True):
        if u in paginated_node_ids and v in paginated_node_ids:
            edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "references"),
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": total_nodes,
        "total_edges": G.number_of_edges(),
    }
