import { apiClient } from './client'

/**
 * One function per backend endpoint, matching FRONTEND_CONTRACT.md's 9
 * routes exactly. Paths are relative to apiClient's baseURL, which already
 * includes `/api/v1` — do not prefix these paths with it again.
 */

/** @returns {Promise<{status: string}>} */
export function getHealth() {
  return apiClient.get('/health').then((r) => r.data)
}

/** @returns {Promise<import('./types').QuotaInfo>} */
export function getHealthQuota() {
  return apiClient.get('/health/quota').then((r) => r.data)
}

/**
 * @param {string} question
 * @returns {Promise<import('./types').AskResponse>}
 */
export function askQuestion(question) {
  return apiClient
    .post('/ask', /** @type {import('./types').AskRequest} */ ({ question }))
    .then((r) => r.data)
}

/**
 * @param {string} productDescription
 * @returns {Promise<import('./types').GapCheckResponse>}
 */
export function checkGap(productDescription) {
  return apiClient
    .post('/gap-check', /** @type {import('./types').GapCheckRequest} */ ({
      product_description: productDescription,
    }))
    .then((r) => r.data)
}

/**
 * N-hop relationship subgraph centered on one standard.
 * @param {string} standardNo
 * @param {number} [depth=1]  1-3 per FRONTEND_CONTRACT.md §3.3
 * @param {import('axios').AxiosRequestConfig} [options]
 * @returns {Promise<import('./types').GraphResponse>}
 */
export function getGraphForStandard(standardNo, depth = 1, options = {}) {
  return apiClient
    .get(`/graph/${encodeURIComponent(standardNo)}`, { params: { depth }, ...options })
    .then((r) => r.data)
}

/**
 * @param {{ limit?: number, offset?: number }} [pagination]
 * @param {import('axios').AxiosRequestConfig} [options]
 * @returns {Promise<import('./types').GraphResponse>}
 */
export function getFullGraph({ limit = 100, offset = 0 } = {}, options = {}) {
  return apiClient.get('/graph/full', { params: { limit, offset }, ...options }).then((r) => r.data)
}


/**
 * @param {string} query
 * @param {import('axios').AxiosRequestConfig} [options]
 * @returns {Promise<import('./types').SearchResponse>}
 */
export function searchStandards(query, options = {}) {
  return apiClient.get('/standards/search', { params: { q: query }, ...options }).then((r) => r.data)
}

/**
 * @param {string} query
 * @param {import('axios').AxiosRequestConfig} [options]
 * @returns {Promise<import('./types').SuggestResponse>}
 */
export function suggestStandards(query, options = {}) {
  return apiClient.get('/standards/suggest', { params: { q: query }, ...options }).then((r) => r.data)
}


/**
 * @param {string} standardNo
 * @returns {Promise<import('./types').StatusResponse>}
 */
export function getStandardStatus(standardNo) {
  return apiClient.get(`/standards/${encodeURIComponent(standardNo)}/status`).then((r) => r.data)
}
