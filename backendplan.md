# Standardify — Backend Development Master Plan
**Team Trailblazers · SIH26107 · AI-Powered Intelligent Assistant for Indian Standards & BIS Services**

This is the single source of truth for building the Standardify backend. It is written to be consumed in small, numbered pieces (Phase.Subphase, e.g. `3.2`) so you can feed one sub-phase at a time to ChatGPT to generate a precise coding-agent prompt, then hand that prompt to your agent (Antigravity or similar). Each sub-phase is scoped tight enough that the agent cannot "wander" into other files and break what already works.

---

## 0. How To Use This Document

1. **Never skip ahead.** Sub-phases have hard dependencies (listed in each one). Complete and verify a sub-phase before moving to the next.
2. **One sub-phase = one agent prompt = one commit.** After the agent finishes a sub-phase, run the listed Acceptance Criteria, commit (`git commit -m "phase X.Y: <name>"`), and only then move on.
3. **The repo structure in §4 is locked from Phase 0 onward.** No sub-phase is allowed to restructure folders unless that sub-phase explicitly says so. This is the single biggest reason agent-generated code "breaks old code" — an agent reorganizing files it wasn't asked to touch. Forbid it explicitly in every prompt (template given in §10).
4. When you turn a sub-phase into a ChatGPT prompt, paste **§10 Master Context Block** + the specific sub-phase section + your current file tree. This is what stops regressions.
5. §11 is your pre-recording checklist — read it now so you understand *why* certain design choices (caching, key-swap script, offline LLM use) exist before you start building.

---

## 1. Project Snapshot (what judges are scoring against)

| PPT Section | Must Ship | Plan Reference |
|---|---|---|
| Proposed Solution | Conversational Q&A, Standard/Clause/Page citation, confidence score | Phase 2, 3 |
| Innovation — Compliance Gap Checker | Product description → applicable standards → missing requirements | Phase 5 |
| Innovation — Standards Relationship Graph | Interactive graph of related/referenced/superseding standards | Phase 6 |
| Innovation — Multi-Standard Reasoning | Combine clauses from >1 standard for compound questions | Phase 3.5 |
| Innovation — Amendment & Withdrawal Tracking | Warn when a cited standard is outdated/withdrawn | Phase 7 |
| Feasibility — "no evidence, no answer" | Refuse to hallucinate when retrieval confidence is low | Phase 3.4, 4.3 |
| Feasibility — hybrid search | Semantic + keyword retrieval | Phase 4.4 |
| Tech stack (slide 3) | FastAPI, PyMuPDF/pdfplumber/pytesseract, BGE-M3, ChromaDB, LlamaIndex, Groq+Gemini, NetworkX | Every phase |
| Standard Search | Search by product / keyword / standard number | Phase 8 |

If a feature isn't traceable to a row above, it's scope creep — cut it or move it to Phase 12 (stretch).

---

## 2. Non-Negotiable Golden Rules (put these in every agent prompt)

1. **Locked folder structure.** Only create/modify files inside the paths the current sub-phase names. Do not rename, move, or delete existing files.
2. **Single LLM gateway.** All Groq/Gemini calls go through `app/core/llm_client.py`. No other file may import `groq` or `google.genai` directly. This is what makes rate-limit handling and provider-swapping possible without touching 10 files later.
3. **Single embedding gateway.** All BGE-M3 calls go through `app/core/embeddings.py` (loaded once as a singleton, not per-request).
4. **Config via `.env` only.** No hardcoded API keys, paths, or model names anywhere else — everything reads from `app/config.py`.
5. **Every function has type hints + a docstring.** Every new endpoint has a Pydantic request AND response model in `app/models/schemas.py` — never a bare `dict`.
6. **Idempotent ingestion.** Re-running any ingestion script must not duplicate rows in ChromaDB/SQLite. Always upsert on a stable ID (`standard_no + clause_id`).
7. **Never break existing tests.** Before a sub-phase is "done," `pytest` must pass for *all* tests written so far, not just the new ones.
8. **Fail safe, not silent.** If retrieval confidence is below threshold, or an LLM call fails after fallback, the API must return a clear `evidence_found: false` response — never an empty 500 or a fabricated answer.
9. **No feature touches two "layers" at once.** Ingestion code never calls FastAPI code; API route files never talk to ChromaDB directly — they go through `app/core/*`. This is what lets you regenerate one layer without breaking another.

---

## 3. Final Tech Stack (locked, matches PPT slide 3)

