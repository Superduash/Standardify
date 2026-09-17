/**
 * Shared type definitions (JSDoc, not TypeScript — matches the rest of the
 * project's plain-JS stack) mirroring FRONTEND_CONTRACT.md exactly — the
 * verified contract generated from the live FastAPI OpenAPI schema.
 *
 * FRONTEND_CONTRACT.md is authoritative. This file is the ONLY file that
 * should need to change if the contract is revised (see frontendplan.md §0).
 */

/**
 * @typedef {Object} AskRequest
 * @property {string} question
 */

/**
 * @typedef {Object} CitedStandard
 * @property {string} standard_no   e.g. "IS 9001:2025"
 * @property {string} clause_no     e.g. "5.2"
 * @property {number} page
 * @property {string} title
 */

/** @typedef {"high"|"medium"|"low"} ConfidenceLabel */
/** @typedef {"groq"|"gemini"|"cache"|"none"} ProviderUsed */

/**
 * @typedef {Object} AskResponse
 * @property {string} answer
 * @property {boolean} evidence_found
 * @property {number} confidence            0.0-1.0
 * @property {ConfidenceLabel} confidence_label
 * @property {CitedStandard[]} citations
 * @property {string[]} warnings            e.g. "cited standard is superseded"
 * @property {ProviderUsed} provider_used
 * @property {number} latency_ms
 */

/**
 * @typedef {Object} GapCheckRequest
 * @property {string} product_description
 */

/**
 * @typedef {Object} GapCheckResponse
 * @property {string[]} applicable_standards
 * @property {string[]} matched_requirements     pre-formatted, e.g. "[IS 9001:2025 Clause 4.1] ..."
 * @property {string[]} missing_requirements     pre-formatted, same style
 * @property {string} summary
 * @property {number} confidence                 0.0-1.0
 */

/**
 * Standard lifecycle status, exactly as returned by the backend — Title
 * Case, four possible values. NOT the same vocabulary the frontend
 * originally guessed (lowercase "active"/"revised"/"withdrawn"); this was
 * corrected against FRONTEND_CONTRACT.md.
 * @typedef {"Active"|"Superseded"|"Withdrawn"|"Under Revision"} StandardStatus
 */

/**
 * @typedef {Object} GraphNode
 * @property {string} id            standard number, e.g. "IS 374:2019"
 * @property {string} label
 * @property {StandardStatus} status
 * @property {string} [category]
 */

/**
 * @typedef {Object} GraphEdge
 * @property {string} source
 * @property {string} target
 * @property {"supersedes"|"references"|"same_category"} relation
 */

/**
 * @typedef {Object} GraphResponse
 * @property {GraphNode[]} nodes
 * @property {GraphEdge[]} edges
 * @property {number} [total_nodes]
 * @property {number} [total_edges]
 */

/**
 * @typedef {Object} SearchResult
 * @property {string} standard_no
 * @property {string} title
 * @property {string} [category]
 * @property {StandardStatus} status
 * @property {number} relevance_score   0.0-1.0
 */

/**
 * @typedef {Object} SearchResponse
 * @property {string} query
 * @property {number} total_results
 * @property {SearchResult[]} results
 */

/**
 * @typedef {Object} SuggestItem
 * @property {string} standard_no
 * @property {string} title
 */

/**
 * @typedef {Object} SuggestResponse
 * @property {string} query
 * @property {SuggestItem[]} suggestions   max 5 items, per contract
 */

/**
 * @typedef {Object} StatusResponse
 * @property {string} standard_no
 * @property {StandardStatus} status
 * @property {string|null} [superseded_by]
 * @property {string|null} [last_amended_date]   ISO date string
 */

/**
 * @typedef {Object} QuotaInfo
 * @property {string} status
 * @property {number} groq_calls_today
 * @property {number} gemini_calls_today
 * @property {number} cache_hits_today
 */

/**
 * Error envelope per FRONTEND_CONTRACT.md §1 — every non-2xx response.
 * @typedef {"validation_error"|"rate_limit_exceeded"|"llm_unavailable"|"http_error"|"internal_server_error"} ApiErrorCode
 * @typedef {Object} ApiErrorBody
 * @property {ApiErrorCode|string} error
 * @property {string} detail
 * @property {string} [request_id]
 */

export {}
