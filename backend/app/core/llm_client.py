"""
Standardify — Unified LLM gateway (Groq → Gemini fallback).

ALL Groq and Gemini calls in the codebase go through this module.
No other file may import `groq` or `google.genai` directly (Golden Rule #2).

Exposes:
  generate_answer(prompt: str) -> LLMResult(text, provider_used, latency_ms)

Retry strategy: tenacity, max 2 attempts, short backoff on Groq 429/5xx.
Fallback chain: Groq → Gemini (google-genai SDK) → LLMUnavailableError.
Also hosts the prompt-building helper used by the /ask endpoint.

Phase 0 stub: no logic yet — implemented in Phases 3.1 and 3.2.
"""
from __future__ import annotations
