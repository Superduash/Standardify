"""
Standardify — Application Configuration Module.

Loads and validates environment configuration using pydantic-settings.
All environment variables are loaded from the project's .env file or the
runtime environment. No hardcoded keys, secrets, or environment-specific
paths exist in the codebase.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings schema for the Standardify backend.

    Attributes:
        groq_api_key: API key for Groq LLM inference (primary provider). Required.
        gemini_api_key: API key for Google Gemini LLM inference (fallback). Required.
        embedding_model_name: HuggingFace model identifier for dense embeddings.
        chroma_persist_dir: Local filesystem directory for persistent ChromaDB storage.
        llm_primary_provider: Identifier of the primary LLM provider ('groq' or 'gemini').
        log_level: Logging verbosity level (e.g., 'INFO', 'DEBUG', 'WARNING').
        cache_ttl_seconds: Diskcache TTL duration in seconds.
        confidence_floor: Minimum confidence threshold below which evidence is deemed absent.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required API Keys — must be provided via .env or runtime environment
    groq_api_key: str = Field(
        ...,
        description="API key for Groq LLM inference (primary provider)",
    )
    gemini_api_key: str = Field(
        ...,
        description="API key for Google Gemini LLM inference (fallback provider)",
    )

    # Embedding and Vector Database Configuration
    embedding_model_name: str = Field(
        default="BAAI/bge-m3",
        description="HuggingFace model name for dense vector embeddings",
    )
    chroma_persist_dir: str = Field(
        default="./data/chroma_store",
        description="Directory path for persistent ChromaDB storage",
    )

    # LLM Provider Configuration
    llm_primary_provider: Literal["groq", "gemini"] = Field(
        default="groq",
        description="Primary LLM provider to use ('groq' or 'gemini')",
    )

    # Operational & Retrieval Tuning Parameters
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    cache_ttl_seconds: int = Field(
        default=86400,
        description="Cache time-to-live in seconds (default: 86400 / 24h)",
    )
    confidence_floor: float = Field(
        default=0.35,
        description="Minimum confidence score threshold for evidence validity",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retrieve or create the cached singleton Settings instance.

    Returns:
        Settings: Validated application configuration settings instance.
    """
    return Settings()


# Expose a single settings instance for direct import across modules
settings: Settings = get_settings()
