import axios from 'axios'

/**
 * Single Axios instance for the whole app.
 *
 * Per FRONTEND_CONTRACT.md §1/§4, the base URL includes the `/api/v1`
 * prefix — endpoint functions in endpoints.js call relative paths like
 * `/ask`, not `/api/v1/ask`.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 20000, // /ask can take a few seconds on a cache miss (LLM round-trip)
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

/**
 * @typedef {Object} NormalizedApiError
 * @property {number|null} status
 * @property {string} message      human-readable, safe to show in a toast
 * @property {string} kind         "network" | "timeout" | "rate_limited" |
 *                                 "unavailable" | "validation" | "not_found" | "server" | "unknown"
 * @property {string} [detail]     raw backend detail, if present
 * @property {string} [requestId]  FRONTEND_CONTRACT.md §1's X-Request-ID / body request_id, for support reference
 */

/**
 * @param {unknown} error
 * @returns {NormalizedApiError}
 */
export function normalizeApiError(error) {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED') {
      return { status: null, kind: 'timeout', message: 'That took too long to answer. Please try again.' }
    }
    if (!error.response) {
      return {
        status: null,
        kind: 'network',
        message: "Couldn't reach Standardify. Check your connection or try again shortly.",
      }
    }

    const status = error.response.status
    /** @type {import('./types').ApiErrorBody | undefined} */
    const body = error.response.data
    const detail = typeof body?.detail === 'string' ? body.detail : undefined
    const requestId = body?.request_id || error.response.headers?.['x-request-id']
    const errorCode = body?.error

    // Prefer the backend's named error code where it disambiguates better
    // than the raw HTTP status alone (per FRONTEND_CONTRACT.md §1).
    if (errorCode === 'llm_unavailable' || status === 503) {
      return { status, kind: 'unavailable', message: 'The assistant is temporarily unavailable. Please try again shortly.', detail, requestId }
    }
    if (errorCode === 'rate_limit_exceeded' || status === 429) {
      return { status, kind: 'rate_limited', message: "You've hit the rate limit — please wait a moment and try again.", detail, requestId }
    }
    if (errorCode === 'validation_error' || status === 422) {
      return { status, kind: 'validation', message: detail || "That input doesn't look right — please check it and try again.", detail, requestId }
    }
    if (status === 404) {
      return { status, kind: 'not_found', message: detail || "That standard wasn't found in the BIS registry.", detail, requestId }
    }
    if (status >= 500) {
      return { status, kind: 'server', message: 'Something went wrong on our end. Please try again.', detail, requestId }
    }
    return { status, kind: 'unknown', message: detail || 'Something unexpected happened.', detail, requestId }
  }

  return { status: null, kind: 'unknown', message: 'Something unexpected happened.' }
}
