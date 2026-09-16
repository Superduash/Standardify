"""
Standardify — BGE-M3 embedding singleton wrapper.

Loads BAAI/bge-m3 (or the configured embedding model) exactly ONCE at process startup.
Reuses the loaded model instance across all subsequent inference requests.
Uses FP16 when a CUDA GPU is available, falling back gracefully to CPU FP32.

Exposes:
  get_embedding_engine() -> EmbeddingEngine
  embed_query(text: str) -> list[float]
  embed_batch(texts: Sequence[str]) -> list[list[float]]

All embedding operations in the codebase flow through this module (Golden Rule #3).
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Sequence

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Singleton wrapper for local dense vector embedding generation.

    Attributes:
        model_name: HuggingFace repository identifier of the embedding model.
        device: Active compute device ('cuda' or 'cpu').
        use_fp16: True if FP16 mixed precision is enabled on GPU.
    """

    _instance: Optional[EmbeddingEngine] = None
    _model: Any = None

    def __new__(cls, *args: Any, **kwargs: Any) -> EmbeddingEngine:
        """Enforce singleton instance creation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: Optional[str] = None) -> None:
        """
        Initialize the embedding engine and load the neural model once.

        Args:
            model_name: Optional override for the model identifier.
        """
        if self._model is not None:
            return

        self.model_name: str = model_name or settings.embedding_model_name
        self.device: str = "cpu"
        self.use_fp16: bool = False

        self._load_model()

    def _load_model(self) -> None:
        """Load the embedding model into memory with appropriate device/precision."""
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                self.use_fp16 = True
            else:
                self.device = "cpu"
                self.use_fp16 = False
        except ImportError:
            self.device = "cpu"
            self.use_fp16 = False

        logger.info(
            "Loading embedding model '%s' on device '%s' (fp16=%s)...",
            self.model_name,
            self.device,
            self.use_fp16,
        )

        # Attempt to load via FlagEmbedding first, fallback to sentence-transformers
        try:
            from FlagEmbedding import BGEM3FlagModel
            self._model = BGEM3FlagModel(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device,
            )
            self._backend = "flag_embedding"
            logger.info("Successfully loaded model '%s' via FlagEmbedding.", self.model_name)
            return
        except Exception as exc:
            logger.debug("FlagEmbedding not available or failed (%s); trying sentence-transformers.", exc)

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )
            self._backend = "sentence_transformers"
            logger.info("Successfully loaded model '%s' via sentence-transformers.", self.model_name)
            return
        except Exception as exc:
            logger.error("Failed to load embedding model '%s': %s", self.model_name, exc)
            raise RuntimeError(f"Could not load embedding model '{self.model_name}': {exc}") from exc

    def embed_query(self, text: str) -> List[float]:
        """
        Compute dense vector embedding for a single text query.

        Args:
            text: Query string to embed.

        Returns:
            List[float]: Normalized dense embedding vector.
        """
        if not text or not text.strip():
            # Return zero vector fallback or embed placeholder
            text = " "

        results = self.embed_batch([text])
        return results[0]

    def embed_batch(self, texts: Sequence[str], batch_size: int = 32) -> List[List[float]]:
        """
        Compute dense vector embeddings for a sequence of text strings.

        Args:
            texts: Sequence of text strings to embed.
            batch_size: Processing batch size for batch encoding.

        Returns:
            List[List[float]]: List of normalized dense embedding vectors.
        """
        if not texts:
            return []

        cleaned_texts = [t if (t and t.strip()) else " " for t in texts]

        if getattr(self, "_backend", None) == "flag_embedding":
            output = self._model.encode(
                cleaned_texts,
                batch_size=batch_size,
                max_length=8192,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            dense_vecs = output["dense_vecs"]
            if hasattr(dense_vecs, "tolist"):
                return dense_vecs.tolist()
            return [list(map(float, vec)) for vec in dense_vecs]

        # sentence-transformers backend
        embeddings = self._model.encode(
            cleaned_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


def get_embedding_engine() -> EmbeddingEngine:
    """
    Retrieve the singleton EmbeddingEngine instance.

    Returns:
        EmbeddingEngine: Active singleton instance.
    """
    return EmbeddingEngine()


def embed_query(text: str) -> List[float]:
    """
    Compute dense vector embedding for a query using the singleton engine.

    Args:
        text: Query text string.

    Returns:
        List[float]: Dense vector representation.
    """
    return get_embedding_engine().embed_query(text)


def embed_batch(texts: Sequence[str]) -> List[List[float]]:
    """
    Compute dense vector embeddings for a batch of strings using the singleton engine.

    Args:
        texts: Sequence of strings.

    Returns:
        List[List[float]]: List of dense vector representations.
    """
    return get_embedding_engine().embed_batch(texts)
