"""
Standardify — Structured logging configuration.

Configures Python's standard logging subsystem with structured formatting
and honours the configured LOG_LEVEL. Called during application startup.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure global structured logging for the application.

    Args:
        log_level: Desired log verbosity level (e.g. 'DEBUG', 'INFO', 'WARNING').
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    # Set third-party loggers to reasonable levels
    logging.getLogger("uvicorn.access").setLevel(numeric_level)
    logging.getLogger("uvicorn.error").setLevel(numeric_level)
