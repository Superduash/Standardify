"""
Standardify — Cache warmer for demo rehearsal.

Fires each question from a rehearsal list through POST /api/v1/ask so
that the first answer is computed and cached before the recording starts.
All subsequent identical (or near-duplicate) questions during the demo
will be instant cache hits — zero additional LLM calls.

Usage:
  python scripts/warm_cache.py --questions rehearsal_questions.txt

Phase 0 stub: no logic yet — implemented in Phase 10 (pre-demo prep).
"""
from __future__ import annotations
