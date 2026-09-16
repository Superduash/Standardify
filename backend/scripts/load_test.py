"""
Standardify — 20-Request Concurrent Async Load & Latency Test (Phase 10.2).

Fires 20 concurrent requests to POST /api/v1/ask with a realistic mixture of
cached and novel questions. Computes p50, p95, and error metrics.

Usage:
  python scripts/load_test.py
  python scripts/load_test.py --url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

import httpx

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.main import app
from app.models.domain import LLMResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("load_test")

QUESTIONS = [
    # Cached items (pre-warmed during warmup phase)
    {"q": "What is the drop test height for plastic water bottles?", "type": "cached"},
    {"q": "What are the material requirements for plastic containers for packaged drinking water?", "type": "cached"},
    {"q": "What are mandatory nutritional parameters on packaged food labels?", "type": "cached"},
    {"q": "What is the minimum air delivery for electric ceiling fans?", "type": "cached"},
    {"q": "What is the maximum headform acceleration in helmet impact tests?", "type": "cached"},
    {"q": "What is the small parts cylinder diameter for toy safety?", "type": "cached"},
    {"q": "What is the drop test height for plastic water bottles?", "type": "cached"},
    {"q": "What are the material requirements for plastic containers for packaged drinking water?", "type": "cached"},
    {"q": "What are mandatory nutritional parameters on packaged food labels?", "type": "cached"},
    {"q": "What is the minimum air delivery for electric ceiling fans?", "type": "cached"},
    # Novel / varied questions
    {"q": "How much hydrostatic pressure must water bottles withstand?", "type": "novel"},
    {"q": "What are allergen declaration requirements for packaged food?", "type": "novel"},
    {"q": "What is the chin strap retention load test for motorcycle helmets?", "type": "novel"},
    {"q": "What safety valves are required on domestic pressure cookers?", "type": "novel"},
    {"q": "What risk group must domestic LED lighting luminaires comply with?", "type": "novel"},
    {"q": "What is the tensile pull test load for ceiling fan suspension shackles?", "type": "novel"},
    {"q": "Are recycled plastics permitted in packaged drinking water bottles?", "type": "novel"},
    {"q": "What is the sharp edges test requirement for children toys?", "type": "novel"},
    {"q": "What are the safety requirements for electric ceiling fan motor windings?", "type": "novel"},
    {"q": "What information must be stamped regarding expiry date on pre-packaged foods?", "type": "novel"},
]


async def send_ask_request(
    client: httpx.AsyncClient,
    base_url: str,
    question_info: Dict[str, str],
    idx: int,
) -> Dict[str, Any]:
    """Send a single ask request and record latency and response properties."""
    q_text = question_info["q"]

    start = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url}/api/v1/ask",
            json={"question": q_text},
            timeout=30.0,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0

        if response.status_code == 200:
            data = response.json()
            provider_used = data.get("provider_used", "none")
            is_cache_hit = provider_used == "cache"
            return {
                "idx": idx,
                "status": 200,
                "latency_ms": latency_ms,
                "is_cache_hit": is_cache_hit,
                "provider_used": provider_used,
                "error": None,
            }
        else:
            return {
                "idx": idx,
                "status": response.status_code,
                "latency_ms": latency_ms,
                "is_cache_hit": False,
                "provider_used": "error",
                "error": f"HTTP {response.status_code}: {response.text[:100]}",
            }
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "idx": idx,
            "status": 0,
            "latency_ms": latency_ms,
            "is_cache_hit": False,
            "provider_used": "exception",
            "error": str(exc),
        }


def compute_percentiles(latencies: List[float]) -> Tuple[float, float]:
    """Compute p50 and p95 for a list of latencies in ms."""
    if not latencies:
        return 0.0, 0.0
    sorted_lats = sorted(latencies)
    p50 = statistics.median(sorted_lats)
    p95_idx = int(math.ceil(0.95 * len(sorted_lats))) - 1
    p95 = sorted_lats[max(0, min(p95_idx, len(sorted_lats) - 1))]
    return round(p50, 2), round(p95, 2)


async def run_load_test(base_url: str = "http://testserver", concurrency: int = 20) -> None:
    """Execute concurrent load test against live server or in-process ASGI app."""
    logger.info("Initializing load test client (target: %s, concurrency: %d)...", base_url, concurrency)
    selected_questions = QUESTIONS[:concurrency]

    transport = None
    if "testserver" in base_url:
        transport = httpx.ASGITransport(app=app)

    # If mock mode needed (keys unconfigured in local test runner)
    mock_needed = (
        not settings.groq_api_key
        or "your_groq_api_key_here" in settings.groq_api_key
        or not settings.gemini_api_key
        or "your_gemini_api_key_here" in settings.gemini_api_key
    )

    patcher1 = None
    patcher2 = None
    if mock_needed and "testserver" in base_url:
        logger.info("API keys unconfigured in local test runner - using mock provider for novel LLM calls...")
        from app.api.v1 import ask as ask_module
        from app.core import llm_client
        mock_result = LLMResult(
            text="According to the relevant Indian Standard, technical specifications require strict compliance.",
            provider_used="groq",
            latency_ms=120,
        )
        patcher1 = patch.object(ask_module, "generate_answer", return_value=mock_result)
        patcher2 = patch.object(llm_client, "generate_answer", return_value=mock_result)
        patcher1.start()
        patcher2.start()

    try:
        async with httpx.AsyncClient(transport=transport, base_url=base_url if transport else None) as client:
            # 1. Warm up embedding singleton and exact cache
            logger.info("Pre-warming embedding singleton and exact cache...")
            from app.core.embeddings import embed_query
            embed_query("warmup query")

            for q in selected_questions:
                if q["type"] == "cached":
                    try:
                        await client.post(
                            f"{base_url}/api/v1/ask",
                            json={"question": q["q"]},
                            timeout=30.0,
                        )
                    except Exception as exc:
                        logger.debug("Warmup exception: %s", exc)

            # 2. Launch concurrent requests
            logger.info("Launching %d concurrent requests...", len(selected_questions))
            tasks = [
                send_ask_request(client, base_url, q_info, idx)
                for idx, q_info in enumerate(selected_questions)
            ]

            start_all = time.perf_counter()
            results = await asyncio.gather(*tasks)
            total_time_s = time.perf_counter() - start_all
    finally:
        if patcher1:
            patcher1.stop()
        if patcher2:
            patcher2.stop()

    # Analyze results
    success_count = sum(1 for r in results if r["status"] == 200)
    error_count = len(results) - success_count

    all_latencies = [r["latency_ms"] for r in results if r["status"] == 200]
    cache_hit_latencies = [r["latency_ms"] for r in results if r["status"] == 200 and r["is_cache_hit"]]
    cache_miss_latencies = [r["latency_ms"] for r in results if r["status"] == 200 and not r["is_cache_hit"]]

    overall_p50, overall_p95 = compute_percentiles(all_latencies)
    hit_p50, hit_p95 = compute_percentiles(cache_hit_latencies)
    miss_p50, miss_p95 = compute_percentiles(cache_miss_latencies)

    print("\n" + "=" * 50)
    print("      STANDARDIFY LOAD TEST REPORT (20 REQS)     ")
    print("=" * 50)
    print(f"Total Requests:       {len(results)}")
    print(f"Success Count:        {success_count}")
    print(f"Error Count:          {error_count}")
    print(f"Total Test Wall Time: {total_time_s:.2f}s")
    print("-" * 50)
    print(f"Cache Hits:           {len(cache_hit_latencies)} requests")
    print(f"Cache-hit p50:        {hit_p50} ms")
    print(f"Cache-hit p95:        {hit_p95} ms")
    print("-" * 50)
    print(f"Cache Misses:         {len(cache_miss_latencies)} requests")
    print(f"Cache-miss p50:       {miss_p50} ms")
    print(f"Cache-miss p95:       {miss_p95} ms")
    print("-" * 50)
    print(f"Overall p50:          {overall_p50} ms")
    print(f"Overall p95:          {overall_p95} ms")
    print("=" * 50 + "\n")


def main() -> None:
    """CLI parser for load testing."""
    parser = argparse.ArgumentParser(description="Standardify 20-Request Load Test")
    parser.add_argument("--url", type=str, default="http://testserver", help="Base URL of target backend (default: http://testserver for ASGI)")
    parser.add_argument("--concurrency", type=int, default=20, help="Number of concurrent requests (default: 20)")
    args = parser.parse_args()

    asyncio.run(run_load_test(base_url=args.url, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
