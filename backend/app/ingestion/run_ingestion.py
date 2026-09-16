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

from app.ingestion.metadata_extractor import DEMO_CATALOG, extract_standard_meta, tag_chunk
from app.models.domain import Clause, StandardMeta

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY_PATH = Path("./data/registry.db")

# Curated demo clause corpus for offline demo seeding & testing
CURATED_DEMO_CLAUSES: list[Clause] = [
    Clause(
        text="4.1 Material Requirements\nPlastic containers for packaged drinking water shall be made from virgin food grade polymers compliant with IS 9001:2025. Recycled plastics are strictly prohibited.",
        page_no=2,
        standard_no="IS 9001:2025",
        clause_no="4.1",
        section_title="Material Requirements",
        document_title="Plastic Containers for Packaged Drinking Water — Specification",
        category="Plastics & Packaging",
        needs_review=False,
    ),
    Clause(
        text="5.2 Drop Impact and Pressure Test\nThe filled bottle container shall withstand a free fall drop test from 1.2 m height onto a flat concrete surface without rupture or leakage. Hydrostatic pressure of 200 kPa must be maintained for 5 minutes.",
        page_no=4,
        standard_no="IS 9001:2025",
        clause_no="5.2",
        section_title="Drop Impact and Pressure Test",
        document_title="Plastic Containers for Packaged Drinking Water — Specification",
        category="Plastics & Packaging",
        needs_review=False,
    ),
    Clause(
        text="3.2 Mandatory Nutritional Labelling\nAll pre-packaged food items must display energy value, proteins, carbohydrates, total sugars, added sugars, fats, and sodium per 100g or per single serving on the principal display panel.",
        page_no=3,
        standard_no="IS 9004:2025",
        clause_no="3.2",
        section_title="Mandatory Nutritional Labelling",
        document_title="Packaged Food Products — Nutritional and Safety Labelling",
        category="Food & Agriculture",
        needs_review=False,
    ),
    Clause(
        text="4.5 Allergen Declarations and Date Marking\nPresence of gluten, nuts, dairy, soy, or shellfish allergens shall be clearly highlighted in bold type. Expiry date or Use By date must be prominently stamped.",
        page_no=5,
        standard_no="IS 9004:2025",
        clause_no="4.5",
        section_title="Allergen Declarations and Date Marking",
        document_title="Packaged Food Products — Nutritional and Safety Labelling",
        category="Food & Agriculture",
        needs_review=False,
    ),
    Clause(
        text="4.1 Physical and Mechanical Hazards\nToys intended for children under 36 months must not contain small parts that fit into the small parts cylinder (31.7 mm diameter) to eliminate choking hazards.",
        page_no=2,
        standard_no="IS 9002:2025",
        clause_no="4.1",
        section_title="Physical and Mechanical Hazards",
        document_title="Safety of Toys — Mechanical and Physical Properties",
        category="Consumer Products",
        needs_review=False,
    ),
    Clause(
        text="5.3 Sharp Edges and Points Test\nAccessible metal and glass edges on children toys shall be smooth or protected to prevent laceration injuries during normal play.",
        page_no=4,
        standard_no="IS 9002:2025",
        clause_no="5.3",
        section_title="Sharp Edges and Points Test",
        document_title="Safety of Toys — Mechanical and Physical Properties",
        category="Consumer Products",
        needs_review=False,
    ),
    Clause(
        text="6.1 Impact Absorption Test for Helmets\nProtective helmets for two-wheeler motorcycle riders shall be dropped onto flat and hemispherical steel anvils at 7.5 m/s. The peak acceleration transmitted to the headform shall not exceed 300g.",
        page_no=6,
        standard_no="IS 9003:2026",
        clause_no="6.1",
        section_title="Impact Absorption Test for Helmets",
        document_title="Protective Helmets for Two-Wheeler Riders — Specification",
        category="Automotive & Safety",
        needs_review=False,
    ),
    Clause(
        text="7.2 Retention System and Chin Strap\nThe chin strap retention mechanism shall not slip more than 25 mm under a dynamic 50 kg load test.",
        page_no=8,
        standard_no="IS 9003:2026",
        clause_no="7.2",
        section_title="Retention System and Chin Strap",
        document_title="Protective Helmets for Two-Wheeler Riders — Specification",
        category="Automotive & Safety",
        needs_review=False,
    ),
    Clause(
        text="5.1 Air Delivery and Speed Regulation\nElectric ceiling fans of 1200 mm sweep shall deliver a minimum air flow of 210 m3/min at rated voltage with an energy service value exceeding 4.0 m3/min/Watt.",
        page_no=3,
        standard_no="IS 374:2019",
        clause_no="5.1",
        section_title="Air Delivery and Speed Regulation",
        document_title="Electric Ceiling Fans — Specification",
        category="Electrical & Electronics",
        needs_review=False,
    ),
    Clause(
        text="7.4 Thermal Protection and Suspension Safety\nFan motor windings must incorporate thermal overload protection. Suspension downrod and safety shackle must withstand a 1000 N tensile pull test.",
        page_no=7,
        standard_no="IS 374:2019",
        clause_no="7.4",
        section_title="Thermal Protection and Suspension Safety",
        document_title="Electric Ceiling Fans — Specification",
        category="Electrical & Electronics",
        needs_review=False,
    ),
    Clause(
        text="4.2 Safety Valves and Bursting Pressure\nDomestic pressure cookers must be fitted with an operating pressure regulator, safety relief valve, and fusible safety plug that releases pressure safely before reaching 300 kPa.",
        page_no=3,
        standard_no="IS 9005:2025",
        clause_no="4.2",
        section_title="Safety Valves and Bursting Pressure",
        document_title="Domestic Pressure Cookers — Safety and Performance",
        category="Mechanical & Consumer Goods",
        needs_review=False,
    ),
    Clause(
        text="6.2 Photobiological and Blue Light Hazard\nDomestic LED lighting luminaires shall comply with Risk Group RG0 (Exempt) or RG1 (Low Risk) according to photobiological safety standards.",
        page_no=5,
        standard_no="IS 9999:2026",
        clause_no="6.2",
        section_title="Photobiological and Blue Light Hazard",
        document_title="LED Lighting Systems for Domestic Use — Safety and Photobiological Specifications",
        category="Electrical & Electronics",
        needs_review=False,
    ),
]

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
    for std_no, entry in DEMO_CATALOG.items():
        title = entry[0]
        category = entry[1]
        status = entry[2]
        superseded_by = entry[3] if len(entry) > 3 else None
        last_amended_date = entry[4] if len(entry) > 4 else None
        meta = StandardMeta(
            standard_no=std_no,
            title=title,
            category=category,
            status=status,
            superseded_by=superseded_by,
            last_amended_date=last_amended_date,
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


def ingest_demo_dataset(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> int:
    """
    Seed the SQLite registry and upsert curated demo clauses into ChromaDB.

    Args:
        db_path: Filesystem path to SQLite registry database.

    Returns:
        int: Total number of clauses upserted to vector store.
    """
    from app.ingestion.embed_and_store import embed_and_upsert_clauses

    # 1. Populate SQLite standards registry
    seed_registry_with_demo_catalog(db_path=db_path)

    # 2. Embed and upsert curated demo clauses
    upserted = embed_and_upsert_clauses(CURATED_DEMO_CLAUSES)
    return upserted


def ingest_pdf_directory(pdf_dir: Path | str, db_path: Path | str = DEFAULT_REGISTRY_PATH) -> int:
    """
    Process all PDFs in a directory: extract, chunk, tag metadata, and store in SQLite + ChromaDB.

    Args:
        pdf_dir: Directory containing PDF files.
        db_path: Path to SQLite registry database.

    Returns:
        int: Total number of clauses indexed.
    """
    from app.ingestion.clause_chunker import chunk_document
    from app.ingestion.embed_and_store import embed_and_upsert_clauses
    from app.ingestion.pdf_extract import extract_document

    path = Path(pdf_dir)
    pdf_files = list(path.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", pdf_dir)
        return 0

    all_tagged_clauses: list[Clause] = []

    for pdf_file in pdf_files:
        logger.info("Processing PDF: %s", pdf_file.name)
        pages = extract_document(pdf_file)
        raw_clauses = chunk_document(pages)

        # Extract document metadata
        first_page_text = pages[0].raw_text if pages else ""
        meta = extract_standard_meta(first_page_text, fallback_standard_no=pdf_file.stem)
        upsert_standard(meta, db_path=db_path)

        # Tag each chunk with document metadata
        for chunk in raw_clauses:
            tagged = tag_chunk(chunk, document_meta=meta)
            all_tagged_clauses.append(tagged)

    if all_tagged_clauses:
        return embed_and_upsert_clauses(all_tagged_clauses)
    return 0


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


def validate_ingestion(db_path: Path | str = DEFAULT_REGISTRY_PATH) -> bool:
    """
    Validation helper returning boolean status for automated pipelines.

    Args:
        db_path: Filesystem path to SQLite registry.

    Returns:
        bool: True if validation passed.
    """
    res = validate_ingestion_qa()
    return bool(res.get("passed", False))


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
