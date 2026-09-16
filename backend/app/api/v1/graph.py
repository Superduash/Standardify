"""
Standardify — GET /api/v1/graph/{standard_no}
              GET /api/v1/graph/full

Returns a NetworkX-derived subgraph (or full graph) in the
react-force-graph node-link JSON format:
  { nodes: [{id, label, status}], edges: [{source, target, relation}] }

Phase 0 stub: routes not yet implemented — wired in Phase 6.4.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