| Layer | Tool | Notes for this build |
|---|---|---|
| API framework | FastAPI + Uvicorn + Pydantic v2 | async routes, OpenAPI docs free |
| PDF extraction | PyMuPDF (`fitz`) primary, `pdfplumber` for tables | pytesseract OCR fallback for scanned pages |
| Chunking/metadata | Custom regex + rule engine | BIS clause numbering is regular enough to parse reliably |
| Embeddings | `BAAI/bge-m3` via `FlagEmbedding` (or `sentence-transformers` fallback) | runs **locally**, no external rate limit, dense vectors only (skip sparse/ColBERT — not worth the complexity for this scope) |
| Vector DB | ChromaDB (persistent client, local disk) | one collection, rich metadata filters |
| RAG orchestration | LlamaIndex (`VectorStoreIndex` over a Chroma vector store) | keeps retrieval logic declarative and swappable |
| Answer LLM (primary) | Groq — `llama-3.3-70b-versatile` (quality) / `llama-3.1-8b-instant` (speed fallback) | free tier ≈ 30 req/min, ~6–15k tokens/min, ~14,400 req/day *(verify current numbers at console.groq.com/settings/limits before demo — Groq revises these)* |
| Answer LLM (fallback) | Gemini — `gemini-2.5-flash` via the **`google-genai`** SDK (`pip install google-genai`) | `google-generativeai` is deprecated (EOL Nov 30, 2025) — do not let the agent use it. Free tier ≈ 10–15 req/min, ~250k tokens/min, low req/day *(verify at ai.google.dev/gemini-api/docs/rate-limits)* |
| Knowledge graph | NetworkX, persisted as JSON | rendered by `react-force-graph` on the frontend later |
| Search | SQLite FTS5 (keyword) + Chroma (semantic) combined | no extra service needed |
| Caching | `diskcache` (exact + semantic near-duplicate cache) | this is your quota insurance policy — see Phase 3.3 |
| Testing | `pytest`, `httpx.AsyncClient` | golden Q&A regression set |
| Deployment | Render (backend), env vars for keys | matches PPT slide 3 |

---

## 4. Locked Repository Structure (create this exact tree in Phase 0, nowhere else after)

```
standardify-backend/
├── app/
│   ├── main.py                      # FastAPI app + startup/shutdown events
│   ├── config.py                    # pydantic-settings: all env vars
│   ├── logging_conf.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py            # aggregates all routers
│   │       ├── ask.py               # POST /api/v1/ask
│   │       ├── gap_check.py         # POST /api/v1/gap-check
│   │       ├── graph.py             # GET  /api/v1/graph/{standard_no}, /full
│   │       ├── standards.py         # GET  /api/v1/standards/search, /{id}, /{id}/status
│   │       └── health.py            # GET  /api/v1/health, /health/quota
│   ├── core/
│   │   ├── retrieval.py             # LlamaIndex + Chroma retrieval
│   │   ├── embeddings.py            # BGE-M3 singleton wrapper
│   │   ├── llm_client.py            # Groq→Gemini fallback, quota tracking, retries
│   │   ├── cache.py                 # diskcache exact + semantic cache
│   │   ├── confidence.py            # confidence scoring formula
│   │   ├── graph_engine.py          # NetworkX load/query/subgraph
│   │   ├── gap_checker.py           # gap-check business logic
│   │   └── status_tracker.py        # amendment/withdrawal lookups + warnings
│   ├── models/
│   │   ├── schemas.py               # ALL Pydantic request/response models
│   │   └── domain.py                # internal dataclasses (Clause, StandardMeta, ...)
│   └── ingestion/
│       ├── pdf_extract.py           # PyMuPDF + pdfplumber + pytesseract OCR
│       ├── clause_chunker.py        # splits raw text into clause-level chunks
│       ├── metadata_extractor.py    # regex: standard no / clause no / page
│       ├── relationship_extractor.py# supersedes / references / same-category edges
│       ├── requirement_extractor.py # ONE-TIME offline LLM extraction, cached
│       ├── embed_and_store.py       # batch-embeds chunks → ChromaDB upsert
│       └── run_ingestion.py         # CLI orchestrator for the whole pipeline
├── data/
│   ├── raw_pdfs/                    # source BIS PDFs (git-ignored, see Phase 1.1)
│   ├── processed/                   # extracted JSON per document (debuggable)
│   ├── registry.db                  # SQLite: standards metadata + status
│   ├── graph.json                   # persisted NetworkX graph
│   ├── requirements_cache.json      # cached per-standard requirement checklists
│   └── chroma_store/                # ChromaDB persistent directory
├── tests/
│   ├── golden_qa.json               # ~20 question/expected-standard pairs
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_ask.py
│   ├── test_gap_check.py
│   ├── test_graph.py
│   └── test_status.py
├── scripts/
│   ├── seed_demo_dataset.py         # curates the 8–12 demo standards end-to-end
│   ├── warm_cache.py                # pre-computes answers for rehearsed demo Qs
│   └── switch_provider_key.sh       # swap Gemini key with zero code changes
├── requirements.txt
├── .env.example
├── render.yaml
└── README.md
```

---

## 5. Data Sourcing Rule (read before Phase 1)

