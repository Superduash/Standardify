# Standardify Backend

AI-powered compliance and search assistant for the Bureau of Indian Standards (BIS) — SIH 2026, Team Trailblazers.

---

## Phase Status

| Phase | Description | Status |
|---|---|---|
| **0** | Foundation, Models, Settings & Scaffold | ✅ Complete |
| **1** | Multi-Format Ingestion Pipeline & SQLite Registry | ✅ Complete |
| **2** | Core Hybrid Retrieval Engine (BGE-M3 + BM25 + Reciprocal Rank Fusion) | ✅ Complete |
| **3** | Grounded Answer Generation & Resilient LLM Gateway (Groq + Gemini + Cache) | ✅ Complete |
| **5** | Deterministic Compliance Gap Checker & Cached Requirements | ✅ Complete |
| **6** | Standards Relationship Graph & NetworkX Topology Engine | ✅ Complete |
| **7** | Standard Status & Amendment / Supersession Tracking | ✅ Complete |
| **8** | Fast SQLite FTS5 Keyword & Semantic Standards Search | ✅ Complete |
| **9** | Unified Response Schemas, OpenAPI Specs & Rate Limiting | ✅ Complete |
| **10** | Performance Tuning, Automated Demo Seeding, Load Testing & Render Deployment | ✅ Complete |

---

## Quick Start

### 1. Environment Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Set your `GROQ_API_KEY` and `GEMINI_API_KEY` in `.env`.

### 2. One-Command Demo Dataset Seeding

To build or refresh the entire demo database, vector indices, relationship graph, and requirement caches:

```bash
python scripts/seed_demo_dataset.py
```

This single idempotent command orchestrates:
1. SQLite registry table creation (`data/registry.db`)
2. Multi-format PDF / structured clause chunking & metadata extraction
3. BGE-M3 dense vector embeddings generation
4. ChromaDB persistent collection upsert (`data/chroma_store`)
5. FTS5 full-text search index synchronization
6. NetworkX cross-standard relationship graph extraction (`data/graph.json`)
7. Standard requirement checklists extraction & validation (`data/requirements_cache.json`)
8. Automated retrieval verification

### 3. Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger UI)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Testing & Quality Assurance

### Run Complete Pytest Suite
```bash
pytest
```
*Executes all 62 regression tests across retrieval, grounded QA, gap checking, graph queries, status tracking, search, API contracts, error handling, and health endpoints.*

### Run Concurrency & Load Benchmark
```bash
python scripts/load_test.py --concurrency 20 --url http://127.0.0.1:8000
```
*Fires concurrent requests mixing cached and novel queries, reporting p50 and p95 latencies for cache hits, cache misses, and overall throughput.*

---

## API Endpoints Summary

All routes are prefixed with `/api/v1`:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/health` | `GET` | Service liveness, vector store status, and loaded models |
| `/api/v1/health/quota` | `GET` | LLM provider health and rate limit tracking |
| `/api/v1/ask` | `POST` | Grounded compliance Q&A with exact clause citations and cache logging |
| `/api/v1/gap-check` | `POST` | Automated product specification compliance gap analysis |
| `/api/v1/graph` | `GET` | Full standards dependency, supersession, and reference graph |
| `/api/v1/standards/search` | `GET` | Hybrid standard search (Exact > FTS5 Keyword > Semantic) |
| `/api/v1/standards/{standard_no}/status` | `GET` | Standard validity status and amendment history |
| `/api/v1/standards/{standard_no}/requirements` | `GET` | Pre-extracted compliance checklist for a standard |

---

## Deployment Architecture (Render)

Standardify is configured for zero-friction containerized deployment on Render via [`render.yaml`](file:///C:/Users/Superduash/Desktop/Projects/Standardify/backend/render.yaml).

### Design & Storage Strategy:
- **Zero Bloat in Git**: Heavy binary vectors and raw ML model weights are excluded from Git.
- **Build-Time Seeding**: During `buildCommand` (`pip install -r requirements.txt && python scripts/seed_demo_dataset.py`), the seed script rebuilds the SQLite registry and ChromaDB vector store deterministically in ~15 seconds.
- **Lightweight Inference**: BGE-M3 embedding model runs on CPU in FP32 mode with singleton in-memory caching across requests.
- **Disk Persistence**: Response caching (`diskcache`) and ChromaDB vector persistence ensure rapid response times (<50ms for cached queries).
- **Environment Isolation**: Secrets are injected strictly via Render Environment Variables.
