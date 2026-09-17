"""
Standardify — LLM Client Gateway (Phase 3.2).

Single point of entry for all Large Language Model inference calls (Golden Rule #2).
Implements Groq primary provider inference with tenacity retries and automatic
fallback to Google Gemini (`google-genai` SDK).
"""

from __future__ import annotations

import logging
import re
import time
from typing import List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.core.cache import record_llm_call
from app.models.domain import LLMResult, LLMUnavailableError

logger = logging.getLogger(__name__)

# Default model identifiers
GROQ_PRIMARY_MODEL: str = "llama-3.3-70b-versatile"
GEMINI_FALLBACK_MODEL: str = "gemini-2.5-flash"


def _extract_used_clause_ids(text: str) -> List[str]:
    """Extract cited clause markers like [CITATIONS: IS 9001:2025::4.1] from LLM output."""
    matches = re.findall(r'\[CITATIONS?:\s*([^\]]+)\]', text, flags=re.IGNORECASE)
    ids: list[str] = []
    for match in matches:
        # Split by comma or semicolon
        items = re.split(r'[,;]\s*', match)
        for it in items:
            clean_it = it.strip()
            if clean_it and clean_it not in ids:
                ids.append(clean_it)
    return ids


def _clean_response_text(text: str) -> str:
    """Remove trailing [CITATIONS: ...] tags from user-facing answer text."""
    cleaned = re.sub(r'\n*\[CITATIONS?:\s*[^\]]+\]', '', text, flags=re.IGNORECASE)
    return cleaned.strip()


def _is_valid_key(key: Optional[str]) -> bool:
    """Check if an API key is present and not a default placeholder."""
    if not key or not key.strip():
        return False
    val = key.strip().lower()
    return val not in ("your_groq_api_key_here", "your_gemini_api_key_here", "none", "null", "placeholder", "")


def _call_groq(prompt: str) -> str:
    """Call Groq API with tenacity-based transient error retry."""
    if not _is_valid_key(settings.groq_api_key):
        raise ValueError("GROQ_API_KEY is not configured in backend/.env.")

    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        reraise=True,
    )
    def _execute_groq_request() -> str:
        completion = client.chat.completions.create(
            model=GROQ_PRIMARY_MODEL,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
            timeout=15.0,
        )
        if completion.choices and completion.choices[0].message:
            content = completion.choices[0].message.content
            if content:
                return content
        raise ValueError("Empty response received from Groq.")

    return _execute_groq_request()


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API using modern google-genai SDK."""
    if not _is_valid_key(settings.gemini_api_key):
        raise ValueError("GEMINI_API_KEY is not configured in backend/.env.")

    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=GEMINI_FALLBACK_MODEL,
        contents=prompt,
    )
    if response and hasattr(response, "text") and response.text:
        return response.text

    raise ValueError("Empty response received from Gemini.")


def generate_answer(prompt: str) -> LLMResult:
    """
    Generate an answer using Groq with automatic fallback to Gemini.

    Args:
        prompt: Grounded prompt text containing evidence and question.

    Returns:
        LLMResult: Output containing generated answer, provider, and latency.

    Raises:
        LLMUnavailableError: If both primary and fallback providers fail or are unconfigured.
    """
    start_time = time.time()
    errors: list[str] = []

    # 1. Attempt Primary Provider: Groq
    try:
        logger.info("Calling primary LLM provider (Groq: %s)...", GROQ_PRIMARY_MODEL)
        raw_output = _call_groq(prompt)
        elapsed_ms = int((time.time() - start_time) * 1000)

        record_llm_call("groq")
        logger.info("Groq inference succeeded in %d ms.", elapsed_ms)

        clause_ids = _extract_used_clause_ids(raw_output)
        clean_text = _clean_response_text(raw_output)

        return LLMResult(
            text=clean_text,
            provider_used="groq",
            latency_ms=elapsed_ms,
            used_clause_ids=clause_ids,
        )
    except Exception as exc:
        err_msg = f"Groq primary provider failed: {exc}"
        logger.warning("%s. Falling back to Gemini...", err_msg)
        errors.append(err_msg)

    # 2. Attempt Fallback Provider: Google Gemini
    fallback_start = time.time()
    try:
        logger.info("Calling fallback LLM provider (Gemini: %s)...", GEMINI_FALLBACK_MODEL)
        raw_output = _call_gemini(prompt)
        elapsed_ms = int((time.time() - fallback_start) * 1000)

        record_llm_call("gemini")
        logger.info("Gemini inference succeeded in %d ms.", elapsed_ms)

        clause_ids = _extract_used_clause_ids(raw_output)
        clean_text = _clean_response_text(raw_output)

        total_elapsed_ms = int((time.time() - start_time) * 1000)
        return LLMResult(
            text=clean_text,
            provider_used="gemini",
            latency_ms=total_elapsed_ms,
            used_clause_ids=clause_ids,
        )
    except Exception as exc:
        err_msg = f"Gemini fallback provider failed: {exc}"
        logger.error("%s.", err_msg)
        errors.append(err_msg)

    # 3. Both Providers Failed
    total_elapsed_ms = int((time.time() - start_time) * 1000)
    joined_errs = "; ".join(errors)
    logger.critical("All LLM providers failed (%d ms): %s", total_elapsed_ms, joined_errs)
    raise LLMUnavailableError(
        f"All AI inference providers are currently unavailable ({joined_errs}). "
        f"Standards Search, Registry, Gap Checker, and Graph remain fully available."
    )
