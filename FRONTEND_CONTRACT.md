# Standardify — Frontend Integration Contract (API v1)
**Team Trailblazers · SIH26107 · AI-Powered Intelligent Assistant for Indian Standards (BIS)**

This document defines the formal, verified integration contract between the Standardify backend and frontend clients (React/Vite/Next.js/Axios). All schemas, parameters, response models, and error behaviors match the live FastAPI OpenAPI schema generated at `/openapi.json`.

---

## 1. Global API Standards

- **Base URL**: `http://localhost:8000/api/v1` (Production: configure via `VITE_API_BASE_URL` or `NEXT_PUBLIC_API_URL`)
- **Headers**:
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `X-Request-ID`: *(Optional in request, always returned in response)* Correlation UUID for telemetry and logging.
- **Authentication**: None required for demo (open / permissive CORS in local dev; restricted in prod).
- **Interactive OpenAPI Documentation**:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

### Standardized Error Envelope (`ErrorResponse`)
All non-2xx responses conform to this consistent envelope:
```json
{
  "error": "validation_error | rate_limit_exceeded | llm_unavailable | http_error | internal_server_error",
  "detail": "Human-readable error explanation or array of field validation objects",
  "request_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
}
```

---

## 2. Endpoint Index

| Feature | Method | Path | Summary |
|---|---|---|---|
| **Grounded Q&A** | `POST` | `/api/v1/ask` | Ask questions grounded in Indian Standards with clause citations |
| **Compliance Gap Checker** | `POST` | `/api/v1/gap-check` | Analyze product description for matched & missing requirements |
| **Standards Subgraph** | `GET` | `/api/v1/graph/{standard_no}` | Get N-hop relationship network for a specific standard |
| **Full Standards Graph** | `GET` | `/api/v1/graph/full` | Get full inter-standard relationship network (paginated) |
| **Standard Search** | `GET` | `/api/v1/standards/search` | Search standards via number, FTS5 keywords, and semantic title similarity |
| **Autocomplete / Suggest** | `GET` | `/api/v1/standards/suggest` | Fast prefix title autocomplete for search bars (<100ms) |
| **Lifecycle Status** | `GET` | `/api/v1/standards/{standard_no}/status` | Check if standard is Active, Superseded, Withdrawn, or Amended |
| **Liveness Health** | `GET` | `/api/v1/health` | Service liveness and readiness probe |
| **Quota Telemetry** | `GET` | `/api/v1/health/quota` | Daily LLM provider API call counters and cache metrics |

---

## 3. Detailed Endpoint Contracts

### 3.1 Grounded Q&A — `POST /api/v1/ask`

Ask natural language questions about BIS standards. Answers are strictly grounded in retrieved clauses. If no evidence is found, the system deterministic skips LLM inference.

- **URL**: `/api/v1/ask`
- **Method**: `POST`
- **Rate Limit**: 60 requests / minute per client IP (`429` on burst).
- **Request Body** (`AskRequest`):
  ```json
  {
    "question": "What is the drop test height for plastic packaged drinking water bottles?"
  }
  ```
- **Response Schema** (`AskResponse`):
  ```typescript
  interface CitedStandard {
    standard_no: string;      // e.g. "IS 9001:2025"
    clause_no: string;        // e.g. "5.2"
    page: number;             // e.g. 4
    title: string;            // e.g. "Drop Impact and Pressure Test"
  }

  interface AskResponse {
    answer: string;           // Grounded plain-language answer
    evidence_found: boolean;  // True if sufficient evidence was found in retrieved standards
    confidence: number;       // Normalized score [0.0 - 1.0]
    confidence_label: "high" | "medium" | "low";
    citations: CitedStandard[];
    warnings: string[];       // Advisory warnings (e.g. if a cited standard is superseded)
    provider_used: "groq" | "gemini" | "cache" | "none";
    latency_ms: number;       // Total processing time in ms
  }
  ```
- **Example Response**:
  ```json
  {
    "answer": "Filled plastic bottle containers for packaged drinking water must withstand a free-fall drop test from a height of 1.2 meters onto a flat concrete surface without rupture or leakage.",
    "evidence_found": true,
    "confidence": 0.88,
    "confidence_label": "high",
    "citations": [
      {
        "standard_no": "IS 9001:2025",
        "clause_no": "5.2",
        "page": 4,
        "title": "Drop Impact and Pressure Test"
      }
    ],
    "warnings": [],
    "provider_used": "groq",
    "latency_ms": 342
  }
  ```

