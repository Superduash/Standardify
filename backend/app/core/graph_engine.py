"""
Standardify — NetworkX graph engine.

Manages the standards relationship graph persisted at data/graph.json.
Loaded ONCE at startup, never rebuilt per-request.

Exposes:
  build_graph()  → builds DiGraph from ingested relationship data, saves to disk
  load_graph()   → loads DiGraph from data/graph.json (called at startup)
  get_subgraph(standard_no, depth=1) → {nodes, edges} in react-force-graph format

Nodes: standard_no (attrs: title, status, category)
Edges: relation type — "supersedes" | "references" | "same_category"

Phase 0 stub: no logic yet — implemented in Phases 6.2 and 6.3.
"""
from __future__ import annotations
