"""
Standardify — PDF text extraction (PyMuPDF primary, pdfplumber fallback, pytesseract OCR).

Exposes:
  extract_document(path: Path) -> list[PageText]
    PageText: page_no, raw_text, used_ocr (bool)

Logic (Phase 1.1):
  1. Try PyMuPDF (fitz) — fast, high-quality for digital-text PDFs.
  2. If a page's extracted text is near-empty, fall back to pdfplumber.
  3. If still near-empty, rasterize the page and run pytesseract OCR.
  OCR is ONLY triggered when needed — never run on every page.

Phase 0 stub: no logic yet — implemented in Phase 1.1.
"""
from __future__ import annotations
