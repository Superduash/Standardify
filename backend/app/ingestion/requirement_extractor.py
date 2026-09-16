"""
Standardify — ONE-TIME Offline LLM-Assisted Requirement Checklist Extractor (Phase 5.1).

For each demo standard, makes EXACTLY ONE LLM call asking it to extract a structured
list of discrete, checkable requirements from that standard's clauses. Results are cached
permanently to data/requirements_cache.json keyed by standard_no.

This script runs ONLY during ingestion (never at request time). It is idempotent:
safe to re-run and skips any standard_no already present in the cache file.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Dict, List, Optional

from app.core.llm_client import generate_answer
from app.models.domain import Clause

logger = logging.getLogger(__name__)

CACHE_FILE_PATH = Path("./data/requirements_cache.json")
CACHE_VERSION = "1.0"


def load_requirements_cache() -> Dict[str, Any]:
    """
    Load requirements cache from data/requirements_cache.json.
    Returns dictionary with '_version' and 'standards' mapping.
    """
    if not CACHE_FILE_PATH.exists():
        return {"_version": CACHE_VERSION, "standards": {}}

    try:
        with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "standards" not in data:
                return {"_version": CACHE_VERSION, "standards": {}}
            return data
    except Exception as exc:
        logger.warning("Failed to parse requirements cache file, initializing fresh: %s", exc)
        return {"_version": CACHE_VERSION, "standards": {}}


def save_requirements_cache(cache_data: Dict[str, Any]) -> None:
    """
    Atomically save requirements cache to data/requirements_cache.json.
    """
    CACHE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write via temporary file
    temp_dir = CACHE_FILE_PATH.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
        json.dump(cache_data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name

    try:
        os.replace(temp_name, CACHE_FILE_PATH)
        logger.info("Successfully updated requirements cache at %s", CACHE_FILE_PATH)
    except Exception as exc:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise IOError(f"Failed to atomically write requirements cache: {exc}") from exc


def build_requirement_extraction_prompt(standard_no: str, clauses: List[Clause]) -> str:
    """
    Build a concise prompt instructing the LLM to extract discrete, checkable requirements.
    """
    clause_blocks = []
    for c in clauses:
        clause_id = c.clause_no or "General"
        title = c.section_title or c.document_title or "Requirements"
        clause_blocks.append(f"--- [Clause {clause_id} - {title}] ---\n{c.text.strip()}")

    joined_clauses = "\n\n".join(clause_blocks)

    return (
        f"You are a BIS Standards Compliance Analyst. Extract a list of discrete, testable technical requirements "
        f"from the following clauses of Indian Standard '{standard_no}'.\n\n"
        f"Rules:\n"
        f"1. Extract ONLY concrete, testable compliance requirements (specifications, dimensions, limits, tests, warnings, prohibitions).\n"
        f"2. Ignore general commentary, historical context, or introductory text.\n"
        f"3. Format each requirement as a JSON array of objects with the exact keys: 'clause_no', 'section_title', 'text'.\n"
        f"4. Do NOT invent requirements not supported by the clauses.\n\n"
        f"CLAUSES:\n{joined_clauses}\n\n"
        f"Return ONLY valid JSON in format:\n"
        f"[\n"
        f'  {{"clause_no": "4.1", "section_title": "Material Requirements", "text": "Requirement statement..."}}\n'
        f"]"
    )


def extract_requirements_for_standard(
    standard_no: str,
    clauses: List[Clause],
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """
    Extract checkable requirements for a single standard.
    Skips if standard is already cached unless force_refresh=True.
    """
    cache = load_requirements_cache()
    standards_dict = cache.get("standards", {})

    if not force_refresh and standard_no in standards_dict and standards_dict[standard_no]:
        logger.info("Cache hit for standard '%s' — skipping LLM extraction.", standard_no)
        return standards_dict[standard_no]

    if not clauses:
        logger.warning("No clauses provided for standard '%s'. Skipping extraction.", standard_no)
        return []

    logger.info("Extracting requirements for standard '%s' via LLM gateway...", standard_no)
    prompt = build_requirement_extraction_prompt(standard_no, clauses)

    result = generate_answer(prompt)
    raw_text = result.text.strip()

    # Parse JSON from LLM output
    extracted_items: List[Dict[str, Any]] = []
    try:
        # Extract markdown code block if present
        json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', raw_text)
        json_str = json_match.group(1) if json_match else raw_text
        
        # In case the LLM returned bare JSON
        if not json_match and not json_str.startswith("["):
            bracket_match = re.search(r'\[[\s\S]*\]', json_str)
            if bracket_match:
                json_str = bracket_match.group(0)

        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "text" in item:
                    extracted_items.append({
                        "standard_no": standard_no,
                        "clause_no": str(item.get("clause_no", clauses[0].clause_no or "General")),
                        "section_title": str(item.get("section_title", clauses[0].section_title or "")),
                        "text": str(item.get("text", "")).strip(),
                    })
    except Exception as exc:
        logger.error("Failed to parse JSON response for standard '%s': %s. Raw output: %s", standard_no, exc, raw_text)
        # Fallback to clause texts as discrete requirements
        for c in clauses:
            extracted_items.append({
                "standard_no": standard_no,
                "clause_no": c.clause_no or "General",
                "section_title": c.section_title or "",
                "text": c.text.strip(),
            })

    # Update cache
    standards_dict[standard_no] = extracted_items
    cache["standards"] = standards_dict
    save_requirements_cache(cache)

    logger.info("Extracted %d requirements for '%s' and saved to cache.", len(extracted_items), standard_no)
    return extracted_items
