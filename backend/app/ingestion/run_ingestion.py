"""
Standardify — Ingestion orchestrator & SQLite metadata registry.

Manages standards metadata registry storage at data/registry.db, orchestrates
the ingestion pipeline stages, and runs automated retrieval QA validation.

CLI usage:
  python -m app.ingestion.run_ingestion
  python -m app.ingestion.run_ingestion --validate
  python -m app.ingestion.run_ingestion --dry-run
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import logging
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, Generator, List, Optional, Sequence

from app.ingestion.metadata_extractor import DEMO_CATALOG
from app.models.domain import Clause, StandardMeta

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_PATH = Path("./data/registry.db")

# Curated evaluation benchmark questions for Phase 1.6 Ingestion QA
QA_BENCHMARK_QUERIES: list[tuple[str, str]] = [
    (
        "What are the material and drop test safety requirements for plastic drinking water bottles?",
        "IS 9001:2025",
    ),
    (
        "What are the nutritional information and safety labelling specifications for packaged foods?",
        "IS 9004:2025",
    ),
    (
        "What are the mechanical and physical safety requirements for children's toys to prevent injury?",
        "IS 9002:2025",
    ),
    (
        "What are the protective impact and retention specifications for two-wheeler motorcycle helmets?",
        "IS 9003:2026",
    ),
    (
        "What are the speed performance and safety requirements for electric ceiling fans?",
        "IS 374:2019",
    ),
]


@contextmanager
def db_session(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for SQLite database connections, ensuring proper connection closure.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Yields:
        sqlite3.Connection: Active SQLite connection.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_registry_db(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
    """
    Create the standards registry schema if it does not already exist.

    Args:
        db_path: Filesystem path to the SQLite database file.
    """
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS standards (
                standard_no TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                status TEXT NOT NULL,
                superseded_by TEXT,
                last_amended_date TEXT,
                source_url TEXT
            )
            """
        )
        conn.commit()