Do **not** attempt to scrape or bulk-download the full BIS corpus — most standards are sold by BIS and are not freely redistributable, and BIS's portal actively restricts bulk access. For a build of this quality, curate **8–12 real, freely-available BIS documents**: preview/summary PDFs from BIS "Know Your Standards," gazette notifications, and draft standards published for public comment (the same free sources the PPT's own References slide lists). A focused, fully-correct 10-standard system beats a shallow 500-standard one — the judges are testing depth of the pipeline, not corpus size, and slide 4 ("Focused implementation… then expand") already commits you to this scope.

---

## PHASE 0 — Foundation & Environment

### 0.1 Repo scaffold
**Goal:** create the exact tree in §4, empty files with docstring stubs only, no logic yet.
**Files:** entire tree above.
**Acceptance criteria:**
- [ ] `tree standardify-backend` matches §4 exactly.
- [ ] `git init` + first commit.
- [ ] `.gitignore` excludes `data/raw_pdfs/`, `data/chroma_store/`, `.env`, `__pycache__/`.

### 0.2 Environment & config
**Goal:** `app/config.py` using `pydantic-settings`, reading `GROQ_API_KEY`, `GEMINI_API_KEY`, `EMBEDDING_MODEL_NAME`, `CHROMA_PERSIST_DIR`, `LLM_PRIMARY_PROVIDER`, `LOG_LEVEL`, `CACHE_TTL_SECONDS`, `CONFIDENCE_FLOOR`.
**Files:** `app/config.py`, `.env.example` (dummy values only, never real keys), `requirements.txt` (pin every package named in §3).
**Acceptance criteria:**
- [ ] `python -c "from app.config import settings; print(settings)"` runs without error when `.env` is filled.
- [ ] Missing required var raises a clear validation error, not a silent `None`.

### 0.3 App skeleton, logging, health check
**Goal:** `app/main.py` boots FastAPI, mounts `app/api/v1/router.py`, structured logging via `logging_conf.py`, CORS middleware (open for now, tightened in 8.2).
**Files:** `app/main.py`, `app/logging_conf.py`, `app/api/v1/health.py`, `app/api/v1/router.py`.
**Acceptance criteria:**
- [ ] `uvicorn app.main:app --reload` starts cleanly.
- [ ] `GET /api/v1/health` → `200 {"status": "ok"}`.
- [ ] `/docs` renders Swagger UI.

**Depends on:** none. **Do NOT** touch `app/core/` or `app/ingestion/` in this sub-phase — they don't exist as logic yet, only as empty stub files.

---

## PHASE 1 — Data Ingestion Pipeline (offline, runs once per corpus update)

### 1.1 PDF intake & raw storage
**Goal:** place curated PDFs in `data/raw_pdfs/`, write `pdf_extract.py`'s text-extraction function (PyMuPDF primary; if a page's extracted text is near-empty, fall back to `pdfplumber`, and if still empty, rasterize the page and run `pytesseract` OCR).
**Files:** `app/ingestion/pdf_extract.py`.
**Acceptance criteria:**
- [ ] Function `extract_document(path) -> list[PageText]` returns page number + raw text + `used_ocr: bool` per page.
- [ ] Manually verify on 2 scanned and 2 digital-text PDFs that OCR only triggers when needed (don't OCR every page — it's slow and unnecessary).

### 1.2 Clause-level chunking
**Goal:** `clause_chunker.py` splits each document's raw page text into clause-sized chunks (target 150–400 tokens each) using BIS's numbered-clause pattern (e.g. `4.2`, `5.1.3`) as split points, falling back to paragraph splitting where no clause numbering is detected.
**Files:** `app/ingestion/clause_chunker.py`.
**Acceptance criteria:**
- [ ] Given a sample extracted page, output is a list of `Clause(text, approx_clause_no, page_no)`.
- [ ] No chunk exceeds ~500 tokens (hard cap, to keep retrieval + prompt costs predictable).

### 1.3 Metadata extraction
**Goal:** `metadata_extractor.py` — regex-based extraction of: standard number (e.g. `IS 374:2019`), clause number, section title, document title, category (manual mapping table for the demo's 8–12 standards is fine — don't over-engineer a classifier for this scope).
**Files:** `app/ingestion/metadata_extractor.py`, `app/models/domain.py` (`StandardMeta`, `Clause` dataclasses).
**Acceptance criteria:**
- [ ] Every chunk from 1.2 gets tagged with `standard_no`, `clause_no`, `page_no`, `title` with >90% accuracy on manual spot-check across the demo set.
- [ ] Untaggable chunks are flagged `needs_review` rather than silently dropped.

