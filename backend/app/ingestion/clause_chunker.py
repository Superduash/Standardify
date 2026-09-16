"""
Standardify — Clause-level document chunker.

Splits per-page raw text from pdf_extract.py into clause-sized chunks
(target 150–400 tokens, hard cap ~500 tokens) using BIS's numbered-clause
pattern (e.g. 4.2, 5.1.3) as split points. Falls back to paragraph
splitting where no clause numbering is detected.

Exposes:
  chunk_document(pages: list[PageText]) -> list[Clause]

Phase 0 stub: no logic yet — implemented in Phase 1.2.
"""
from __future__ import annotations
