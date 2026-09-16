"""
Tests for the standards relationship graph (Phase 6).

Covers:
  - graph_engine.load_graph() logs node/edge counts and reuses in-memory graph
  - get_subgraph(standard_no, depth=1) returns correct neighbor set
  - GET /api/v1/graph/{standard_no} returns valid react-force-graph JSON
  - GET /api/v1/graph/full returns paginated/capped response

Phase 0 stub: test skeletons only — implemented in Phase 6.4.
"""
from __future__ import annotations
