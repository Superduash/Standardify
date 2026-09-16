"""
Standardify — LlamaIndex + ChromaDB hybrid retrieval engine.

Exposes:
  get_index()  → VectorStoreIndex backed by the Chroma bis_clauses collection
  retrieve(question, top_k, standard_filter) → list[RetrievedClause]
    Combines BGE-M3 dense semantic search with a BM25 keyword boost and
    re-ranks by combined score. Supports optional standard_no metadata filter.

All ChromaDB access goes through this module — API routes never touch
chromadb directly.

Phase 0 stub: no logic yet — implemented in Phases 2.2 and 2.3.
"""
from __future__ import annotations
