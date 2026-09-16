/**
 * Standardify — Axios API client.
 *
 * All API calls in the frontend go through this module.
 * The baseURL automatically proxies to the FastAPI backend
 * in development (via vite.config.js proxy) and uses the
 * production URL in deployment (set via VITE_API_URL env var).
 *
 * Phase 0 stub: client configured, endpoints added per-phase.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

export default api
