"""
Standardify — Standards relationship extractor (offline, runs during ingestion).

Performs a regex pass over each document's foreword/scope text to detect:
  - "supersedes IS XXXX"   → supersedes edge
  - "this standard is based on ..." → references edge
  - "reference is made to IS XXXX" → references edge
  - same-category membership → same_category edges

Edges feed into app/core/graph_engine.py to build the NetworkX DiGraph.
For the small demo corpus, extracted edges are hand-verified and stored
in data/graph.json — this is the correct scope for the demo (not a shortcut).

Exposes:
  extract_relationships(standard_no: str, text: str) -> list[RelationshipEdge]

Phase 0 stub: no logic yet — implemented in Phase 6.1.
"""
from __future__ import annotations
