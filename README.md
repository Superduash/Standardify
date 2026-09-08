# Standardify 🇮🇳

> **AI-Powered Compliance & Assistant for Bureau of Indian Standards (BIS)**  
> *Smart India Hackathon 2026 Prototype — Problem Statement SIH26107*

---

## Overview

**Standardify** is a Retrieval-Augmented Generation (RAG) assistant designed to make Indian Standards (BIS) easily searchable, interpretable, and actionable. It helps manufacturers, compliance officers, and consumers check product specifications against mandatory BIS requirements, trace clause dependencies, and detect compliance gaps.

---

## Key Features

- 💬 **Clause Q&A**: Ask technical compliance questions and receive answers with exact clause citations. Supports **zero-API-key mode** (extractive RAG fallback) or Groq / Google Gemini if configured.
- 📋 **Gap Checker**: Paste product specifications to run automated compliance checks and receive a prioritized list of missing or non-compliant clauses.
- 🔍 **Standards Search**: Rapid full-text and semantic search across indexed standards, categories, and mandates.
- 🕸️ **Standards Graph**: Interactive 2D knowledge graph showing cross-references, supersessions, and category hierarchies across BIS documents.

---

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide / Heroicons, `react-force-graph-2d`
- **Backend**: Python, FastAPI, ChromaDB (vector database), BAAI/bge-m3 embeddings, NetworkX
- **LLM Engine**: Groq (Llama 3.3) / Google Gemini with transparent fallback to local extractive RAG

---

## Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm

### 2. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # On Windows (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
python ingest.py           # Ingests seed standards into ChromaDB
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit the app at **`http://localhost:5173`**.

---

## Environment Variables (Optional)

The application runs fully offline/locally with **zero API keys** via extractive fallback. To enable generative LLM responses, configure `backend/.env`:

```env
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
LLM_PROVIDER=groq          # or gemini / extractive
```

---

## Disclaimer

The seed standards included in `backend/data/standards_raw/` are synthetic samples modeled after actual BIS standards for prototype and hackathon demonstration purposes.
