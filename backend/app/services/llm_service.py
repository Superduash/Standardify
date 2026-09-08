"""
Standardify — LLM Service with triple fallback.

Priority:  Groq (llama-3.3-70b-versatile)
        -> Gemini (gemini-2.0-flash)
        -> Extractive (return best chunk verbatim)

generate_answer() NEVER raises — it always returns a valid dict.
"""
from __future__ import annotations

import logging
import textwrap
from typing import Any, Literal

from app.core.config import get_settings
from app.models.schemas import Citation

logger = logging.getLogger(__name__)

AnswerMode = Literal["groq", "gemini", "extractive", "no_match"]


def _build_prompt(question: str, chunks: list[dict[str, Any]]) -> str:
    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        std_no = meta.get("standard_no", "Unknown")
        clause = meta.get("clause_no", "")
        text = chunk.get("document", "")
        context_parts.append(
            f"[{i}] {std_no}{' — ' + clause if clause else ''}\n{text}"
        )
    context = "\n\n".join(context_parts)
    return textwrap.dedent(f"""
        You are Standardify, an expert assistant for Indian Bureau of Standards (BIS) regulations.
        Answer the question below using ONLY the provided standard clauses.
        If the answer is not in the clauses, say so clearly.
        Be precise and cite clause numbers in your answer.

        --- STANDARD CLAUSES ---
        {context}
        --- END CLAUSES ---

        Question: {question}

        Answer:
    """).strip()


def _build_citations(chunks: list[dict[str, Any]]) -> list[Citation]:
    citations: list[Citation] = []
    seen: set[str] = set()
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        key = f"{meta.get('standard_no', '')}:{meta.get('clause_no', '')}"
        if key not in seen:
            seen.add(key)
            citations.append(
                Citation(
                    standard_no=meta.get("standard_no", "Unknown"),
                    title=meta.get("title", ""),
                    clause_no=meta.get("clause_no") or None,
                    page=meta.get("page") or None,
                    chunk_text=chunk.get("document", "")[:300],
                )
            )
    return citations


def _try_groq(prompt: str) -> str | None:
    settings = get_settings()
    if not settings.groq_api_key:
        logger.debug("GROQ_API_KEY not set — skipping Groq")
        return None
    try:
        from groq import Groq
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("Groq call failed: %s", exc)
        return None


def _try_gemini(prompt: str) -> str | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.debug("GEMINI_API_KEY not set — skipping Gemini")
        return None
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return None


def _extractive_fallback(chunks: list[dict[str, Any]]) -> str:
    """Return the best chunk's text, trimmed and prefixed with a disclaimer."""
    best = chunks[0]
    meta = best.get("metadata", {})
    std_no = meta.get("standard_no", "Unknown")
    clause = meta.get("clause_no", "")
    text = best.get("document", "").strip()
    header = f"[Extractive match — {std_no}{', ' + clause if clause else ''}]\n\n"
    return header + text


def _score_confidence(chunks: list[dict[str, Any]]) -> Literal["high", "medium", "low"]:
    if not chunks:
        return "low"
    best_score = chunks[0].get("score", 0.0)
    if best_score >= 0.70:
        return "high"
    if best_score >= 0.45:
        return "medium"
    return "low"


def generate_answer(
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    similarity_threshold: float | None = None,
) -> dict[str, Any]:
    """
    Main entry point — always returns:
    {
        "answer": str,
        "citations": list[Citation],
        "confidence": "high" | "medium" | "low",
        "mode": "groq" | "gemini" | "extractive" | "no_match",
    }
    """
    settings = get_settings()
    threshold = similarity_threshold if similarity_threshold is not None else settings.similarity_threshold

    # Step 1: check if we have usable chunks
    usable = [c for c in retrieved_chunks if c.get("score", 0.0) >= threshold]
    if not usable:
        return {
            "answer": "I couldn't find a confident match in the indexed standards for your question.",
            "citations": [],
            "confidence": "low",
            "mode": "no_match",
        }

    citations = _build_citations(usable)
    confidence = _score_confidence(usable)
    prompt = _build_prompt(question, usable)

    # Step 2: Try Groq
    answer = _try_groq(prompt)
    if answer:
        return {"answer": answer, "citations": citations, "confidence": confidence, "mode": "groq"}

    # Step 3: Try Gemini
    answer = _try_gemini(prompt)
    if answer:
        return {"answer": answer, "citations": citations, "confidence": confidence, "mode": "gemini"}

    # Step 4: Extractive fallback — always succeeds
    answer = _extractive_fallback(usable)
    return {"answer": answer, "citations": citations, "confidence": confidence, "mode": "extractive"}
