"""
Standardify — Core Hybrid Retrieval Engine.

Combines BGE-M3 dense semantic vector search via ChromaDB / LlamaIndex with
lexical BM25 keyword matching over the ingested standards corpus.

Exposes:
  get_chroma_client() -> chromadb.PersistentClient
  get_collection() -> chromadb.Collection
  get_index() -> VectorStoreIndex
  retrieve(question: str, top_k: int = 5, standard_filter: Optional[str] = None) -> list[RetrievedClause]
"""

from __future__ import annotations

from functools import lru_cache
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from rank_bm25 import BM25Okapi

from app.config import settings
from app.core.embeddings import embed_batch, embed_query
from app.models.domain import Clause, RetrievedClause

logger = logging.getLogger(__name__)

COLLECTION_NAME = "bis_clauses"


class LlamaIndexBGEAdapter(BaseEmbedding):
    """
    LlamaIndex BaseEmbedding adapter routing directly to the BGE-M3 singleton.
    Prevents LlamaIndex from attempting to load external OpenAI models.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(model_name=settings.embedding_model_name, **kwargs)

    def _get_query_embedding(self, query: str) -> List[float]:
        return embed_query(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return embed_query(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return embed_batch(texts)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return embed_query(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return embed_query(text)


class RetrievalEngine:
    """
    Singleton hybrid retrieval engine coordinating ChromaDB, LlamaIndex, and BM25.
    """

    _instance: Optional[RetrievalEngine] = None

    def __new__(cls) -> RetrievalEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self.persist_dir = Path(settings.chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing persistent ChromaDB client at '%s'...", self.persist_dir)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Standardify BIS standards clause-level vector embeddings"},
        )

        self._vector_store: Optional[ChromaVectorStore] = None
        self._llama_index: Optional[VectorStoreIndex] = None
        self._embed_adapter = LlamaIndexBGEAdapter()
        self._bm25_corpus: list[dict[str, Any]] = []
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_initialized = False

        self._initialized = True
        logger.info("Retrieval engine ready. Active vector collection: '%s' (%d items).", COLLECTION_NAME, self.collection.count())

    def get_llama_index(self) -> VectorStoreIndex:
        """
        Build or retrieve LlamaIndex VectorStoreIndex wrapper around existing Chroma collection.
        Uses the local BGE adapter and does not re-embed data.
        """
        if self._llama_index is None:
            self._vector_store = ChromaVectorStore(chroma_collection=self.collection)
            self._llama_index = VectorStoreIndex.from_vector_store(
                vector_store=self._vector_store,
                embed_model=self._embed_adapter,
            )
        return self._llama_index

    def _sync_bm25_index(self) -> None:
        """Load collection documents into memory and construct BM25Okapi index."""
        count = self.collection.count()
        if count == 0:
            self._bm25_corpus = []
            self._bm25_index = None
            self._bm25_initialized = True
            return

        # Fetch all documents from Chroma collection
        all_data = self.collection.get(
            include=["documents", "metadatas"],
        )

        corpus: list[dict[str, Any]] = []
        tokenized_corpus: list[list[str]] = []

        ids = all_data.get("ids", [])
        docs = all_data.get("documents", [])
        metas = all_data.get("metadatas", [])

        for idx in range(len(ids)):
            doc_text = docs[idx] if idx < len(docs) else ""
            metadata = metas[idx] if idx < len(metas) else {}
            tokens = [t.lower() for t in re.findall(r'\b\w+\b', doc_text) if len(t) > 1]

            corpus.append({
                "id": ids[idx],
                "text": doc_text,
                "metadata": metadata,
            })
            tokenized_corpus.append(tokens)

        self._bm25_corpus = corpus
        if tokenized_corpus:
            self._bm25_index = BM25Okapi(tokenized_corpus)
        else:
            self._bm25_index = None

        self._bm25_initialized = True
        logger.info("BM25 index synchronized with %d corpus documents.", len(corpus))

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        standard_filter: Optional[str] = None,
    ) -> List[RetrievedClause]:
        """
        Execute hybrid dense semantic and BM25 lexical retrieval.

        Args:
            question: User natural language inquiry.
            top_k: Number of final ranked clauses to return.
            standard_filter: Optional standard number (e.g. 'IS 9001:2025') to restrict search.

        Returns:
            List[RetrievedClause]: Top-K retrieved clauses sorted by combined relevance score.
        """
        if not question or not question.strip():
            return []

        if self.collection.count() == 0:
            return []

        if not self._bm25_initialized:
            self._sync_bm25_index()

        # ── 1. Dense Semantic Search ──────────────────────────────────────────
        candidate_k = max(top_k * 3, 10)
        query_vector = embed_query(question)

        where_filter = {"standard_no": standard_filter} if standard_filter else None

        try:
            dense_results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=min(candidate_k, self.collection.count()),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.warning("Chroma dense query failed: %s", exc)
            dense_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        dense_candidates: dict[str, dict[str, Any]] = {}
        if dense_results["ids"] and dense_results["ids"][0]:
            r_ids = dense_results["ids"][0]
            r_docs = dense_results["documents"][0]
            r_metas = dense_results["metadatas"][0]
            r_dists = dense_results["distances"][0]

            for idx in range(len(r_ids)):
                c_id = r_ids[idx]
                dist = r_dists[idx]
                # Convert cosine / L2 distance to similarity score in [0.0, 1.0]
                dense_sim = max(0.0, 1.0 - (dist / 2.0))

                dense_candidates[c_id] = {
                    "text": r_docs[idx],
                    "metadata": r_metas[idx],
                    "dense_score": dense_sim,
                }

        # ── 2. Lexical BM25 Search ────────────────────────────────────────────
        lexical_candidates: dict[str, float] = {}
        if self._bm25_index is not None and self._bm25_corpus:
            query_tokens = [t.lower() for t in re.findall(r'\b\w+\b', question) if len(t) > 1]
            if query_tokens:
                bm25_scores = self._bm25_index.get_scores(query_tokens)
                max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 and max(bm25_scores) > 0 else 1.0

                for idx, score in enumerate(bm25_scores):
                    if score > 0:
                        item = self._bm25_corpus[idx]
                        std_no = item["metadata"].get("standard_no")
                        if standard_filter and std_no != standard_filter:
                            continue
                        norm_score = min(1.0, score / max_bm25)
                        lexical_candidates[item["id"]] = norm_score

        # ── 3. Merge, Score & Deduplicate ─────────────────────────────────────
        all_ids = set(dense_candidates.keys()) | set(lexical_candidates.keys())
        merged: list[RetrievedClause] = []

        for cid in all_ids:
            dense_info = dense_candidates.get(cid)
            lex_score = lexical_candidates.get(cid, 0.0)

            if dense_info:
                text = dense_info["text"]
                meta = dense_info["metadata"]
                dense_score = dense_info["dense_score"]
            else:
                # Retrieve document metadata from BM25 corpus lookup
                matching = next((item for item in self._bm25_corpus if item["id"] == cid), None)
                if not matching:
                    continue
                text = matching["text"]
                meta = matching["metadata"]
                dense_score = 0.0

            # Enforce hard filter if standard_filter was specified
            std_no = meta.get("standard_no", "UNKNOWN")
            if standard_filter and std_no != standard_filter:
                continue

            # Hybrid score formula: 70% dense + 30% lexical with dual-match reinforcement
            if dense_score > 0 and lex_score > 0:
                combined_score = min(1.0, (0.70 * dense_score) + (0.30 * lex_score) + 0.05)
                method = "hybrid"
            elif dense_score > 0:
                combined_score = dense_score
                method = "dense"
            else:
                combined_score = lex_score * 0.75
                method = "lexical"

            clause_obj = Clause(
                text=text,
                page_no=int(meta.get("page_no", 1)),
                standard_no=std_no,
                clause_no=meta.get("clause_no") if meta.get("clause_no") != "N/A" else None,
                section_title=meta.get("title"),
                document_title=meta.get("title"),
                category=meta.get("category"),
                needs_review=bool(meta.get("needs_review", False)),
            )

            merged.append(
                RetrievedClause(
                    clause=clause_obj,
                    similarity_score=round(combined_score, 4),
                    dense_score=round(dense_score, 4),
                    lexical_score=round(lex_score, 4),
                    retrieval_method=method,
                )
            )

        # Sort descending by combined similarity score
        merged.sort(key=lambda x: x.similarity_score, reverse=True)

        return merged[:top_k]


def get_retrieval_engine() -> RetrievalEngine:
    """Retrieve the singleton RetrievalEngine instance."""
    return RetrievalEngine()


def get_chroma_client() -> chromadb.PersistentClient:
    """Retrieve the persistent ChromaDB client."""
    return get_retrieval_engine().chroma_client


def get_collection() -> chromadb.Collection:
    """Retrieve the bis_clauses ChromaDB collection."""
    return get_retrieval_engine().collection


def get_index() -> VectorStoreIndex:
    """Retrieve the LlamaIndex VectorStoreIndex."""
    return get_retrieval_engine().get_llama_index()


def retrieve(
    question: str,
    top_k: int = 5,
    standard_filter: Optional[str] = None,
) -> List[RetrievedClause]:
    """
    Execute hybrid dense + BM25 retrieval for a question.

    Args:
        question: User query string.
        top_k: Number of ranked clauses to return (default: 5).
        standard_filter: Optional standard number restriction.

    Returns:
        List[RetrievedClause]: Ranked retrieved clauses.
    """
    return get_retrieval_engine().retrieve(
        question=question,
        top_k=top_k,
        standard_filter=standard_filter,
    )
