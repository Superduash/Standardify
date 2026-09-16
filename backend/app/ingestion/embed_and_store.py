"""
Standardify — Batch embedding + ChromaDB upsert.

Reads tagged Clause objects produced by the ingestion pipeline, embeds them
in batches using app/core/embeddings.py (BGE-M3 singleton), and upserts into
the persistent ChromaDB collection "bis_clauses".

ID scheme: f"{standard_no}::{clause_no}::{page_no}"  (stable, idempotent)
Metadata stored per vector: standard_no, clause_no, page_no, title, category, needs_review.

Re-running this script NEVER duplicates vectors — ChromaDB upsert ensures
idempotency (Golden Rule #6).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.core.embeddings import embed_batch
from app.models.domain import Clause

logger = logging.getLogger(__name__)

COLLECTION_NAME = "bis_clauses"


def get_chroma_client(persist_dir: Optional[str] = None) -> chromadb.PersistentClient:
    """
    Initialize and return a persistent ChromaDB client.

    Args:
        persist_dir: Optional override for the persistence directory.

    Returns:
        chromadb.PersistentClient: Configured Chroma client.
    """
    storage_path = persist_dir or settings.chroma_persist_dir
    Path(storage_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(storage_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_or_create_collection(
    client: Optional[chromadb.PersistentClient] = None,
    collection_name: str = COLLECTION_NAME,
) -> chromadb.Collection:
    """
    Retrieve or initialize the target ChromaDB vector collection.

    Args:
        client: Optional active Chroma client instance.
        collection_name: Name of the vector collection (default: 'bis_clauses').

    Returns:
        chromadb.Collection: Chroma vector collection.
    """
    chroma_client = client or get_chroma_client()
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Standardify BIS standards clause-level vector embeddings"},
    )


def generate_clause_id(clause: Clause, index_in_batch: int = 0) -> str:
    """
    Generate a deterministic, stable ID for a clause chunk.

    Format: "{standard_no}::{clause_no}::{page_no}" (with suffix if clause_no is None).

    Args:
        clause: Clause chunk instance.
        index_in_batch: Index offset to resolve potential duplicates within the same page.

    Returns:
        str: Stable unique identifier.
    """
    std = clause.standard_no or "UNKNOWN"
    cl = clause.clause_no or f"unindexed_{index_in_batch}"
    pg = clause.page_no
    return f"{std}::{cl}::{pg}"


def embed_and_upsert_clauses(
    clauses: Sequence[Clause],
    batch_size: int = 32,
    persist_dir: Optional[str] = None,
    collection_name: str = COLLECTION_NAME,
) -> int:
    """
    Batch-embed clause chunks and upsert them into ChromaDB.

    Args:
        clauses: Sequence of metadata-tagged Clause objects.
        batch_size: Processing batch size for embedding and DB writes.
        persist_dir: Optional override for Chroma storage path.
        collection_name: Target collection name.

    Returns:
        int: Number of clauses successfully upserted.
    """
    if not clauses:
        logger.info("No clauses provided for embedding and upsert.")
        return 0

    client = get_chroma_client(persist_dir=persist_dir)
    collection = get_or_create_collection(client=client, collection_name=collection_name)

    total_clauses = len(clauses)
    logger.info("Starting embedding and upsert for %d clauses in batches of %d...", total_clauses, batch_size)

    seen_ids: dict[str, int] = {}
    upserted_count = 0

    for i in range(0, total_clauses, batch_size):
        batch = clauses[i : i + batch_size]
        texts_to_embed = [c.text for c in batch]

        # 1. Compute dense embeddings via singleton wrapper
        embeddings = embed_batch(texts_to_embed)

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for idx, clause in enumerate(batch):
            base_id = generate_clause_id(clause, index_in_batch=i + idx)
            # Ensure unique IDs if multiple sub-chunks have identical standard/clause/page
            if base_id in seen_ids:
                seen_ids[base_id] += 1
                unique_id = f"{base_id}_sub{seen_ids[base_id]}"
            else:
                seen_ids[base_id] = 0
                unique_id = base_id

            title_val = clause.section_title or clause.document_title or ""

            metadata_dict: dict[str, Any] = {
                "standard_no": str(clause.standard_no or "UNKNOWN"),
                "clause_no": str(clause.clause_no or "N/A"),
                "page_no": int(clause.page_no),
                "title": str(title_val),
                "category": str(clause.category or "General"),
                "needs_review": bool(clause.needs_review),
            }

            ids.append(unique_id)
            documents.append(clause.text)
            metadatas.append(metadata_dict)

        # 2. Upsert into ChromaDB (idempotent, replaces existing vectors with same ID)
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        upserted_count += len(batch)
        logger.debug("Upserted batch %d/%d (%d total)", i + len(batch), total_clauses, upserted_count)

    logger.info("Successfully completed ChromaDB upsert: %d clauses stored.", upserted_count)
    return upserted_count
