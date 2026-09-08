# Standardify 🇮🇳

> **AI-Powered Compliance & Assistant for Bureau of Indian Standards (BIS)**  
> *Smart India Hackathon 2026 Prototype — Problem Statement SIH26107*

---

## Overview

**Standardify** is an enterprise-grade Retrieval-Augmented Generation (RAG) assistant designed to make Indian Standards (BIS) easily searchable, interpretable, and actionable. It empowers manufacturers, compliance officers, and consumers to check product specifications against mandatory BIS requirements, trace clause dependencies, and detect compliance gaps before submitting for certification.

---

## Key Features

- 💬 **Clause Q&A**: Ask technical compliance questions in natural language and receive answers with exact clause citations and confidence ratings. Works in **zero-API-key mode** (extractive RAG fallback) or with Groq (`llama-3.3-70b-versatile`) / Google Gemini (`gemini-2.0-flash`).
- 📋 **Compliance Gap Checker**: Paste product descriptions and engineering specifications to run automated compliance checks and receive a prioritized list of missing or unaddressed clauses.
- 🔍 **Standards Search**: Rapid semantic and keyword search across indexed standards, categories, and technical mandates with instant relevance scoring.
- 🕸️ **Standards Knowledge Graph**: Interactive 2D force-directed relationship graph visualizing dependencies, cross-references, and supersession links among BIS standards.

---

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS (v4), `react-force-graph`, Axios
- **Backend**: Python 3.12, FastAPI, ChromaDB (vector database), BAAI/bge-m3 embeddings (SentenceTransformers), NetworkX
- **LLM Layer**: Groq / Google Gemini with transparent local extractive fallback
- **Seed Data**: 8 Indian standards spanning Household Electricals, Packaged Water, Toys, Helmets, Packaged Food, Pressure Cookers, and LED Lighting

---

## Quick Start (One-Click on Windows)

### 1. Setup (Run Once)
Double click **`setup.bat`** (or run `setup.bat` in Command Prompt / PowerShell).
This automatically:
- Creates a Python virtual environment (`backend/venv`)
- Installs all backend dependencies
- Ingests the seed standards into ChromaDB with BGE-M3 embeddings
- Installs all frontend npm dependencies

### 2. Launch
Double click **`start-all.bat`**.
This opens both servers in parallel:
- **Backend API**: `http://localhost:8000` (Swagger UI at `/docs`)
- **Frontend Web UI**: `http://localhost:5173`

---

## Manual Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
python ingest.py           # Embeds seed standards into ChromaDB
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Automated API Verification
To test and verify all 5 API endpoints (`/api/health`, `/api/query`, `/api/search`, `/api/graph`, `/api/gap-check`):
```bash
cd backend
python test_api.py
```

---

## Configuration (Optional)

The application runs in **zero-API-key mode** right out of the box using extractive RAG. To enable generative AI answers:

Edit `backend/.env`:
```env
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
```

---

## Disclaimer

The seed standards included in `backend/data/standards_raw/` are structured samples modeled after actual BIS standards for hackathon demonstration and testing purposes.
