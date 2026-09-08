"""
Standardify — FastAPI application entry point.

Loads ChromaDB index and knowledge graph at startup via lifespan context manager.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import routes_health, routes_query, routes_gap_check, routes_graph, routes_search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load heavy singletons at startup so first requests aren't slow."""
    logger.info("Standardify backend starting up…")
    settings = get_settings()

    # Pre-load vector store (connect to Chroma)
    from app.services.vector_store import get_vector_store
    vs = get_vector_store()
    logger.info("Vector store ready: %d documents indexed", vs.document_count)

    # Pre-load graph
    from app.services.graph_service import get_graph_service
    gs = get_graph_service()
    graph_data = gs.to_json()
    logger.info("Knowledge graph ready: %d nodes, %d edges",
                len(graph_data["nodes"]), len(graph_data["links"]))

    # Pre-load embedding model (this takes a while on first run)
    from app.services.embeddings_service import get_embeddings_service
    emb = get_embeddings_service()
    logger.info("Embedding model ready (dim=%d)", emb.dimension)

    logger.info("Standardify backend ready ✓")
    yield
    logger.info("Standardify backend shutting down…")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Standardify API",
        description="AI Assistant for Indian Bureau of Standards (BIS) — SIH 2026",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — configured via CORS_ORIGINS env var (default: all origins for dev)
    origins = settings.get_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes under /api prefix
    prefix = "/api"
    app.include_router(routes_health.router, prefix=prefix, tags=["Health"])
    app.include_router(routes_query.router, prefix=prefix, tags=["Query"])
    app.include_router(routes_gap_check.router, prefix=prefix, tags=["Gap Check"])
    app.include_router(routes_graph.router, prefix=prefix, tags=["Graph"])
    app.include_router(routes_search.router, prefix=prefix, tags=["Search"])

    @app.get("/")
    def root():
        return {"message": "Standardify API is running. Visit /docs for the interactive API."}

    return app


app = create_app()
