"""
Standardify — Ingestion CLI entrypoint.

Usage (from repo root):
    python backend/ingest.py

Or from the backend/ directory:
    python ingest.py

Reads .env for config (STANDARDS_RAW_PATH, CHROMA_PATH, EMBEDDING_MODEL, CHROMA_COLLECTION).
All settings have sane defaults so this works with zero configuration.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure the backend/ directory is on sys.path so `app` package resolves
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Change working directory to backend/ so relative paths in .env resolve correctly
os.chdir(backend_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest")


def main() -> None:
    from app.core.config import get_settings
    from app.services.ingestion_service import ingest_directory

    settings = get_settings()

    logger.info("=" * 60)
    logger.info("Standardify — Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info("Standards directory : %s", settings.resolved_standards_raw_path())
    logger.info("ChromaDB path       : %s", settings.resolved_chroma_path())
    logger.info("Embedding model     : %s", settings.embedding_model)
    logger.info("Collection name     : %s", settings.chroma_collection)
    logger.info("=" * 60)

    total = ingest_directory(
        raw_dir=str(settings.resolved_standards_raw_path()),
        chroma_path=str(settings.resolved_chroma_path()),
        collection_name=settings.chroma_collection,
        embedding_model=settings.embedding_model,
    )

    if total > 0:
        logger.info("✓ Ingestion complete: %d chunks indexed", total)
    else:
        logger.warning("⚠ No chunks were indexed. Check that standards_raw/ contains .txt or .pdf files.")


if __name__ == "__main__":
    main()