### 1.4 Standards metadata registry (SQLite)
**Goal:** `registry.db` schema: `standards(standard_no PK, title, category, status, superseded_by, last_amended_date, source_url)`. Seed script populates this for the demo set (status data is curated by hand for the demo — this is legitimate; BIS doesn't expose a clean status API, so hand-curated is the correct approach at this scope, not a shortcut).
**Files:** `app/ingestion/run_ingestion.py` (registry-writing step), `data/registry.db`.
**Acceptance criteria:**
- [ ] `SELECT * FROM standards` returns one row per demo standard with no NULL `status`.

### 1.5 Embedding generation → ChromaDB
**Goal:** `embed_and_store.py` batch-embeds all clause chunks with BGE-M3 (via `app/core/embeddings.py`, built in 2.1 — so do 2.1 first, see dependency note) and upserts into a single Chroma collection `bis_clauses`, ID = `f"{standard_no}::{clause_no}::{page_no}"`, metadata = everything from 1.3.
**Files:** `app/ingestion/embed_and_store.py`.
**Depends on:** Phase 2.1 (embedding singleton) must exist first — build 2.1 before 1.5, even though it's numbered later; note this explicitly in the agent prompt for 1.5.
**Acceptance criteria:**
- [ ] Re-running the script twice does not duplicate vectors (upsert, not insert).
- [ ] `collection.count()` matches the number of chunks from 1.2/1.3.

### 1.6 Ingestion QA script
**Goal:** `run_ingestion.py --validate` runs a handful of known questions against the freshly built index and prints top-3 retrieved clauses, so you can eyeball correctness before moving to Phase 2.
**Acceptance criteria:**
- [ ] For 5 hand-picked questions with known correct standards, the correct standard appears in the top-3 results for at least 4 of them.

---

## PHASE 2 — Core Retrieval Engine (RAG)

### 2.1 Embedding singleton
**Goal:** `app/core/embeddings.py` loads `BAAI/bge-m3` **once** at process startup (not per-call), exposes `embed_query(text) -> vector` and `embed_batch(texts) -> list[vector]`. Use `use_fp16=True` for speed if a GPU is available; fall back gracefully to CPU fp32.
**Acceptance criteria:**
- [ ] Model loads once (add a log line on load); subsequent calls reuse the loaded model (no re-instantiation per request — verify by checking load only happens once across multiple `/ask` calls in Phase 3 testing).

### 2.2 ChromaDB client + LlamaIndex wiring
**Goal:** `app/core/retrieval.py` sets up a persistent `chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)`, wraps the `bis_clauses` collection in a LlamaIndex `ChromaVectorStore`, builds a `VectorStoreIndex` from it (index existing vectors, don't re-embed).
**Acceptance criteria:**
- [ ] `retrieval.get_index()` returns a working LlamaIndex index without re-running embedding.

### 2.3 Hybrid retrieval
**Goal:** `retrieve(question, top_k=5, standard_filter=None) -> list[RetrievedClause]` combining (a) BGE-M3 dense semantic search via the index and (b) a lightweight keyword boost (simple substring/BM25-style score via `rank-bm25` over the same corpus) — merge and re-rank by combined score. Support optional metadata filter (e.g. restrict to a specific `standard_no` for multi-standard reasoning in 3.5).
**Acceptance criteria:**
- [ ] Function returns clauses sorted by combined score with `similarity_score` attached to each.
- [ ] Filtering by `standard_no` returns only clauses from that standard.

### 2.4 Confidence scoring
**Goal:** `app/core/confidence.py` — `score(retrieved_clauses) -> ConfidenceResult(value: float 0-1, label: "high"|"medium"|"low", evidence_found: bool)`. Formula: weight top-1 similarity score most heavily, add a small bonus if ≥2 chunks agree on the same standard, and any score below `settings.CONFIDENCE_FLOOR` (e.g. 0.35) forces `evidence_found=False` regardless of the rest.
**Acceptance criteria:**
- [ ] Documented thresholds in the docstring (don't bury magic numbers unexplained).
- [ ] Unit test: a clearly-relevant clause set scores "high"; an empty/irrelevant retrieval scores `evidence_found=False`.

### 2.5 Retrieval regression test
**Goal:** `tests/test_retrieval.py` runs `tests/golden_qa.json` (build this file now — ~20 question → expected `standard_no` pairs across your demo set) and asserts top-3 hit rate ≥ 80%.
**Acceptance criteria:**
- [ ] `pytest tests/test_retrieval.py` passes at the 80% threshold.

---

## PHASE 3 — Grounded Answer Generation (`/api/v1/ask`)

### 3.1 Prompt template
**Goal:** a single prompt-building function in `llm_client.py` (or a `prompts.py` helper it imports) that: (a) inserts only the top-3 retrieved clauses verbatim with their standard/clause/page tags, (b) instructs the model to answer **only** from the provided clauses, (c) instructs it to explicitly say "not covered in the retrieved standards" if the clauses don't answer the question, (d) requests a structured output (plain text answer + which clause IDs it actually used).
**Acceptance criteria:**
- [ ] Prompt is under ~1200 tokens with 3 clauses inserted (keeps you well inside Groq's TPM budget per call).

### 3.2 LLM client abstraction (Groq → Gemini fallback)
**Goal:** `app/core/llm_client.py` exposes one function: `generate_answer(prompt) -> LLMResult(text, provider_used, latency_ms)`. Tries Groq first with `tenacity`-based retry (max 2 attempts, short backoff); on a 429/5xx or timeout, falls through to Gemini (`google-genai` SDK); if both fail, raises a typed `LLMUnavailableError` that the route layer catches (see 3.4 — never a raw 500).
**Acceptance criteria:**
- [ ] Unit test with mocked Groq client raising a 429 confirms the Gemini path is used and the caller can't tell the difference except `provider_used`.
- [ ] Unit test with both providers mocked as failing confirms `LLMUnavailableError` is raised, not an unhandled exception.

### 3.3 Quota-aware caching (this is the sub-phase that answers "make sure AI doesn't do all the work")
**Goal:** `app/core/cache.py` — before any LLM call in `/ask` or `/gap-check`:
1. Exact-match cache: hash the normalized question string → check `diskcache` for a cached `LLMResult`. TTL configurable (default 24h — standards don't change hourly).
2. Semantic near-duplicate cache: embed the incoming question (already computing this for retrieval anyway — reuse it, don't re-embed), compare cosine similarity against cached question embeddings; if similarity ≥ 0.92, reuse that cached answer instead of calling the LLM again.
3. Only call `llm_client.generate_answer` on a full cache miss.
4. A `/api/v1/health/quota` endpoint reports today's call count per provider (simple counter in the cache store) so you can watch it live during rehearsal.
**Acceptance criteria:**
- [ ] Asking the same question twice results in exactly one LLM call (verified via a call-count mock/log).
- [ ] Asking a reworded-but-equivalent question (e.g. "Can I sell this fan?" vs "Is this fan allowed to be sold in India?") hits the semantic cache on the second ask.

### 3.4 `/api/v1/ask` endpoint
**Goal:** wire together 2.3 (retrieve) → 2.4 (confidence) → 3.3 (cache) → 3.2 (generate) → response assembly. If `evidence_found=False`, skip the LLM call entirely and return a templated "not found in retrieved standards" response (saves a call *and* satisfies the "no evidence, no answer" requirement in one place).
**Files:** `app/api/v1/ask.py`, request/response schemas in `app/models/schemas.py`:
```python
class AskRequest(BaseModel):
    question: str

class CitedStandard(BaseModel):
    standard_no: str
    clause_no: str
    page: int
    title: str

class AskResponse(BaseModel):
    answer: str
    evidence_found: bool
    confidence: float
    confidence_label: Literal["high", "medium", "low"]
    citations: list[CitedStandard]
    warnings: list[str]        # populated by Phase 7's status check
    provider_used: Literal["groq", "gemini", "cache", "none"]
    latency_ms: int
```
**Acceptance criteria:**
- [ ] End-to-end test: known-good question returns a correct citation and `evidence_found=True`.
- [ ] Nonsense/out-of-scope question returns `evidence_found=False` and no fabricated citation.

### 3.5 Multi-standard reasoning
**Goal:** in `ask.py`, detect when a question likely needs more than one standard (heuristic: top retrieval results span ≥2 different `standard_no` values with comparable scores, or the question contains multiple product/material nouns mapped in your category table). When detected, retrieve per-standard (using the `standard_filter` from 2.3) for each candidate standard separately, then pass all clause sets together into one prompt (still capped at ~3 clauses per standard, 2 standards max, to control token count) so the LLM synthesizes a combined answer citing both.
**Acceptance criteria:**
- [ ] A hand-crafted compound question spanning 2 of your demo standards returns citations from both in one answer.

### 3.6 Eval harness
**Goal:** extend `tests/golden_qa.json` with expected-answer-contains-keyword checks (not exact string match — LLM phrasing varies) and a latency assertion (<3s on cache hit, <8s on cache miss with Groq).
**Acceptance criteria:**
- [ ] `pytest tests/test_ask.py` passes; report average latency printed to console.

---

## PHASE 4 — (folded into Phase 2/3 above — kept numbering intentionally aligned with the PPT's "Technical Approach" slide; no separate Phase 4 sub-phases needed beyond what's built. Skip to Phase 5.)

---

## PHASE 5 — Compliance Gap Checker

### 5.1 Requirement checklist extraction (offline, one-time, LLM-assisted)
**Goal:** `requirement_extractor.py` — for **each of the 8–12 demo standards only** (not per-query!), make **one** LLM call asking it to extract a structured list of discrete, checkable requirements from that standard's clauses (already chunked/tagged from Phase 1). Cache results permanently to `data/requirements_cache.json` keyed by `standard_no`. This runs during ingestion, never at request time.
**Files:** `app/ingestion/requirement_extractor.py`.
**Acceptance criteria:**
- [ ] Exactly one LLM call per standard, confirmed via log count = number of demo standards.
- [ ] Output is a list of short requirement strings per standard, each traceable back to a `clause_no`.
- [ ] Script is safe to skip if `requirements_cache.json` already has an entry for a standard (idempotent, quota-friendly).

### 5.2 Product → applicable standards mapping
**Goal:** `app/core/gap_checker.py::find_applicable_standards(description) -> list[standard_no]` using the same embedding + keyword approach as retrieval (no new tech needed — reuse `app/core/retrieval.py`), filtered to standard-level (aggregate clause hits by standard, rank by combined score, take top 1–2).
**Acceptance criteria:**
- [ ] Given a demo product description, returns the correct standard(s) with no LLM call involved.

### 5.3 Gap detection (deterministic, no LLM)
**Goal:** compare the product description text against the cached requirement checklist (5.1) for each applicable standard using embedding similarity per requirement item (threshold-based: "matched" if similarity ≥ X, else "missing"). This is the core gap logic and must be fully deterministic/local — no LLM call per gap-check request.
**Acceptance criteria:**
- [ ] For a demo product description you've manually reasoned through, matched vs missing requirements line up with your manual assessment.

### 5.4 Optional gap summary phrasing (cached LLM call)
**Goal:** one *optional* LLM call to turn the matched/missing lists into a friendly one-paragraph summary — routed through the same `llm_client.py` + cache from Phase 3.3 (exact + semantic cache on the product description text), so repeated demo runs of the same product description never re-call the API.
**Acceptance criteria:**
- [ ] Same product description asked twice = one LLM call, same as 3.3's test pattern.

### 5.5 `/api/v1/gap-check` endpoint
**Files:** `app/api/v1/gap_check.py`, schemas:
```python
class GapCheckRequest(BaseModel):
    product_description: str

class GapCheckResponse(BaseModel):
    applicable_standards: list[str]
    matched_requirements: list[str]
    missing_requirements: list[str]
    summary: str
    confidence: float
```
**Acceptance criteria:**
- [ ] End-to-end call on a demo product returns a non-empty `missing_requirements` list for at least one deliberately-incomplete test description.

---

## PHASE 6 — Standards Relationship Graph

### 6.1 Relationship extraction (offline)
**Goal:** `relationship_extractor.py` — regex pass over each document's foreword/scope text for patterns like "supersedes IS \d+", "this standard is based on", "reference is made to IS \d+" → candidate edges. For the small demo corpus, hand-verify and hand-correct the extracted edges (store corrections directly in the output — a curated-but-tool-assisted graph is the right scope here, and honest to say so if a judge asks).
**Acceptance criteria:**
- [ ] Every demo standard has at least category-membership edges; supersession/reference edges present wherever they genuinely exist in your chosen documents.

### 6.2 NetworkX graph construction & persistence
**Goal:** `app/core/graph_engine.py::build_graph()` builds a `networkx.DiGraph`, node = standard (attrs: title, status, category), edge = relation type (`supersedes`, `references`, `same_category`). Persist as `data/graph.json` (node-link format) so the API never rebuilds it per-request — load once at startup like the embedding model.
**Acceptance criteria:**
- [ ] `graph_engine.load_graph()` at startup logs node/edge counts once; subsequent calls reuse the in-memory graph.

### 6.3 Subgraph query
**Goal:** `get_subgraph(standard_no, depth=1) -> {nodes, edges}` — BFS from the given node up to `depth` hops, returned in a shape `react-force-graph` consumes directly (`{id, label, status}` nodes / `{source, target, relation}` edges).
**Acceptance criteria:**
- [ ] Querying a standard with known relationships returns exactly the expected neighbor set.

### 6.4 `/api/v1/graph/{standard_no}` and `/api/v1/graph/full` endpoints
**Files:** `app/api/v1/graph.py`.
**Acceptance criteria:**
- [ ] Both endpoints return valid JSON matching the schema above; `/full` is capped/paginated if the demo corpus is small enough it doesn't matter yet, but the cap logic should exist for honesty toward "scalable" claims on slide 4.

---

## PHASE 7 — Amendment & Withdrawal Tracking

### 7.1 Status schema (already created in 1.4 registry — this sub-phase wires it into the app layer)
**Goal:** `app/core/status_tracker.py::get_status(standard_no) -> StatusInfo(status, superseded_by, last_amended_date)` reading from `registry.db`.
**Acceptance criteria:**
- [ ] Returns correct curated data for every demo standard.

### 7.2 Inject warnings into `/ask` responses
**Goal:** modify `ask.py` (from Phase 3.4) — after assembling citations, check each cited standard's status via 7.1; if `status != "active"`, append a warning string to `AskResponse.warnings`, e.g. `"IS xxxx:20xx has been superseded by IS yyyy:20yy — verify before relying on this clause."`
**Acceptance criteria:**
- [ ] A demo question that cites a deliberately-marked "superseded" standard returns a non-empty `warnings` list.

### 7.3 `/api/v1/standards/{standard_no}/status` endpoint
**Files:** `app/api/v1/standards.py` (status route only in this sub-phase — search route is 8.1, keep them in the same file but build incrementally).
**Acceptance criteria:**
- [ ] Endpoint returns the schema above for every demo standard, 404 for unknown ones.

---

## PHASE 8 — Standard Search

### 8.1 Keyword + semantic combined search
**Goal:** add SQLite FTS5 virtual table over `registry.db`'s `title`/`category` columns for fast keyword search; combine with a lightweight semantic pass over standard *titles* (not full clauses — this is standard-level search, distinct from clause-level `/ask` retrieval) for fuzzy matches like "fan safety" → "IS 374 ceiling fans."
**Files:** `app/api/v1/standards.py` (`/search` route), `app/models/schemas.py` (`SearchResult`).
**Acceptance criteria:**
- [ ] Exact standard-number search (`"IS 374"`) returns that standard first.
- [ ] Fuzzy product-term search returns a relevant standard even without an exact keyword match.

### 8.2 Autocomplete/suggestions (optional, small)
**Goal:** `/api/v1/standards/suggest?q=` returns top-5 title matches for a frontend typeahead.
**Acceptance criteria:**
- [ ] Sub-100ms response on the demo corpus (it's tiny — this should be trivial; if it isn't, something's wrong).

---

## PHASE 9 — API Hardening & Integration Contract

### 9.1 Unified response envelope & OpenAPI polish
**Goal:** ensure every route has explicit `response_model`, meaningful `summary`/`description` for Swagger, and consistent error shape (`{"error": str, "detail": str}`) via a FastAPI exception handler — this becomes the literal reference doc you hand to Claude for frontend integration.
**Acceptance criteria:**
- [ ] `/docs` is a clean, complete contract with example request/response for every endpoint.

### 9.2 CORS + basic abuse protection
**Goal:** restrict CORS to your actual frontend origin(s) for deployment (leave permissive in local dev via env flag), add a simple per-IP request throttle (`slowapi` or hand-rolled) on `/ask` and `/gap-check` specifically — these are your expensive/LLM-touching routes, not the cheap ones.
**Acceptance criteria:**
- [ ] Hammering `/ask` past the configured limit returns `429` with a clear message, not a crash.

### 9.3 Structured error handling middleware
**Goal:** global exception handler catches `LLMUnavailableError` (from 3.2) → `503` with a friendly message; catches validation errors → `422` with field-level detail; catches everything else → `500` logged with a request ID for debugging, never leaking a stack trace to the client.
**Acceptance criteria:**
- [ ] Deliberately trigger each error type in a test and confirm the right status code + shape.

### 9.4 API versioning confirmation
**Goal:** confirm every route lives under `/api/v1/` (should already be true if you followed §4) — this sub-phase is really just a review + a `tests/test_api_contract.py` that walks the OpenAPI schema and asserts every path starts with `/api/v1/`.

### 9.5 Frontend integration contract doc
**Goal:** generate `FRONTEND_CONTRACT.md` (separate file, auto-summarized from the OpenAPI schema) listing every endpoint, method, request shape, response shape, and one real example each — this is what you'll hand to Claude when building the frontend, so it never has to guess your API shape.
**Acceptance criteria:**
- [ ] Doc covers all 8 endpoints (`ask`, `gap-check`, `graph/{id}`, `graph/full`, `standards/search`, `standards/suggest`, `standards/{id}/status`, `health`).

---

## PHASE 10 — Performance, QA & Demo Readiness

### 10.1 Response caching sanity pass
**Goal:** confirm 3.3's cache is actually wired into both `/ask` and `/gap-check` (not just `/ask`), add cache hit-rate logging.
**Acceptance criteria:**
- [ ] Log line on every request shows `cache_hit: true/false`.

### 10.2 Load/latency check
**Goal:** simple `scripts/`-level async script firing 20 concurrent requests at `/ask` (mix of cached and novel questions), report p50/p95 latency.
**Acceptance criteria:**
- [ ] p95 latency on cache hits is well under 1s; cache misses are dominated by LLM round-trip, not your own code.

### 10.3 Full pytest suite
**Goal:** run everything from tests/ together; this is the final regression gate before touching deployment config.
**Acceptance criteria:**
- [ ] `pytest` — 100% pass, zero skipped-without-reason.

### 10.4 Demo dataset seeding
**Goal:** `scripts/seed_demo_dataset.py` runs the entire ingestion pipeline (Phase 1) end-to-end on the final curated 8–12 PDFs in one command, so the whole backend can be rebuilt from scratch on a clean machine (or Render) reliably.
**Acceptance criteria:**
- [ ] Fresh clone + `.env` + one script call = fully working `/ask` within a few minutes.

### 10.5 Deployment
**Goal:** `render.yaml`, environment variable list documented in `.env.example`, `README.md` with setup steps for a teammate or judge.
**Acceptance criteria:**
- [ ] Deployed Render URL responds to `/api/v1/health`.
- [ ] Deployed instance can serve `/ask` against the pre-built `chroma_store`/`registry.db` (commit these as build artifacts or a startup download step — decide based on Render's free-tier disk limits and document the choice in the README).

---

## PHASE 11 — Optional Stretch (only if time remains, in this priority order)

1. **Reranker** — add `bge-reranker-base` as a second pass over top-10 retrieved chunks before picking the final top-3; improves precision, costs a bit of local compute, zero API quota.
2. **Streaming answers** — Server-Sent Events on `/ask` so the frontend can show token-by-token output (nice demo polish, not judged criteria — do this last).
3. **Query analytics log** — anonymized log of asked questions + confidence, useful to show judges "here's how we'd keep improving retrieval."
4. **Hindi support** — BGE-M3 is already multilingual; this is a config/prompt change more than new engineering, good low-effort wow-factor if there's spare time.

Do not start Phase 11 before Phase 10 is fully green.

---

## 12. AI Quota & Cost Strategy — Summary Table

| LLM call site | Frequency | Cached? | Notes |
|---|---|---|---|
| Requirement extraction (5.1) | Once per standard, offline | Permanent | ~8–12 calls total, ever |
| Relationship extraction (6.1) | Once per standard, offline, regex-first | Permanent | LLM only for ambiguous cases, if at all |
| `/ask` answer generation (3.2–3.4) | Per unique question | Exact + semantic (0.92 cosine) | Skipped entirely if `evidence_found=False` |
| `/gap-check` summary (5.4) | Per unique product description | Exact + semantic | Core gap logic (5.3) never calls the LLM |
| Fallback chain | Groq → Gemini → deterministic template | — | System stays functional at **zero** quota remaining |

**Before recording the demo video:** switch `GEMINI_API_KEY` in `.env` (via `scripts/switch_provider_key.sh`, no code changes needed — this is exactly why 3.2 routes everything through one client), then run `scripts/warm_cache.py` with your exact rehearsed question list so every question you ask on camera is a guaranteed instant cache hit. Keep the live/uncached path working too, since judges will ask follow-up questions off-script during Q&A — that's what the fallback chain and confidence handling protect you against.

---

## 13. Risk Register (mirrors PPT slide 4 — keep answers ready for judges)

| Risk | Mitigation already built in |
|---|---|
| Correct standard hard to identify among related ones | Hybrid retrieval (2.3) + multi-standard reasoning (3.5) |
| Dense/complex clauses mis-parsed | Manual spot-check gate in 1.3, `needs_review` flag instead of silent failure |
| LLM hallucination | Grounded prompt (3.1) + confidence floor (2.4) + "no evidence, no answer" (3.4) |
| Standards get revised/withdrawn | Status registry (1.4/7.1) + automatic warnings injected into answers (7.2) |
| Free-tier rate limits during demo | Provider fallback (3.2) + caching (3.3) + pre-warmed cache before recording (§12) |
| Data access/usage restrictions | Curated free-source demo corpus only (§5), documented, no scraping |

---

## 14. Master Context Block (paste this into ChatGPT before every sub-phase prompt)

```
PROJECT: Standardify — AI assistant for Indian Standards (BIS), SIH26107, Team Trailblazers.
STACK: FastAPI + Uvicorn + Pydantic v2, PyMuPDF/pdfplumber/pytesseract, BGE-M3 (FlagEmbedding, local),
ChromaDB (persistent, local), LlamaIndex, Groq (primary LLM) + Gemini via google-genai SDK (fallback),
NetworkX (graph), SQLite (registry + FTS5 search), diskcache (caching).

LOCKED REPO STRUCTURE (never restructure, only add/edit within named paths):
<paste §4 tree here>

GOLDEN RULES (enforce strictly):
<paste §2 here>

CURRENT STATE: <paste your actual current file tree + a one-line status of what's built so far>

TASK: Implement ONLY sub-phase <X.Y — name> as specified below. Do not modify any file not explicitly
named in this sub-phase. Do not add features from other sub-phases even if they seem related. After
implementing, list every file you created or modified, and confirm the Acceptance Criteria are met.

<paste the specific sub-phase section from this document here>
```

Ask ChatGPT: *"Turn this into a precise, unambiguous prompt for my coding agent — keep every constraint, add nothing new, and make the acceptance criteria explicit instructions the agent must self-check before declaring the task done."* That output is what you paste into Antigravity.

---

## 15. Definition of "Done" for the whole backend

- [ ] All 8 endpoints in §9.5's contract respond correctly against the seeded demo dataset.
- [ ] `pytest` fully green.
- [ ] `/ask` demonstrably refuses to answer out-of-scope questions.
- [ ] `/ask` demonstrably shows a warning for a superseded standard.
- [ ] `/gap-check` demonstrably lists at least one missing requirement on a deliberately incomplete product description.
- [ ] `/graph/{id}` returns a non-trivial subgraph for at least one standard with real relationships.
- [ ] Cache hit-rate log shows repeated demo questions cost zero additional LLM calls.
- [ ] Deployed Render URL is reachable and serves the same behavior as local.
- [ ] `FRONTEND_CONTRACT.md` exists and is accurate — hand this to Claude next for frontend integration.

Good luck — build it phase by phase, don't let the agent skip ahead, and you'll have something judges genuinely can't dismiss as "just another chatbot wrapper."
