"""
Standardify — API v1 Router Aggregator.

Imports and registers all endpoint sub-routers under the /api/v1 prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.ask import router as ask_router
from app.api.v1.gap_check import router as gap_check_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router

router = APIRouter()

# Register sub-routers
router.include_router(health_router)
router.include_router(ask_router)
router.include_router(gap_check_router)
router.include_router(graph_router)


