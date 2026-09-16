"""
Standardify — Clause-level document chunker.

Splits per-page extracted text from pdf_extract.py into clause-sized chunks
(target 150–400 tokens, hard cap ~500 tokens) using BIS numbered-clause patterns
(e.g. '4.2', '5.1.3') as primary split points. Falls back to paragraph-based
splitting where no clause numbering is detected.

Exposes:
  Clause: dataclass(text, approx_clause_no, page_no)
  chunk_document(pages: Sequence[PageText]) -> list[Clause]
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional, Sequence

from app.ingestion.pdf_extract import PageText

# Sizing thresholds
HARD_MAX_TOKENS: int = 500

# Regex to detect BIS clause headers at the start of a line
# Matches e.g. "4.1 Material requirements", "5.1.3 Test procedure", "Clause 4.2", "1 SCOPE"
CLAUSE_HEADING_REGEX = re.compile(
    r'^(?:(?:CLAUSE|Clause|SECTION|Section)\s+)?'
    r'('
    r'\d+(?:\.\d+)+'                              # e.g. 4.1, 5.1.3, 7.2.1.4
    r'|'
    r'\b[1-9]\d{0,1}\b(?=\s+[A-Z][a-zA-Z0-9])'     # e.g. "1 SCOPE", "4 REQUIREMENTS"
    r')'
    r'(?:\.|\:)?'                                  # optional dot/colon
    r'(?:\s+(.*))?$',                              # remainder of the heading
    re.MULTILINE,
)


@dataclass(frozen=True)
class Clause:
    """
    Structured representation of a clause-level document chunk.

    Attributes:
        text: Cleaned text content of the clause chunk.
        approx_clause_no: Detected BIS clause number (e.g. '4.2', '5.1.3') or None.
        page_no: 1-indexed page number where this chunk resides.
    """

    text: str
    approx_clause_no: Optional[str]
    page_no: int


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text snippet.

    Uses a robust ~1.3 tokens/word heuristic for technical text.

    Args:
        text: Text string to evaluate.

    Returns:
        Estimated token count.
    """
    words = text.split()
    if not words:
        return 0
    return max(1, int(len(words) * 1.3))


def _split_oversized_text(text: str, max_tokens: int = HARD_MAX_TOKENS) -> list[str]:
    """
    Split a block of text that exceeds max_tokens into smaller logical pieces.

    Splits progressively along paragraph boundaries, then sentence boundaries,
    and finally word boundaries if necessary.

    Args:
        text: Text content to split.
        max_tokens: Maximum allowed token threshold per sub-chunk.

    Returns:
        List of sub-chunk strings each respecting max_tokens.
    """
    if estimate_tokens(text) <= max_tokens:
        return [text]

    # Try splitting by paragraph
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        chunks: list[str] = []
        current_paras: list[str] = []
        for p in paragraphs:
            candidate = "\n\n".join(current_paras + [p])
            if estimate_tokens(candidate) > max_tokens and current_paras:
                chunks.extend(_split_oversized_text("\n\n".join(current_paras), max_tokens))
                current_paras = [p]
            else:
                current_paras.append(p)
        if current_paras:
            chunks.extend(_split_oversized_text("\n\n".join(current_paras), max_tokens))
        return chunks

    # If a single paragraph is too large, split by sentence
    sentences = re.split(r'(?<=[.?!;])\s+', text)
    if len(sentences) > 1:
        chunks = []
        current_sentences: list[str] = []
        for s in sentences:
            candidate = " ".join(current_sentences + [s])
            if estimate_tokens(candidate) > max_tokens and current_sentences:
                chunks.extend(_split_oversized_text(" ".join(current_sentences), max_tokens))
                current_sentences = [s]
            else:
                current_sentences.append(s)
        if current_sentences:
            chunks.extend(_split_oversized_text(" ".join(current_sentences), max_tokens))
        return chunks

    # Fallback: Split by words if a single sentence exceeds the token limit
    words = text.split()
    chunks = []
    word_chunk_size = max(1, int(max_tokens / 1.3))
    for i in range(0, len(words), word_chunk_size):
        chunk_words = words[i : i + word_chunk_size]
        chunks.append(" ".join(chunk_words))
    return chunks


def _chunk_page_text(page_text: str, page_no: int) -> list[Clause]:
    """
    Parse a single page's text into Clause objects based on clause numbering or paragraphs.

    Args:
        page_text: Raw or normalized text from one page.
        page_no: 1-indexed page number.

    Returns:
        List of Clause objects for the page.
    """
    if not page_text or not page_text.strip():
        return []

    # Find all clause headings in the text
    matches = list(CLAUSE_HEADING_REGEX.finditer(page_text))

    raw_segments: list[tuple[Optional[str], str]] = []

    if matches:
        # Preamble before the first clause heading on the page
        first_start = matches[0].start()
        if first_start > 0:
            preamble = page_text[:first_start].strip()
            if preamble:
                raw_segments.append((None, preamble))

        for idx, match in enumerate(matches):
            clause_no = match.group(1).strip()
            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(page_text)
            clause_content = page_text[start_pos:end_pos].strip()
            if clause_content:
                raw_segments.append((clause_no, clause_content))
    else:
        # No clause numbering found: split by double newline paragraphs
        paragraphs = [p.strip() for p in page_text.split("\n\n") if p.strip()]
        if paragraphs:
            for p in paragraphs:
                raw_segments.append((None, p))
        else:
            raw_segments.append((None, page_text.strip()))

    # Process and bundle segments into optimal token sizes
    final_clauses: list[Clause] = []

    for clause_no, content in raw_segments:
        # If content exceeds hard max tokens, split it into sub-chunks
        if estimate_tokens(content) > HARD_MAX_TOKENS:
            sub_chunks = _split_oversized_text(content, max_tokens=HARD_MAX_TOKENS)
            for sub in sub_chunks:
                if sub.strip():
                    final_clauses.append(
                        Clause(
                            text=sub.strip(),
                            approx_clause_no=clause_no,
                            page_no=page_no,
                        )
                    )
        else:
            final_clauses.append(
                Clause(
                    text=content.strip(),
                    approx_clause_no=clause_no,
                    page_no=page_no,
                )
            )

    return final_clauses


def chunk_document(pages: Sequence[PageText]) -> List[Clause]:
    """
    Split a document's extracted pages into a flat sequence of clause-level chunks.

    Args:
        pages: Sequence of PageText objects from Phase 1.1 extraction.

    Returns:
        List of Clause objects preserving clause numbering and page context.
    """
    document_clauses: list[Clause] = []

    for page in pages:
        page_clauses = _chunk_page_text(page.raw_text, page.page_no)
        document_clauses.extend(page_clauses)

    return document_clauses