def upsert_standard(meta: StandardMeta, db_path: Path | str = DEFAULT_REGISTRY_PATH) -> None:
    """
    Insert or update a single standard metadata record in the SQLite registry.

    Args:
        meta: StandardMeta instance to upsert.
        db_path: Filesystem path to the SQLite database file.
    """
    init_registry_db(db_path)
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO standards (
                standard_no, title, category, status, superseded_by, last_amended_date, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(standard_no) DO UPDATE SET
                title = excluded.title,
                category = excluded.category,
                status = excluded.status,
                superseded_by = excluded.superseded_by,
                last_amended_date = excluded.last_amended_date,
                source_url = excluded.source_url
            """,
            (
                meta.standard_no,
                meta.title,
                meta.category,
                meta.status or "Active",
                meta.superseded_by,
                meta.last_amended_date,
                meta.source_url,
            ),
        )
        conn.commit()


def seed_registry_with_demo_catalog(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> int:
    """
    Populate the SQLite registry with the curated demo standards catalog.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Returns:
        int: Number of standards upserted.
    """
    init_registry_db(db_path)
    count = 0
    for std_no, (title, category, status) in DEMO_CATALOG.items():
        meta = StandardMeta(
            standard_no=std_no,
            title=title,
            category=category,
            status=status,
            source_url=f"https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/{std_no.replace(' ', '_')}",
        )
        upsert_standard(meta, db_path=db_path)
        count += 1
    return count


def get_standard_meta(standard_no: str, db_path: Path | str = DEFAULT_REGISTRY_PATH) -> Optional[StandardMeta]:
    """
    Retrieve a standard metadata record by standard number.

    Args:
        standard_no: Unique identifier of the standard.
        db_path: Filesystem path to the SQLite database file.

    Returns:
        StandardMeta instance or None if not found.
    """
    init_registry_db(db_path)
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT standard_no, title, category, status, superseded_by, last_amended_date, source_url FROM standards WHERE standard_no = ?",
            (standard_no,),
        )
        row = cursor.fetchone()
        if row:
            return StandardMeta(
                standard_no=row["standard_no"],
                title=row["title"],
                category=row["category"],
                status=row["status"],
                superseded_by=row["superseded_by"],
                last_amended_date=row["last_amended_date"],
                source_url=row["source_url"],
            )
    return None


def list_all_standards(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> List[StandardMeta]:
    """
    List all standards currently registered in the database.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Returns:
        List of StandardMeta instances.
    """
    init_registry_db(db_path)
    standards: list[StandardMeta] = []
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT standard_no, title, category, status, superseded_by, last_amended_date, source_url FROM standards ORDER BY standard_no"
        )
        for row in cursor.fetchall():
            standards.append(
                StandardMeta(
                    standard_no=row["standard_no"],
                    title=row["title"],
                    category=row["category"],
                    status=row["status"],
                    superseded_by=row["superseded_by"],
                    last_amended_date=row["last_amended_date"],
                    source_url=row["source_url"],
                )
            )
    return standards


def validate_ingestion_qa(
    top_k: int = 3,
    persist_dir: Optional[str] = None,
    collection_name: str = "bis_clauses",
) -> Dict[str, Any]:
    """
    Run the Phase 1.6 Ingestion QA validation test suite against ChromaDB.

    Evaluates 5 benchmark queries and reports whether expected standards appear
    in top-K retrieved clauses.

    Args:
        top_k: Number of retrieved results to inspect per query.
        persist_dir: Optional Chroma persistence directory override.
        collection_name: Target vector collection name.

    Returns:
        Dict[str, Any]: Summary metrics containing accuracy, total questions, and hit details.
    """
    from app.core.embeddings import embed_query
    from app.ingestion.embed_and_store import get_chroma_client, get_or_create_collection

    client = get_chroma_client(persist_dir=persist_dir)
    collection = get_or_create_collection(client=client, collection_name=collection_name)

    total_chunks = collection.count()
    print(f"\n=======================================================")
    print(f" Phase 1.6: Ingestion QA Validation")
    print(f" Target Collection: '{collection_name}' | Total Vectors: {total_chunks}")
    print(f"=======================================================\n")

    if total_chunks == 0:
        print("[WARNING] ChromaDB collection is currently empty! Ingest documents first.")
        return {
            "total_queries": len(QA_BENCHMARK_QUERIES),
            "correct_in_top_k": 0,
            "accuracy": 0.0,
            "collection_count": 0,
            "passed": False,
        }

    correct_count = 0
    results_detail: list[dict[str, Any]] = []

    for idx, (query_text, expected_standard) in enumerate(QA_BENCHMARK_QUERIES, start=1):
        query_vec = embed_query(query_text)
        query_res = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved_metadatas = query_res["metadatas"][0] if query_res["metadatas"] else []
        retrieved_distances = query_res["distances"][0] if query_res["distances"] else []

        retrieved_standards: list[str] = []
        for meta in retrieved_metadatas:
            retrieved_standards.append(meta.get("standard_no", "UNKNOWN"))

        matched = expected_standard in retrieved_standards
        if matched:
            correct_count += 1

        print(f"[{idx}/5] Query: {query_text}")
        print(f"     Expected Standard: {expected_standard}")
        print(f"     Status: {'PASS [Found in Top-' + str(top_k) + ']' if matched else 'FAIL [Not in Top-' + str(top_k) + ']'}")
        print("     Top-3 Retrieved:")
        for r_idx, meta in enumerate(retrieved_metadatas, start=1):
            std_no = meta.get("standard_no", "UNKNOWN")
            cl_no = meta.get("clause_no", "N/A")
            pg_no = meta.get("page_no", "?")
            dist = retrieved_distances[r_idx - 1] if r_idx - 1 < len(retrieved_distances) else 0.0
            print(f"       {r_idx}. Standard: {std_no} | Clause: {cl_no} | Page: {pg_no} | Distance: {dist:.4f}")
        print("-" * 55)

        results_detail.append({
            "query": query_text,
            "expected_standard": expected_standard,
            "retrieved_standards": retrieved_standards,
            "matched": matched,
        })

    accuracy = correct_count / len(QA_BENCHMARK_QUERIES) if QA_BENCHMARK_QUERIES else 0.0
    passed = accuracy >= 0.8  # At least 4/5 (80%) required by acceptance criteria

    print(f"\nFinal Result: {correct_count}/{len(QA_BENCHMARK_QUERIES)} queries correct ({accuracy * 100:.1f}%)")
    print(f"QA Acceptance Threshold (>=80%): {'PASSED' if passed else 'FAILED'}\n")

    return {
        "total_queries": len(QA_BENCHMARK_QUERIES),
        "correct_in_top_k": correct_count,
        "accuracy": accuracy,
        "collection_count": total_chunks,
        "passed": passed,
        "details": results_detail,
    }


def main() -> None:
    """CLI entry point for running ingestion and QA validation."""
    parser = argparse.ArgumentParser(description="Standardify Ingestion Pipeline & QA")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run QA validation test queries against ChromaDB",
    )
    parser.add_argument(
        "--seed-registry",
        action="store_true",
        help="Seed SQLite standards metadata registry",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate chunks without persisting embeddings",
    )

    args = parser.parse_args()

    # Default action: seed registry and run validation if flag passed
    seed_registry_with_demo_catalog()

    if args.validate:
        validate_ingestion_qa()
    else:
        print("Standardify ingestion orchestrator ready. Use --validate to run QA benchmark.")


if __name__ == "__main__":
    main()