---

### 3.2 Compliance Gap Checker — `POST /api/v1/gap-check`

Determines applicable Indian Standards for a product description, performs local deterministic requirement matching via BGE-M3 embeddings, and generates an executive summary.

- **URL**: `/api/v1/gap-check`
- **Method**: `POST`
- **Rate Limit**: 60 requests / minute per client IP.
- **Request Body** (`GapCheckRequest`):
  ```json
  {
    "product_description": "We manufacture 1-liter plastic drinking water bottles from virgin food-grade PET polymer."
  }
  ```
- **Response Schema** (`GapCheckResponse`):
  ```typescript
  interface GapCheckResponse {
    applicable_standards: string[];   // e.g. ["IS 9001:2025"]
    matched_requirements: string[];   // Traceable satisfied items
    missing_requirements: string[];   // Unaddressed/unverified items
    summary: string;                  // Executive compliance summary
    confidence: number;               // Standard retrieval match score [0.0 - 1.0]
  }
  ```
- **Example Response**:
  ```json
  {
    "applicable_standards": [
      "IS 9001:2025"
    ],
    "matched_requirements": [
      "[IS 9001:2025 Clause 4.1] Plastic containers shall be made from virgin food grade polymers; recycled plastics are strictly prohibited."
    ],
    "missing_requirements": [
      "[IS 9001:2025 Clause 5.2] Filled bottle containers shall withstand a free-fall drop test from 1.2 m height onto a flat concrete surface without rupture or leakage.",
      "[IS 9001:2025 Clause 5.2] Containers must withstand and maintain a hydrostatic pressure of 200 kPa for 5 minutes without leakage or deformation."
    ],
    "summary": "The product satisfies material specifications under IS 9001:2025 by utilizing virgin food-grade polymer. However, physical drop impact testing (1.2m) and internal hydrostatic pressure validation (200 kPa) remain missing from the specification and require laboratory certification.",
    "confidence": 0.85
  }
  ```

---

### 3.3 Standards Relationship Subgraph — `GET /api/v1/graph/{standard_no}`

Extracts an N-hop neighborhood graph centered around a given standard in `react-force-graph` node-link format.

- **URL**: `/api/v1/graph/{standard_no}`
- **Method**: `GET`
- **Path Parameters**:
  - `standard_no` (string, required): e.g. `IS 374:2019` or `IS 9001:2025`
- **Query Parameters**:
  - `depth` (integer, optional, default: `1`, min: `1`, max: `3`): BFS exploration depth
- **Response Schema** (`GraphResponse`):
  ```typescript
  interface GraphNode {
    id: string;             // Standard number (e.g. "IS 374:2019")
    label: string;          // Human-readable title
    status: string;         // "Active" | "Superseded" | "Withdrawn"
    category?: string;      // Category tag
  }

  interface GraphEdge {
    source: string;         // Source node id
    target: string;         // Target node id
    relation: string;       // "supersedes" | "references" | "same_category"
  }

  interface GraphResponse {
    nodes: GraphNode[];
    edges: GraphEdge[];
    total_nodes?: number;
    total_edges?: number;
  }
  ```
- **Example Response**:
  ```json
  {
    "nodes": [
      {
        "id": "IS 374:2019",
        "label": "Electric Ceiling Fans",
        "status": "Active",
        "category": "Electrical & Electronics"
      },
      {
        "id": "IS 374:1979",
        "label": "Electric Ceiling Fans (1979 Edition)",
        "status": "Superseded",
        "category": "Electrical & Electronics"
      },
      {
        "id": "IS 1293:2019",
        "label": "Plugs and Socket-Outlets",
        "status": "Active",
        "category": "Electrical & Electronics"
      }
    ],
    "edges": [
      {
        "source": "IS 374:2019",
        "target": "IS 374:1979",
        "relation": "supersedes"
      },
      {
        "source": "IS 374:2019",
        "target": "IS 1293:2019",
        "relation": "references"
      }
    ],
    "total_nodes": 3,
    "total_edges": 2
  }
  ```

---

### 3.4 Full Standards Graph — `GET /api/v1/graph/full`

Retrieves the entire network of indexed standards and relationships with pagination support.

