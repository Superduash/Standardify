# Standardify Backend

AI-powered assistant for Indian Bureau of Standards (BIS) — SIH 2026, Team Trailblazers.

## Phase Status

| Phase | Status |
|---|---|
| 0 — Foundation & Scaffold | ✅ Complete (this commit) |
| 1 — Ingestion Pipeline | 🔲 Not started |
| 2 — Core Retrieval | 🔲 Not started |
| 3 — Answer Generation | 🔲 Not started |
| 5 — Gap Checker | 🔲 Not started |
| 6 — Standards Graph | 🔲 Not started |
| 7 — Status Tracking | 🔲 Not started |
| 8 — Standard Search | 🔲 Not started |
| 9 — API Hardening | 🔲 Not started |
| 10 — Demo Readiness | 🔲 Not started |

## Quick Start

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # fill in API keys
uvicorn app.main:app --reload
```

## Repository Structure

See `backendplan.md §4` — the folder structure in this repo matches it exactly.

## Tech Stack

FastAPI · Uvicorn · Pydantic v2 · PyMuPDF · pdfplumber · pytesseract ·
BGE-M3 (FlagEmbedding, local) · ChromaDB · LlamaIndex · Groq · Gemini (google-genai) ·
NetworkX · SQLite FTS5 · diskcache · pytest
