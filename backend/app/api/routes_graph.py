"""GET /api/graph"""
from __future__ import annotations

from fastapi import APIRouter

from app.services.graph_service import get_graph_service

router = APIRouter()


@router.get("/graph")
def get_graph() -> dict:
    """
    Returns the knowledge graph in react-force-graph format:
    { nodes: [...], links: [...] }
    """
    graph_service = get_graph_service()
    return graph_service.to_json()
