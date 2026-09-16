"""
Standardify — Batch embedding + ChromaDB upsert.

Reads tagged Clause objects produced by the ingestion pipeline, embeds them
in batches using app/core/embeddings.py (BGE-M3 singleton), and upserts into
the ChromaDB collection "bis_clauses".

ID scheme: f"{standard_no}::{clause_no}::{page_no}"  (stable, idempotent)
Metadata stored per vector: standard_no, clause_no, page_no, title, category

Re-running this script NEVER duplicates vectors — ChromaDB upsert ensures
idempotency (Golden Rule #6).

Depends on: Phase 2.1 (embeddings.py singleton) must be implemented first.

Phase 0 stub: no logic yet — implemented in Phase 1.5 (after Phase 2.1).
"""
from __future__ import annotations
