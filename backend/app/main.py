"""
Standardify — FastAPI Application Entry Point (Phase 9 Hardened).

Wires:
  - Centralized structured exception handlers (LLMUnavailableError, ValidationError, HTTPException, 500)
  - Correlation Request ID middleware (X-Request-ID)
  - In-memory per-IP rate limiting middleware for expensive endpoints (/ask, /gap-check)
  - Configurable CORS middleware
  - OpenAPI v1 router mounting
"""

from __future__ import annotations

from collections import defaultdict
from contextlib import asynccontextmanager
import logging
import time
from typing import AsyncGenerator, Dict, List
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_v1_router
from app.config import settings
from app.logging_conf import setup_logging
from app.models.domain import LLMUnavailableError

logger = logging.getLogger(__name__)

# Sliding window rate limiter state: client_ip -> list of timestamps
_RATE_LIMIT_STORE: Dict[str, List[float]] = defaultdict(list)
RATE_LIMITED_PATHS = {"/api/v1/ask", "/api/v1/gap-check"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle (startup and shutdown events).
    """
    setup_logging(log_level=settings.log_level)
    logger.info("Standardify API initialized successfully. Environment ready.")
    yield
    logger.info("Standardify API shutting down.")


def create_app() -> FastAPI:
    """
    Construct and configure the production-hardened FastAPI application instance.
    """
    app = FastAPI(
        title="Standardify API",
        description=(
            "AI-Powered Intelligent Assistant for Indian Standards (BIS) & Regulatory Services. "
            "Supports Grounded Q&A, Compliance Gap Checking, Standards Relationship Graph, "
            "Lifecycle Status Tracking, and Full-Text Search."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Request Correlation ID & Rate Limiter Middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        # Generate or capture correlation request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id

        path = request.url.path.rstrip("/")
        # Rate limit check for expensive POST endpoints
        if request.method.upper() == "POST" and path in RATE_LIMITED_PATHS:
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window = settings.rate_limit_window_seconds
            max_reqs = settings.rate_limit_requests

            # Purge timestamps older than window
            timestamps = [t for t in _RATE_LIMIT_STORE[client_ip] if now - t < window]
            if len(timestamps) >= max_reqs:
                logger.warning("Rate limit exceeded for IP %s on %s (ReqID: %s)", client_ip, path, req_id)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "detail": f"Rate limit exceeded ({max_reqs} requests per {window}s). Please try again later.",
                        "request_id": req_id,
                    },
                    headers={"X-Request-ID": req_id, "Retry-After": str(window)},
                )

            timestamps.append(now)
            _RATE_LIMIT_STORE[client_ip] = timestamps

        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # 3. Global Exception Handlers

    @app.exception_handler(LLMUnavailableError)
    async def llm_unavailable_exception_handler(request: Request, exc: LLMUnavailableError):
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error("LLM Provider Unavailable on %s (ReqID: %s): %s", request.url.path, req_id, exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "llm_unavailable",
                "detail": "The AI inference service is temporarily unavailable. Please try again shortly.",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.info("Validation error on %s (ReqID: %s): %s", request.url.path, req_id, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "detail": exc.errors(),
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "detail": exc.detail,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.error("Unhandled internal exception on %s (ReqID: %s): %s", request.url.path, req_id, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "detail": "An internal error occurred. Please contact support with the request ID.",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    # Mount API v1 router
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app: FastAPI = create_app()
