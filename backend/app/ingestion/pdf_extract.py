"""
Standardify — PDF text extraction (PyMuPDF primary, pdfplumber fallback, pytesseract OCR).

Exposes:
  extract_document(path: str | Path) -> list[PageText]
    PageText: page_no, raw_text, used_ocr (bool)

Extraction Flow (Phase 1.1):
  1. Open document via PyMuPDF (fitz) for fast, primary digital text extraction.
  2. For each page, evaluate text quality (meaningful character threshold).
  3. If text is near-empty, fall back to pdfplumber for table/layout extraction on that page.
  4. If text remains insufficient, rasterize the page and apply pytesseract OCR.
  5. OCR is only triggered when strictly necessary — never on pages with usable digital text.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import logging
from pathlib import Path
from typing import List, Union

import fitz  # PyMuPDF
from PIL import Image

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore[assignment]

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Minimum number of alphanumeric characters required to consider extraction usable
MIN_USABLE_ALPHANUMERIC_CHARS: int = 20


@dataclass(frozen=True)
class PageText:
    """
    Extracted text content and metadata for an individual document page.

    Attributes:
        page_no: 1-indexed page number within the source document.
        raw_text: Normalized extracted text string.
        used_ocr: True if optical character recognition was executed for this page.
    """

    page_no: int
    raw_text: str
    used_ocr: bool = False

    @property
    def text(self) -> str:
        """Convenience alias for raw_text."""
        return self.raw_text


def _clean_text(text: str | None) -> str:
    """
    Normalize whitespace and line endings while preserving clause and paragraph structure.

    Args:
        text: Raw text string to normalize.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # Standardize newline characters
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    cleaned_lines: list[str] = []
    blank_streak = 0

    for line in lines:
        cleaned = " ".join(line.split())
        if not cleaned:
            blank_streak += 1
            # Allow at most one consecutive empty line (paragraph separation)
            if blank_streak <= 1:
                cleaned_lines.append("")
        else:
            blank_streak = 0
            cleaned_lines.append(cleaned)

    return "\n".join(cleaned_lines).strip()


def _is_usable_text(text: str, min_chars: int = MIN_USABLE_ALPHANUMERIC_CHARS) -> bool:
    """
    Determine whether extracted page text contains sufficient meaningful characters.

    Args:
        text: Text string to evaluate.
        min_chars: Threshold of alphanumeric characters.

    Returns:
        True if text contains at least min_chars alphanumeric characters.
    """
    if not text:
        return False
    alphanumeric_count = sum(1 for char in text if char.isalnum())
    return alphanumeric_count >= min_chars


def _ocr_page(page: fitz.Page, dpi: int = 200) -> str:
    """
    Rasterize a single PDF page and perform OCR using pytesseract.

    Args:
        page: PyMuPDF Page object to rasterize.
        dpi: Resolution for page rasterization (default: 200 DPI).

    Returns:
        Extracted text from OCR, or empty string on failure.
    """
    if pytesseract is None:
        logger.warning("pytesseract is not installed; OCR fallback skipped.")
        return ""

    try:
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_result = pytesseract.image_to_string(img)
        return ocr_result or ""
    except Exception as exc:
        logger.warning("OCR failed on page %s: %s", getattr(page, "number", "?"), exc)
        return ""


def extract_document(path: Union[str, Path]) -> List[PageText]:
    """
    Extract text from a PDF document using a multi-tiered per-page strategy.

    Strategy:
      1. PyMuPDF (fitz) text extraction.
      2. pdfplumber fallback if PyMuPDF yields near-empty text.
      3. pytesseract OCR fallback if pdfplumber also yields near-empty text.

    Args:
        path: Path to the PDF file.

    Returns:
        List of PageText objects preserving 1-indexed page numbers, extracted text, and OCR status.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid or readable PDF.
    """
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Specified path is not a PDF file: {pdf_path}")

    pages: list[PageText] = []
    plumber_doc = None

    try:
        with fitz.open(pdf_path) as doc:
            if doc.page_count == 0:
                raise ValueError(f"PDF contains no pages: {pdf_path}")

            for page_idx in range(doc.page_count):
                page_no = page_idx + 1
                page = doc[page_idx]
                used_ocr = False

                # Step 1: Primary extraction with PyMuPDF
                fitz_raw = page.get_text("text")
                cleaned_text = _clean_text(fitz_raw)

                # Step 2: Fallback to pdfplumber if text is insufficient
                if not _is_usable_text(cleaned_text):
                    if pdfplumber is not None:
                        try:
                            if plumber_doc is None:
                                plumber_doc = pdfplumber.open(pdf_path)
                            if page_idx < len(plumber_doc.pages):
                                plumber_page = plumber_doc.pages[page_idx]
                                plumber_raw = plumber_page.extract_text()
                                plumber_cleaned = _clean_text(plumber_raw)
                                if _is_usable_text(plumber_cleaned):
                                    cleaned_text = plumber_cleaned
                        except Exception as exc:
                            logger.debug("pdfplumber fallback error on page %d: %s", page_no, exc)

                # Step 3: Fallback to pytesseract OCR if still insufficient
                if not _is_usable_text(cleaned_text):
                    ocr_raw = _ocr_page(page)
                    ocr_cleaned = _clean_text(ocr_raw)
                    if ocr_cleaned:
                        cleaned_text = ocr_cleaned
                    used_ocr = True

                pages.append(
                    PageText(
                        page_no=page_no,
                        raw_text=cleaned_text,
                        used_ocr=used_ocr,
                    )
                )

    except fitz.FileDataError as exc:
        raise ValueError(f"Corrupt or invalid PDF file: {pdf_path}") from exc
    finally:
        if plumber_doc is not None:
            try:
                plumber_doc.close()
            except Exception:
                pass

    return pages
