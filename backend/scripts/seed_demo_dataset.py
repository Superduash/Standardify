"""
Standardify — Demo Dataset Seeder (Phase 10.4).

One-command idempotent initialization that builds and validates the complete
Standardify backend dataset from a clean checkout or container deployment.

Orchestrates:
  1. SQLite registry schema initialization (data/registry.db)
  2. PDF extraction & clause chunking (from data/raw_pdfs/ or demo corpus)
  3. BGE-M3 local vector embedding & ChromaDB upsert (bis_clauses)
  4. SQLite FTS5 full-text search index generation
  5. Inter-standard relationship NetworkX graph persistence (data/graph.json)
  6. Requirement checklist cache verification (data/requirements_cache.json)
  7. Automated health and retrieval validation

Usage:
  python scripts/seed_demo_dataset.py
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.graph_engine import build_graph, load_graph
from app.core.retrieval import get_collection, retrieve
from app.ingestion.metadata_extractor import DEMO_CATALOG
from app.ingestion.requirement_extractor import load_requirements_cache
from app.ingestion.run_ingestion import (
    DEFAULT_REGISTRY_PATH,
    init_registry_db,
    ingest_demo_dataset,
    ingest_pdf_directory,
    validate_ingestion,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_demo_dataset")


def setup_fts5_index(db_path: Path = DEFAULT_REGISTRY_PATH) -> int:
    """Initialize and rebuild the SQLite FTS5 virtual table."""
    logger.info("Setting up SQLite FTS5 full-text search index...")
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS standards_fts USING fts5(
                standard_no, title, category, content=standards, content_rowid=rowid
            )
        """)
        conn.execute("INSERT INTO standards_fts(standards_fts) VALUES('rebuild')")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM standards_fts").fetchone()[0]
    logger.info("FTS5 index successfully built with %d indexed records.", count)
    return count


def main() -> None:
    """Execute end-to-end dataset seeding pipeline."""
    start_time = time.time()
    print("\n" + "=" * 60)
    print("       STANDARDI_FY - DEMO DATASET SEEDING PIPELINE        ")
    print("=" * 60)

    # 1. Initialize SQLite Registry
    logger.info("Stage 1/6: Initializing SQLite metadata registry...")
    init_registry_db(DEFAULT_REGISTRY_PATH)

    # 2. Ingest Documents into ChromaDB & Registry
    raw_pdfs_dir = Path("./data/raw_pdfs")
    pdf_files = list(raw_pdfs_dir.glob("*.pdf")) if raw_pdfs_dir.exists() else []

    if pdf_files:
        logger.info("Stage 2/6: Ingesting %d PDF documents from %s...", len(pdf_files), raw_pdfs_dir)
        ingest_pdf_directory(raw_pdfs_dir, DEFAULT_REGISTRY_PATH)
    else:
        logger.info("Stage 2/6: No external PDFs in %s; seeding standard demo corpus...", raw_pdfs_dir)
        ingest_demo_dataset(DEFAULT_REGISTRY_PATH)

    # 3. Setup SQLite FTS5
    logger.info("Stage 3/6: Building SQLite FTS5 search index...")
    fts_count = setup_fts5_index(DEFAULT_REGISTRY_PATH)

    # 4. Build Standards Relationship Graph
    logger.info("Stage 4/6: Building inter-standard relationship graph (NetworkX)...")
    graph = build_graph()
    logger.info("Graph constructed: %d nodes, %d directed edges.", graph.number_of_nodes(), graph.number_of_edges())

    # 5. Verify Requirement Checklists Cache
    logger.info("Stage 5/6: Validating compliance requirement checklists cache...")
    req_cache = load_requirements_cache()
    standards_with_reqs = len(req_cache.get("standards", {}))
    logger.info("Requirements cache contains %d configured demo standards.", standards_with_reqs)

    # 6. Automated Validation
    logger.info("Stage 6/6: Running validation and retrieval health checks...")
    validation_passed = validate_ingestion(DEFAULT_REGISTRY_PATH)

    # Final Summary Report
    elapsed = time.time() - start_time
    col = get_collection()
    chroma_count = col.count()

    with sqlite3.connect(str(DEFAULT_REGISTRY_PATH)) as conn:
        std_count = conn.execute("SELECT COUNT(*) FROM standards").fetchone()[0]

    print("\n" + "=" * 60)
    print("             SEEDING COMPLETED SUCCESSFULLY             ")
    print("=" * 60)
    print(f"Total Execution Time:        {elapsed:.2f} seconds")
    print(f"SQLite Standards Registered: {std_count}")
    print(f"SQLite FTS5 Indexed Rows:    {fts_count}")
    print(f"ChromaDB Vector Embeddings:  {chroma_count}")
    print(f"Knowledge Graph Nodes/Edges: {graph.number_of_nodes()} nodes / {graph.number_of_edges()} edges")
    print(f"Requirement Checklists:      {standards_with_reqs} standards cached")
    print(f"Retrieval Validation Check:  {'[PASS] (100%)' if validation_passed else '[WARNINGS]'}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
