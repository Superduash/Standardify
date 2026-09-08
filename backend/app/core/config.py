"""
Standardify — Pydantic Settings
Reads from .env file (or environment variables). Every setting has a sane default
so the app runs with ZERO configuration.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM keys — both optional
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # Model names
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash"

    # Embedding
    embedding_model: str = "BAAI/bge-m3"
    chroma_collection: str = "standards_v1"

    # Paths — resolve relative to the backend/ directory where uvicorn is launched
    chroma_path: str = "./data/chroma"
    standards_raw_path: str = "./data/standards_raw"
    graph_json_path: str = "./data/graph_relationships.json"

    # Server
    cors_origins: str = "*"
    port: int = 8000

    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.25

    def get_cors_origins(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def resolved_chroma_path(self) -> Path:
        return Path(self.chroma_path).resolve()

    def resolved_standards_raw_path(self) -> Path:
        return Path(self.standards_raw_path).resolve()

    def resolved_graph_json_path(self) -> Path:
        return Path(self.graph_json_path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
