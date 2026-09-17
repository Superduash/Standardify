import { useEffect, useState } from 'react'
import { getHealth, getHealthQuota } from '../../api/endpoints'
import { normalizeApiError } from '../../api/client'

/**
 * QuotaDebugPanel — Phase 10 team/demo diagnostics panel.
 *
 * ONLY rendered when VITE_SHOW_DEBUG_PANEL === "true".
 * Never visible in normal production builds.
 *
 * Displays:
 *   - /health liveness status
 *   - /health/quota daily API call counters and cache hit stats
 */

const SHOW = import.meta.env.VITE_SHOW_DEBUG_PANEL === 'true'

const REFRESH_INTERVAL_MS = 30_000

/**
 * A small draggable corner panel; does not depend on or affect any app state.
 */
function Panel() {
  const [health, setHealth] = useState(/** @type {string|null} */ (null))
  const [quota, setQuota] = useState(/** @type {import('../../api/types').QuotaInfo|null} */ (null))
  const [error, setError] = useState(/** @type {string|null} */ (null))
  const [loading, setLoading] = useState(true)
  const [minimised, setMinimised] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  const fetch = async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, q] = await Promise.all([getHealth(), getHealthQuota()])
      setHealth(h?.status ?? 'unknown')
      setQuota(q)
    } catch (err) {
      setError(normalizeApiError(err).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, REFRESH_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])

  if (dismissed) return null

  return (
    <div
      className="fixed bottom-4 left-4 z-[9999] flex flex-col rounded-xl border border-border bg-surface shadow-xl text-xs font-mono"
      style={{ minWidth: '210px', maxWidth: '260px' }}
      role="complementary"
      aria-label="Developer diagnostic panel"
    >
      {/* Title Bar */}
      <div className="flex items-center justify-between gap-2 rounded-t-xl border-b border-border bg-bg px-3 py-2">
        <span className="font-sans text-[11px] font-semibold uppercase tracking-widest text-text-muted">
          Debug Panel
        </span>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setMinimised((v) => !v)}
            className="rounded px-1.5 py-0.5 text-text-muted hover:bg-border hover:text-text"
            aria-label={minimised ? 'Expand debug panel' : 'Minimise debug panel'}
          >
            {minimised ? '+' : '−'}
          </button>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            className="rounded px-1.5 py-0.5 text-text-muted hover:bg-danger/10 hover:text-danger"
            aria-label="Dismiss debug panel"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Body */}
      {!minimised && (
        <div className="space-y-2 p-3">
          {/* Health */}
          <Row
            label="Health"
            value={
              loading ? '…' : error ? 'err' : health === 'ok' ? '✓ ok' : health ?? '?'
            }
            ok={!loading && !error && health === 'ok'}
          />

          {/* Quota */}
          {quota && (
            <>
              <Row label="Groq calls" value={quota.groq_calls_today ?? '—'} />
              <Row label="Gemini calls" value={quota.gemini_calls_today ?? '—'} />
              <Row label="Cache hits" value={quota.cache_hits_today ?? '—'} ok />
            </>
          )}

          {error && (
            <p className="text-[10px] text-danger break-all">{error}</p>
          )}

          <button
            type="button"
            onClick={fetch}
            disabled={loading}
            className="mt-1 w-full rounded border border-border bg-bg py-0.5 text-[10px] text-text-muted hover:bg-border disabled:opacity-50"
          >
            {loading ? 'Refreshing…' : 'Refresh now'}
          </button>

          <p className="text-[9px] text-text-muted text-center">
            Auto-refresh every 30s
          </p>
        </div>
      )}
    </div>
  )
}

function Row({ label, value, ok }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-text-muted">{label}</span>
      <span className={ok === false ? 'text-danger' : ok ? 'text-success' : 'text-text font-semibold'}>
        {String(value)}
      </span>
    </div>
  )
}

/**
 * Exported component. Renders nothing when VITE_SHOW_DEBUG_PANEL is falsy.
 * Safe to include in the component tree unconditionally — the flag check is
 * at module evaluation time, so tree-shaking removes the panel body entirely
 * from production builds where the flag is absent.
 */
export function QuotaDebugPanel() {
  if (!SHOW) return null
  return <Panel />
}

export default QuotaDebugPanel
