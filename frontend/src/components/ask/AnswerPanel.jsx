import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  Copy,
  FileSearch,
  FileText,
  Layers,
  SearchX,
  Zap,
} from 'lucide-react'

import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { ConfidenceBadge } from '../ui/ConfidenceBadge'
import { EmptyState } from '../ui/EmptyState'
import { AnswerSkeleton } from '../ui/Skeleton'
import { ConfidenceInfoTooltip } from './ConfidenceInfoTooltip'
import { CitationDetailPanel } from './CitationDetailPanel'
import { formatLatency } from '../../lib/utils'
import { useToast } from '../../context/ToastContext'

const PROVIDER_LABEL = {
  groq: 'Groq',
  gemini: 'Gemini',
  cache: 'Cached answer',
  none: 'No model used',
}

/**
 * Copy button with feedback and toast.
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
      showToast("Couldn't copy — clipboard access was denied.", 'error')
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-auto flex items-center gap-1.5 rounded-[var(--radius-sm)] px-2 py-1 text-xs font-medium text-text-muted transition-colors hover:bg-bg hover:text-text focus-visible:ring-2 focus-visible:ring-primary"
      aria-label="Copy answer text"
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
  const [activeCitation, setActiveCitation] = useState(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)

  if (loading) {
    return (
      <Card>
        <AnswerSkeleton />
      </Card>
    )
  }

  if (!response) return null

  // 1. Dedicated No-Evidence State (Requirement §10)
  if (!response.evidence_found) {
    return (
      <Card className="text-left space-y-4">
        <EmptyState
          icon={SearchX}
          title="No reliable evidence found in indexed standards"
          description="Standardify strictly answers based on indexed Bureau of Indian Standards documents and could not locate verified clause evidence for this question. Try rephrasing with specific technical terms or check the Standards Search repository directly."
          action={
            <Link
              to="/standards"
              className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
            >
              <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
              Search the standards repository
            </Link>
          }
        />

        {/* Retain visibility of any backend warnings */}
        {response.warnings?.length > 0 && (
          <div className="space-y-2 border-t border-border pt-3">
            {response.warnings.map((warning, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/30 bg-amber-50 px-3 py-2 text-xs text-text-body"
              >
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden="true" />
                <span>{warning}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    )
  }

  const handleOpenCitation = (citation) => {
    setActiveCitation(citation)
    setIsDetailOpen(true)
  }

  // Pure frontend presentation calculation of unique standards present in citations[] (Requirement §6)
  const uniqueStandards = Array.from(
    new Set(response.citations?.map((c) => c.standard_no).filter(Boolean))
  )
  const isMultiStandard = uniqueStandards.length > 1

  return (
    <>
      <Card className="text-left space-y-4">
        {/* Telemetry Header */}
        <div className="flex flex-wrap items-center gap-2 border-b border-border/60 pb-3">
          <div className="flex items-center gap-1">
            <ConfidenceBadge
              label={response.confidence_label}
              value={response.confidence}
            />
            <ConfidenceInfoTooltip
              confidence={response.confidence}
              confidenceLabel={response.confidence_label}
            />
          </div>

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

        {/* Grounded Plain-Language Answer Body */}
        <div className="prose prose-sm max-w-none text-text">
          <p className="text-base leading-relaxed text-text">{response.answer}</p>
        </div>

        {/* Advisory Warnings (e.g. superseded status, low confidence) */}
        {response.warnings?.length > 0 && (
          <div className="space-y-2">
            {response.warnings.map((warning, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 rounded-[var(--radius-md)] border border-warning/30 bg-amber-50 px-3.5 py-2.5 text-xs text-text-body"
                role="alert"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
                <div className="space-y-0.5">
                  <span className="font-semibold text-warning">Notice:</span>
                  <p className="leading-relaxed">{warning}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Citations & Evidence Section */}
        {response.citations?.length > 0 && (
          <div className="border-t border-border pt-4">
            {/* Multi-standard or single-standard evidence heading */}
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                {isMultiStandard ? (
                  <>
                    <Layers className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                    <p className="text-xs font-semibold text-text">
                      This answer draws on <strong className="font-technical text-primary">{uniqueStandards.length}</strong> Indian Standards ({response.citations.length} clauses)
                    </p>
                  </>
                ) : (
                  <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
                    Grounding Evidence ({response.citations.length} cited clause{response.citations.length === 1 ? '' : 's'})
                  </p>
                )}
              </div>

              <span className="text-[11px] text-text-muted hidden sm:inline">
                Click any citation for clause details
              </span>
            </div>

            {/* Citations List */}
            <ul className="space-y-2.5" aria-label="Grounded source citations">
              {response.citations.map((citation, i) => (
                <li key={`${citation.standard_no}-${citation.clause_no}-${i}`}>
                  <button
                    type="button"
                    onClick={() => handleOpenCitation(citation)}
                    className="w-full group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-[var(--radius-md)] border border-border bg-bg p-3 text-left transition-all hover:border-primary/40 hover:bg-surface focus-visible:ring-2 focus-visible:ring-primary"
                    aria-haspopup="dialog"
                  >
                    <div className="flex min-w-0 items-start gap-2.5">
                      <FileText className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
                      <div className="min-w-0 space-y-0.5">
                        <p className="truncate text-sm font-semibold text-text group-hover:text-primary">
                          {citation.title}
                        </p>
                        <p className="font-technical text-xs text-text-muted">
                          <strong className="text-primary font-semibold">{citation.standard_no}</strong> · Clause {citation.clause_no} · Page {citation.page}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs font-medium text-primary shrink-0 self-end sm:self-center">
                      <span>View details</span>
                      <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden="true" />
                    </div>
                  </button>
                </li>
              ))}
            </ul>

            {/* Next Best Actions Loop */}
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border/80 bg-bg p-3 text-xs">
              <span className="font-medium text-text-muted">
                Continue investigation:
              </span>

              <div className="flex flex-wrap items-center gap-2">
                {uniqueStandards[0] && (
                  <Link
                    to={`/graph?focus=${encodeURIComponent(uniqueStandards[0])}`}
                    className="inline-flex items-center gap-1 font-medium text-primary hover:underline"
                  >
                    <span>Explore relationships for {uniqueStandards[0]}</span>
                    <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                  </Link>
                )}

                <span className="text-border">|</span>

                <Link
                  to="/gap-check"
                  className="inline-flex items-center gap-1 font-medium text-teal hover:underline"
                >
                  <span>Check product compliance</span>
                  <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                </Link>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Interactive Citation Detail Dialog */}
      <CitationDetailPanel
        citation={activeCitation}
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
      />
    </>
  )
}
