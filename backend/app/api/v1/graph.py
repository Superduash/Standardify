"""
Standardify — GET /api/v1/graph/full & GET /api/v1/graph/{standard_no} (Phase 6.4).

Provides NetworkX-derived inter-standard relationship subgraphs and full network graphs
formatted for frontend visualization libraries (e.g. react-force-graph).
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.graph_engine import get_full_graph, get_subgraph
from app.models.schemas import GraphEdge, GraphNode, GraphResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Standards Relationship Graph"])


@router.get(
    "/full",
    response_model=GraphResponse,
    summary="Retrieve full standards relationship graph",
    description="Returns the full network of BIS standards nodes and relationship edges with pagination support.",
)
async def get_full_graph_endpoint(
    limit: int = Query(default=100, ge=1, le=500, description="Max number of nodes to return"),
    offset: int = Query(default=0, ge=0, description="Node offset for pagination"),
) -> GraphResponse:
    """
    Retrieve paginated full graph structure.
    """
    try:
        data = get_full_graph(limit=limit, offset=offset)
        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
            total_nodes=data.get("total_nodes"),
            total_edges=data.get("total_edges"),
        )
    except Exception as exc:
        logger.error("Error retrieving full graph: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve standards graph: {exc}",
        ) from exc


@router.get(
    "/{standard_no}",
    response_model=GraphResponse,
    summary="Retrieve localized subgraph for a standard",
    description="Returns direct (or N-hop) neighbor relationships for a specific Indian Standard using BFS exploration.",
)
async def get_subgraph_endpoint(
    standard_no: str,
    depth: int = Query(default=1, ge=1, le=3, description="Exploration depth for neighbor extraction (1-3)"),
) -> GraphResponse:
    """
    Retrieve subgraph around a specific standard.
    """
    clean_std = standard_no.strip()
    if not clean_std:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Standard number parameter cannot be empty.",
        )

    try:
        data = get_subgraph(clean_std, depth=depth)
        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
            total_nodes=data.get("total_nodes"),
            total_edges=data.get("total_edges"),
        )
    except KeyError as exc:
        logger.warning("Standard '%s' not found in graph: %s", clean_std, exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Standard '{clean_std}' was not found in the relationship graph.",
        ) from exc
    except Exception as exc:
        logger.error("Error retrieving subgraph for '%s': %s", clean_std, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subgraph: {exc}",
        ) from exc
