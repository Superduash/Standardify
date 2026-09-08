"""
Standardify — BGE-M3 Embedding Service (singleton).

Loads the model once on first use and reuses it. Works fully offline after
the first download (~1.1 GB cached in HuggingFace's default cache dir).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Union

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Wraps SentenceTransformer BGE-M3 with a simple encode() interface."""

    def __init__(self, model_name: str) -> None:
        logger.info("Loading embedding model '%s' — first run may take a while...", model_name)
        self._model = SentenceTransformer(model_name, trust_remote_code=True)
        self._dim = self._model.get_sentence_embedding_dimension()
        logger.info("Embedding model loaded. Dimension: %d", self._dim)

    @property
    def dimension(self) -> int:
        return self._dim

    def encode(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """Encode one or more strings into dense embedding vectors."""
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=16,
        )
        return embeddings.tolist()

    def encode_single(self, text: str) -> list[float]:
        """Convenience: encode a single string and return a 1-D list."""
        return self.encode([text])[0]


@lru_cache(maxsize=1)
def get_embeddings_service() -> EmbeddingsService:
    settings = get_settings()
    return EmbeddingsService(settings.embedding_model)
