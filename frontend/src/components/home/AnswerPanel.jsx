import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowUpRight, Check, Copy, FileText, SearchX, Zap } from 'lucide-react'
import { useState } from 'react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { ConfidenceBadge } from '../ui/ConfidenceBadge'
import { EmptyState } from '../ui/EmptyState'
import { AnswerSkeleton } from '../ui/Skeleton'
import { formatLatency } from '../../lib/utils'
import { useToast } from '../../context/ToastContext'

const PROVIDER_LABEL = {
  groq: 'Groq',
  gemini: 'Gemini',
  cache: 'Cached answer',
  none: 'No model used',
}

/**
 * Small, self-contained so it can own its own `copied` state and call
 * useToast() without affecting AnswerPanel's early-return branches above.
 * @param {{ text: string }} props
 */
function CopyAnswerButton({ text }) {
  const [copied, setCopied] = useState(false)
  const { showToast } = useToast()

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      showToast('Answer copied to clipboard.', 'success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast("Couldn't copy — your browser may be blocking clipboard access.", 'error')
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-auto flex items-center gap-1.5 rounded-[var(--radius-sm)] px-2 py-1 text-xs font-medium text-text-muted transition-colors hover:bg-bg hover:text-text"
      aria-label="Copy answer to clipboard"
    >
      {copied ? (
        <>
          <Check className="h-3.5 w-3.5 text-success" aria-hidden="true" />
          Copied
        </>
      ) : (
        <>
          <Copy className="h-3.5 w-3.5" aria-hidden="true" />
          Copy
        </>
      )}
    </button>
  )
}

/**
 * @param {{
 *   loading: boolean,
 *   response: import('../../api/types').AskResponse | null,
 * }} props
 */
export function AnswerPanel({ loading, response }) {
  if (loading) {
    return (
      <Card>
        <AnswerSkeleton />
      </Card>
    )
  }

  if (!response) return null

  if (!response.evidence_found) {
    return (
      <Card>
        <EmptyState
          icon={SearchX}
          title="No reliable evidence found"
          description="Standardify only answers from the standards it has indexed, and didn't find a confident match for this question. Try rephrasing, or check the Standards Search page directly."
        />
      </Card>
    )
  }

  return (
    <Card className="text-left">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <ConfidenceBadge label={response.confidence_label} value={response.confidence} />
        {response.provider_used && response.provider_used !== 'none' && (
          <Badge tone="neutral">
            <Zap className="h-3 w-3" aria-hidden="true" />
            {PROVIDER_LABEL[response.provider_used] ?? response.provider_used}
          </Badge>
        )}
        {typeof response.latency_ms === 'number' && response.latency_ms > 0 && (
          <span className="font-technical text-xs text-text-muted">
            {formatLatency(response.latency_ms)}
          </span>
        )}
        <CopyAnswerButton text={response.answer} />
      </div>

      <p className="text-base leading-relaxed text-text">{response.answer}</p>

      {response.warnings?.length > 0 && (
        <div className="mt-4 space-y-2">
          {response.warnings.map((warning, i) => (
            <div
              key={i}
              className="flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/30 bg-amber-50 px-3 py-2 text-sm text-text-body"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}

      {response.citations?.length > 0 && (
        <div className="mt-5 border-t border-border pt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Sources
          </p>
          <ul className="space-y-2">
            {response.citations.map((citation, i) => (
              <li
                key={`${citation.standard_no}-${citation.clause_no}-${i}`}
                className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2.5"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <FileText className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-text">{citation.title}</p>
                    <p className="font-technical text-xs text-text-muted">
                      {citation.standard_no} · Clause {citation.clause_no} · Page {citation.page}
                    </p>
                  </div>
                </div>
                {/*
                  Standard detail pages land in Phase 2 (see frontendplan.md).
                  Until then this honestly routes to Standards Search, pre-filled
                  with this standard number, rather than linking to a page that
                  doesn't exist yet.
                */}
                <Link
                  to={`/standards?q=${encodeURIComponent(citation.standard_no)}`}
                  className="flex shrink-0 items-center gap-1 text-xs font-medium text-primary hover:text-primary-dark"
                >
                  View source
                  <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}
