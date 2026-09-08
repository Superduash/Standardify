"""
Standardify — ChromaDB vector store wrapper.

Provides a clean interface for upserting documents and querying top-k results
with their metadata. Uses a local persistent Chroma client.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Wraps a ChromaDB persistent client and a single named collection."""

    def __init__(self, persist_directory: str, collection_name: str) -> None:
        path = Path(persist_directory)
        path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB ready — collection '%s' at '%s' (%d docs)",
            collection_name,
            path,
            self._collection.count(),
        )

    @property
    def document_count(self) -> int:
        return self._collection.count()

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or update documents in the collection."""
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """
        Query the collection for the top_k most similar chunks.

        Returns a list of dicts, each containing:
          - id: str
          - document: str  (the chunk text)
          - metadata: dict  (standard_no, title, clause_no, page, …)
          - distance: float  (cosine distance — lower = more similar)
          - score: float  (1 - distance, so higher = more similar)
        """
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, max(self._collection.count(), 1)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        output: list[dict[str, Any]] = []
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for doc_id, doc, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
            output.append(
                {
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta or {},
                    "distance": dist,
                    "score": float(1.0 - dist),
                }
            )

        return output

    def keyword_search(self, keyword: str, top_k: int = 10) -> list[dict[str, Any]]:
        """
        Naive keyword search: use ChromaDB's `where_document` contains filter.
        Falls back gracefully if nothing found.
        """
        try:
            count = self._collection.count()
            if count == 0:
                return []
            results = self._collection.query(
                query_texts=[keyword],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            output: list[dict[str, Any]] = []
            ids_list = results.get("ids", [[]])[0]
            docs_list = results.get("documents", [[]])[0]
            metas_list = results.get("metadatas", [[]])[0]
            dists_list = results.get("distances", [[]])[0]
            for doc_id, doc, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
                output.append(
                    {
                        "id": doc_id,
                        "document": doc,
                        "metadata": meta or {},
                        "distance": dist,
                        "score": float(1.0 - dist),
                    }
                )
            return output
        except Exception as exc:
            logger.warning("keyword_search failed: %s", exc)
            return []


# Module-level singleton — initialized lazily via get_vector_store()
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        _vector_store = VectorStore(
            persist_directory=str(settings.resolved_chroma_path()),
            collection_name=settings.chroma_collection,
        )
    return _vector_store
