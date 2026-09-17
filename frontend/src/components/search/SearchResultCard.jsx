import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, BookOpen, Check, Copy, MessageSquareText, Network } from 'lucide-react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { StatusBadge } from '../ui/StatusBadge'
import { cn } from '../../lib/utils'
import { useToast } from '../../context/ToastContext'

/**
 * @param {{
 *   result: import('../../api/types').SearchResult,
 *   className?: string
 * }} props
 */
export function SearchResultCard({ result, className }) {
  const [copied, setCopied] = useState(false)
  const { showToast } = useToast()

  const relevancePct = typeof result.relevance_score === 'number'
    ? Math.round(result.relevance_score * 100)
    : null

  const handleCopy = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(result.standard_no)
      setCopied(true)
      showToast(`${result.standard_no} copied to clipboard`, 'success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast('Could not copy to clipboard', 'error')
    }
  }

  return (
    <Card
      className={cn(
        'group relative transition-all duration-150 hover:border-primary/40 hover:shadow-[var(--shadow-card-hover)]',
        className
      )}
    >
      <div className="flex flex-col gap-3">
        {/* Header: Standard No + Status Badge + Relevance */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-technical text-sm font-semibold text-primary">
              {result.standard_no}
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="rounded p-0.5 text-text-muted hover:text-text transition-colors"
              title={`Copy ${result.standard_no}`}
              aria-label={`Copy ${result.standard_no}`}
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-success" aria-hidden="true" />
              ) : (
                <Copy className="h-3.5 w-3.5" aria-hidden="true" />
              )}
            </button>
            <StatusBadge status={result.status} />
          </div>

          {relevancePct !== null && (
            <div
              className="flex items-center gap-1.5"
              title={`Relevance score: ${relevancePct}%`}
              aria-label={`Relevance score: ${relevancePct}%`}
            >
              <span className="text-xs text-text-muted">Relevance</span>
              <div className="h-1.5 w-12 overflow-hidden rounded-full bg-border/60">
                <div
                  className="h-full bg-primary/70 transition-all duration-300"
                  style={{ width: `${relevancePct}%` }}
                />
              </div>
              <span className="font-technical text-xs font-medium text-text-muted">
                {relevancePct}%
              </span>
            </div>
          )}
        </div>

        {/* Title */}
        <h2 className="text-base font-semibold leading-snug text-text">
          <Link
            to={`/standards/${encodeURIComponent(result.standard_no)}`}
            className="inline-flex items-center gap-1.5 hover:text-primary focus-visible:text-primary"
          >
            <span>{result.title}</span>
            <ArrowUpRight
              className="h-4 w-4 shrink-0 text-text-muted transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary"
              aria-hidden="true"
            />
          </Link>
        </h2>

        {/* Footer: Category & Actions */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/50 text-xs">
          {result.category ? (
            <Badge tone="neutral">
              <BookOpen className="h-3 w-3 text-text-muted" aria-hidden="true" />
              {result.category}
            </Badge>
          ) : (
            <span />
          )}

          <div className="flex items-center gap-3">
            <Link
              to={`/graph?focus=${encodeURIComponent(result.standard_no)}`}
              className="inline-flex items-center gap-1 font-medium text-text-muted hover:text-text"
              title={`Explore relationship graph for ${result.standard_no}`}
            >
              <Network className="h-3 w-3" aria-hidden="true" />
              Graph
            </Link>

            <Link
              to={`/?q=${encodeURIComponent(`What does ${result.standard_no} require?`)}`}
              className="inline-flex items-center gap-1 font-medium text-text-muted hover:text-text"
              title={`Ask a grounded question about ${result.standard_no}`}
            >
              <MessageSquareText className="h-3 w-3" aria-hidden="true" />
              Ask AI
            </Link>

            <Link
              to={`/standards/${encodeURIComponent(result.standard_no)}`}
              className="font-medium text-primary hover:text-primary-dark"
            >
              Details →
            </Link>
          </div>
        </div>
      </div>
    </Card>
  )
}
