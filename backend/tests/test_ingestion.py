"""
Tests for the ingestion pipeline (Phase 1).

Covers:
  - pdf_extract.extract_document() returns PageText with correct fields
  - clause_chunker.chunk_document() produces chunks within token limits
  - metadata_extractor.tag_chunk() correctly tags known standard excerpts
  - embed_and_store idempotency (double-run does not duplicate Chroma vectors)

Phase 0 stub: test skeletons only — implemented in Phase 1 alongside each module.
"""
from __future__ import annotations