- **URL**: `/api/v1/graph/full`
- **Method**: `GET`
- **Query Parameters**:
  - `limit` (integer, default: `100`, max: `500`)
  - `offset` (integer, default: `0`)
- **Response Schema**: `GraphResponse` (same as 3.3).

---

### 3.5 Standard Search — `GET /api/v1/standards/search`

Hybrid search over standard numbers, SQLite FTS5 titles/categories, and semantic title embeddings.

- **URL**: `/api/v1/standards/search`
- **Method**: `GET`
- **Query Parameters**:
  - `q` (string, required): Standard number, product name, or keyword (e.g. `IS 374`, `fan safety`, `packaging`)
- **Response Schema** (`SearchResponse`):
  ```typescript
  interface SearchResult {
    standard_no: string;
    title: string;
    category?: string;
    status: string;
    relevance_score: number;  // [0.0 - 1.0]
  }

  interface SearchResponse {
    query: string;
    total_results: number;
    results: SearchResult[];
  }
  ```
- **Example Response**:
  ```json
  {
    "query": "IS 374",
    "total_results": 2,
    "results": [
      {
        "standard_no": "IS 374:2019",
        "title": "Electric Ceiling Fans - Specification",
        "category": "Electrical & Electronics",
        "status": "Active",
        "relevance_score": 1.0
      },
      {
        "standard_no": "IS 374:1979",
        "title": "Electric Ceiling Fans (1979 Edition)",
        "category": "Electrical & Electronics",
        "status": "Superseded",
        "relevance_score": 0.95
      }
    ]
  }
  ```

---

### 3.6 Autocomplete / Suggestions — `GET /api/v1/standards/suggest`

Ultra-fast title and standard number prefix search for frontend search bar dropdowns (<100ms).

- **URL**: `/api/v1/standards/suggest`
- **Method**: `GET`
- **Query Parameters**:
  - `q` (string, required): Prefix term (e.g. `IS 900`, `fan`, `toy`)
- **Response Schema** (`SuggestResponse`):
  ```typescript
  interface SuggestItem {
    standard_no: string;
    title: string;
  }

  interface SuggestResponse {
    query: string;
    suggestions: SuggestItem[]; // Max 5 items
  }
  ```
- **Example Response**:
  ```json
  {
    "query": "fan",
    "suggestions": [
      {
        "standard_no": "IS 374:2019",
        "title": "Electric Ceiling Fans - Specification"
      }
    ]
  }
  ```

---

### 3.7 Lifecycle Status Tracker — `GET /api/v1/standards/{standard_no}/status`

Retrieves official lifecycle, amendment date, and supersession records for any BIS standard.

- **URL**: `/api/v1/standards/{standard_no}/status`
- **Method**: `GET`
- **Path Parameters**:
  - `standard_no` (string, required): e.g. `IS 1293:2005` or `IS 374:2019`
- **Response Schema** (`StatusResponse`):
  ```typescript
  interface StatusResponse {
    standard_no: string;
    status: "Active" | "Superseded" | "Withdrawn" | "Under Revision";
    superseded_by?: string | null;      // Successor standard number
    last_amended_date?: string | null;  // ISO date string e.g. "2024-06-15"
  }
  ```
- **Status Codes**:
  - `200 OK`: Status found
  - `404 Not Found`: Standard not in BIS registry

---

### 3.8 Health & Telemetry Endpoints

- **`GET /api/v1/health`**:
  ```json
  {
    "status": "ok"
  }
  ```
- **`GET /api/v1/health/quota`**:
  ```json
  {
    "status": "ok",
    "groq_calls_today": 12,
    "gemini_calls_today": 1,
    "cache_hits_today": 48
  }
  ```

---

## 4. Frontend Axios Client Example

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Grounded Q&A
export const askStandardQuestion = async (question: string) => {
  const { data } = await api.post('/ask', { question });
  return data;
};

// Compliance Gap Checker
export const checkProductGaps = async (product_description: string) => {
  const { data } = await api.post('/gap-check', { product_description });
  return data;
};

// Autocomplete Suggestions
export const getStandardSuggestions = async (q: string) => {
  const { data } = await api.get('/standards/suggest', { params: { q } });
  return data.suggestions;
};

// Subgraph for Visualization
export const getStandardSubgraph = async (standard_no: string, depth = 1) => {
  const { data } = await api.get(`/graph/${encodeURIComponent(standard_no)}`, { params: { depth } });
  return data;
};
```
