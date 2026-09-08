"""
Standardify — Ingestion Service.

Reads all .txt and .pdf files from the standards_raw directory,
extracts text, splits into chunks with LlamaIndex's SentenceSplitter,
embeds with BGE-M3, and upserts into ChromaDB.

Run standalone via: python backend/ingest.py
"""
from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_text_from_pdf(path: Path) -> str:
    """
    Primary: PyMuPDF.
    Fallback per page: pdfplumber if PyMuPDF yields < 20 chars.
    Last resort per page: pytesseract (OCR) if pdfplumber also yields < 20 chars.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed — skipping PDF: %s", path)
        return ""

    pages_text: list[str] = []
    doc = fitz.open(str(path))

    try:
        import pdfplumber
        plumber_doc: Optional[Any] = pdfplumber.open(str(path))
    except ImportError:
        plumber_doc = None

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()

        if len(text) < 20 and plumber_doc is not None:
            try:
                pb_page = plumber_doc.pages[page_num]
                text = (pb_page.extract_text() or "").strip()
            except Exception:
                pass

        if len(text) < 20:
            try:
                import pytesseract
                from PIL import Image
                import io
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img).strip()
            except Exception:
                pass

        pages_text.append(text)

    if plumber_doc is not None:
        try:
            plumber_doc.close()
        except Exception:
            pass
    doc.close()
    return "\n\n".join(pages_text)


def _parse_metadata_from_filename(filename: str) -> dict[str, str]:
    """
    Heuristically extract standard_no and title from filename.
    Expected pattern: IS_XXXX_YYYY_description.txt
    """
    stem = Path(filename).stem
    parts = stem.split("_")
    standard_no = ""
    title = stem.replace("_", " ")

    if len(parts) >= 3 and parts[0].upper() == "IS":
        try:
            number = parts[1]
            year = parts[2]
            standard_no = f"IS {number}:{year}"
            desc = " ".join(parts[3:]).replace("_", " ")
            title = f"IS {number}:{year} — {desc.title()}"
        except (IndexError, ValueError):
            pass

    return {"standard_no": standard_no, "title": title}


def _extract_clause_number(text: str) -> str:
    """Try to find a leading clause number in a chunk."""
    match = re.match(r"^\s*(\d+(?:\.\d+)*)\s*[.\-—]", text.strip())
    if match:
        return match.group(1)
    return ""


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[str]:
    """
    Use LlamaIndex's SentenceSplitter for semantic chunking.
    Falls back to simple sliding-window split if LlamaIndex is unavailable.
    """
    try:
        from llama_index.core.node_parser import SentenceSplitter
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        nodes = splitter.split_text(text)
        return [n for n in nodes if n.strip()]
    except Exception as exc:
        logger.warning("LlamaIndex chunking failed (%s) — using simple split", exc)
        words = text.split()
        chunks: list[str] = []
        step = max(1, chunk_size - chunk_overlap)
        for i in range(0, len(words), step):
            chunk = " ".join(words[i: i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks


# ── Main ingestion pipeline ───────────────────────────────────────────────────

def ingest_directory(
    raw_dir: str,
    chroma_path: str,
    collection_name: str,
    embedding_model: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> int:
    """
    Ingest all .txt and .pdf files from raw_dir.
    Returns the total number of chunks upserted.
    """
    from app.services.embeddings_service import EmbeddingsService
    from app.services.vector_store import VectorStore

    raw_path = Path(raw_dir)
    if not raw_path.exists():
        logger.error("standards_raw directory not found: %s", raw_dir)
        return 0

    files = list(raw_path.glob("*.txt")) + list(raw_path.glob("*.pdf"))
    if not files:
        logger.warning("No .txt or .pdf files found in %s", raw_dir)
        return 0

    logger.info("Loading embedding model '%s'...", embedding_model)
    emb_service = EmbeddingsService(embedding_model)

    logger.info("Connecting to ChromaDB at '%s'...", chroma_path)
    vector_store = VectorStore(persist_directory=chroma_path, collection_name=collection_name)

    total_chunks = 0

    for file_path in files:
        logger.info("Processing: %s", file_path.name)
        file_meta = _parse_metadata_from_filename(file_path.name)

        if file_path.suffix.lower() == ".pdf":
            raw_text = _extract_text_from_pdf(file_path)
        else:
            raw_text = _extract_text_from_txt(file_path)

        if not raw_text.strip():
            logger.warning("  No text extracted from %s — skipping", file_path.name)
            continue

        # Try to extract a richer title from the first line of the document
        first_line = raw_text.strip().splitlines()[0].strip()
        if len(first_line) > 10:
            file_meta["title"] = first_line[:200]

        chunks = _chunk_text(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info("  Extracted %d chunks", len(chunks))

        ids: list[str] = []
        embeddings_list: list[list[float]] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{file_path.name}:{i}:{chunk[:64]}".encode()).hexdigest()
            clause_no = _extract_clause_number(chunk)
            meta: dict[str, Any] = {
                "standard_no": file_meta["standard_no"],
                "title": file_meta["title"],
                "clause_no": clause_no,
                "page": i,  # chunk index used as page proxy for .txt files
                "source_file": file_path.name,
            }
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(meta)

        # Embed in batches
        batch_size = 32
        all_embeddings: list[list[float]] = []
        for b_start in range(0, len(documents), batch_size):
            batch = documents[b_start: b_start + batch_size]
            all_embeddings.extend(emb_service.encode(batch))

        vector_store.upsert(
            ids=ids,
            embeddings=all_embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)
        logger.info("  Upserted %d chunks for %s", len(chunks), file_meta["standard_no"])

    logger.info("Ingestion complete. Total chunks: %d", total_chunks)
    return total_chunks
