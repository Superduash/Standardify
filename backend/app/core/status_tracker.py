"""
Standardify — Amendment & Withdrawal Status Tracker (Phase 7.1).

Queries data/registry.db for official BIS standard lifecycle statuses
(Active, Superseded, Withdrawn, Under Revision) and generates actionable warnings.

Exposes:
  get_status(standard_no: str) -> Optional[StatusInfo]
  get_status_warning(standard_no: str) -> Optional[str]
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
from typing import Optional

from app.models.domain import StatusInfo

logger = logging.getLogger(__name__)

DB_PATH = Path("./data/registry.db")


def _get_connection() -> sqlite3.Connection:
    """Create a read-only SQLite database connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Registry database not found at {DB_PATH}")
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def get_status(standard_no: str) -> Optional[StatusInfo]:
    """
    Retrieve lifecycle and amendment status for an Indian Standard.

    Args:
        standard_no: Identifier (e.g. 'IS 374:2019', 'IS 1293:2005').

    Returns:
        Optional[StatusInfo]: Populated StatusInfo if found, or None if unknown.
    """
    clean_std = standard_no.strip()
    if not clean_std or not DB_PATH.exists():
        return None

    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT standard_no, status, superseded_by, last_amended_date
                FROM standards
                WHERE standard_no = ?
                COLLATE NOCASE
                """,
                (clean_std,),
            )
            row = cursor.fetchone()
            if row:
                return StatusInfo(
                    standard_no=row[0],
                    status=row[1] or "Active",
                    superseded_by=row[2],
                    last_amended_date=row[3],
                )
            return None
    except Exception as exc:
        logger.error("Error querying status for standard '%s': %s", clean_std, exc)
        return None


def get_status_warning(standard_no: str) -> Optional[str]:
    """
    Generate an advisory warning string if a standard is superseded, withdrawn, or amended.

    Returns:
        Optional[str]: Warning text if standard has non-active status, else None.
    """
    info = get_status(standard_no)
    if not info:
        return None

    status_lower = info.status.lower()
    if status_lower == "superseded":
        successor = info.superseded_by or "a newer edition"
        return f"{info.standard_no} has been superseded by {successor} — verify before relying on this clause."
    elif status_lower == "withdrawn":
        return f"{info.standard_no} has been withdrawn by BIS — this clause may no longer be legally enforceable."
    elif status_lower == "under revision":
        return f"{info.standard_no} is currently under active revision by the BIS technical committee."

    return None
