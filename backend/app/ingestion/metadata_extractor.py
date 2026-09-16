"""
Standardify — Regex-based metadata extractor.

Extracts per-chunk metadata from raw BIS standard text:
  - standard_no  (e.g. "IS 374:2019")
  - clause_no    (e.g. "4.2.1")
  - section_title
  - document_title
  - category     (manual mapping table for demo corpus — not a classifier)

Chunks that cannot be tagged are flagged needs_review=True rather than
silently dropped.

Exposes:
  tag_chunk(chunk: Clause, document_header: str) -> Clause  (with metadata filled)
  extract_standard_meta(header_text: str) -> StandardMeta

Phase 0 stub: no logic yet — implemented in Phase 1.3.
"""
from __future__ import annotations
