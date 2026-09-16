"""
Standardify — FastAPI application entry point.

Mounts all API v1 routers and wires startup/shutdown lifespan events.
Structured logging and CORS middleware are configured here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.logging_conf import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle (startup and shutdown events).

    Initializes structured logging and prepares application runtime.
    """
    setup_logging(log_level=settings.log_level)
    yield


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Returns:
        FastAPI: The configured application instance.
    """
    app = FastAPI(
        title="Standardify API",
        description="AI Assistant for Indian Standards (BIS) — SIH 2026",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS middleware (open for development, restricted in Phase 8.2)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API v1 router
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app: FastAPI = create_app()
