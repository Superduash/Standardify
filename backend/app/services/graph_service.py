"""
Standardify — Knowledge Graph Service.

Loads graph_relationships.json at startup into a NetworkX DiGraph.
Exposes methods to get related standards and to serialise the graph
to react-force-graph's {nodes, links} format.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import networkx as nx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, json_path: str) -> None:
        self._graph = nx.DiGraph()
        self._node_data: dict[str, dict[str, Any]] = {}
        self._load(json_path)

    def _load(self, json_path: str) -> None:
        path = Path(json_path)
        if not path.exists():
            logger.warning("Graph JSON not found at '%s' — graph will be empty", json_path)
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for node in data.get("nodes", []):
            node_id = node["id"]
            self._graph.add_node(node_id, **node)
            self._node_data[node_id] = node

        for edge in data.get("edges", []):
            src = edge["source"]
            tgt = edge["target"]
            # Skip self-loops that were used only for category metadata
            if src != tgt:
                self._graph.add_edge(src, tgt, **edge)

        logger.info(
            "Knowledge graph loaded: %d nodes, %d edges",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
        )

    def get_related(self, standard_id: str) -> list[dict[str, Any]]:
        """Return neighbours (successors + predecessors) with edge metadata."""
        if standard_id not in self._graph:
            return []
        related: list[dict[str, Any]] = []
        for neighbour in self._graph.successors(standard_id):
            edge_data = self._graph.get_edge_data(standard_id, neighbour, {})
            related.append(
                {
                    "node": self._node_data.get(neighbour, {"id": neighbour}),
                    "relation": edge_data.get("relation", "related"),
                    "direction": "outgoing",
                }
            )
        for neighbour in self._graph.predecessors(standard_id):
            edge_data = self._graph.get_edge_data(neighbour, standard_id, {})
            related.append(
                {
                    "node": self._node_data.get(neighbour, {"id": neighbour}),
                    "relation": edge_data.get("relation", "related"),
                    "direction": "incoming",
                }
            )
        return related

    def to_json(self) -> dict[str, Any]:
        """
        Serialise to react-force-graph format:
        { nodes: [...], links: [...] }
        """
        nodes = [
            {
                "id": n,
                "standard_no": attrs.get("standard_no", n),
                "title": attrs.get("title", ""),
                "category": attrs.get("category", ""),
                "year": attrs.get("year", 0),
            }
            for n, attrs in self._graph.nodes(data=True)
        ]
        links = [
            {
                "source": u,
                "target": v,
                "relation": attrs.get("relation", "related"),
                "label": attrs.get("label", ""),
            }
            for u, v, attrs in self._graph.edges(data=True)
        ]
        return {"nodes": nodes, "links": links}


# Module-level singleton
_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    global _graph_service
    if _graph_service is None:
        settings = get_settings()
        _graph_service = GraphService(str(settings.resolved_graph_json_path()))
    return _graph_service
