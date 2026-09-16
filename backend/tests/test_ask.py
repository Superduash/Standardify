"""
End-to-end tests for POST /api/v1/ask (Phase 3).

Covers:
  - Known-good question returns evidence_found=True with correct citation
  - Nonsense question returns evidence_found=False with no fabricated citation
  - Cache hit on repeated question results in exactly one LLM call
  - Mocked Groq 429 triggers Gemini fallback
  - Both providers mocked as failing → 503 response (not 500)
  - Latency: cache hit < 3s, cache miss < 8s

Phase 0 stub: test skeletons only — implemented in Phase 3.6.
"""
from __future__ import annotations
