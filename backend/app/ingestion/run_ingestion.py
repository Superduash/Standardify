"""
Standardify — CLI orchestrator for the full ingestion pipeline.

Runs the complete pipeline end-to-end in this order:
  1. pdf_extract      — extract text from raw PDFs in data/raw_pdfs/
  2. clause_chunker   — split into clause-level chunks
  3. metadata_extractor — tag each chunk with standard_no, clause_no, etc.
  4. SQLite registry  — upsert StandardMeta rows into data/registry.db
  5. embed_and_store  — batch-embed chunks and upsert into ChromaDB

Flags:
  --validate   After ingestion, run 5 hand-picked queries and print top-3
               retrieved clauses for manual eyeball correctness check.
  --dry-run    Parse and chunk only; skip embedding and DB writes.

Phase 0 stub: no logic yet — implemented across Phases 1.1–1.6.
"""
from __future__ import annotations
