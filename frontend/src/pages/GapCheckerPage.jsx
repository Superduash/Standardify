import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  FileSearch,
  MessageSquareText,
  SearchX,
} from 'lucide-react'


import { checkGap } from '../api/endpoints'
import { normalizeApiError } from '../api/client'
import { useToast } from '../context/ToastContext'
import { ProductDescriptionForm } from '../components/gap-checker/ProductDescriptionForm'
import { RequirementItem } from '../components/gap-checker/RequirementItem'
import { GapSummaryCard } from '../components/gap-checker/GapSummaryCard'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Skeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { buttonClasses } from '../components/ui/Button'

/** Skeleton loading view for Gap Checker results */
function GapResultsSkeleton() {
  return (
    <div className="space-y-6 pt-4" role="status" aria-label="Analyzing product compliance">
      {/* Summary Skeleton */}
      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <div className="flex gap-2 pt-2">
          <Skeleton className="h-7 w-32 rounded-[var(--radius-md)]" />
          <Skeleton className="h-7 w-28 rounded-[var(--radius-md)]" />
          <Skeleton className="h-7 w-36 rounded-[var(--radius-md)]" />
        </div>
      </Card>

      {/* Applicable Standards Skeleton */}
      <div className="space-y-2">
        <Skeleton className="h-5 w-40" />
        <div className="flex gap-2">
          <Skeleton className="h-10 w-36 rounded-[var(--radius-md)]" />
          <Skeleton className="h-10 w-36 rounded-[var(--radius-md)]" />
        </div>
      </div>

      {/* Requirements List Skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-16 w-full rounded-[var(--radius-md)]" />
        <Skeleton className="h-16 w-full rounded-[var(--radius-md)]" />
        <Skeleton className="h-16 w-full rounded-[var(--radius-md)]" />
      </div>
    </div>
  )
}

export function GapCheckerPage() {
  const [productDescription, setProductDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [error, setError] = useState(null)
  const [hasSubmitted, setHasSubmitted] = useState(false)

  const { showToast } = useToast()

  const handleAnalyze = async (descriptionToAnalyze) => {
    const trimmed = (descriptionToAnalyze || productDescription).trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    setHasSubmitted(true)
    setResponse(null)

    try {
      const result = await checkGap(trimmed)
      setResponse(result)
    } catch (err) {
      const normalized = normalizeApiError(err)
      setError(normalized)

      if (normalized.kind === 'rate_limited') {
        showToast("Rate limit reached. Please wait a moment before re-submitting.", 'error')
      } else if (normalized.kind === 'unavailable') {
        showToast("Compliance assistant is temporarily unavailable.", 'error')
      } else {
        showToast(normalized.message, 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const applicableStandards = response?.applicable_standards || []
  const matchedRequirements = response?.matched_requirements || []
  const missingRequirements = response?.missing_requirements || []

  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10 space-y-8">
      {/* Header */}
      <header className="text-center sm:text-left space-y-2">
        <span className="inline-flex items-center rounded-full border border-primary/20 bg-primary-light px-3 py-1 text-xs font-medium text-primary">
          Compliance Evaluation
        </span>
        <h1 className="text-2xl sm:text-3xl font-bold text-text">
          Product Compliance Gap Checker
        </h1>
        <p className="max-w-2xl text-sm text-text-muted">
          Paste your product material specs, manufacturing processes, or engineering parameters to identify applicable Indian Standards, satisfied clauses, and missing certification criteria.
        </p>
      </header>

      {/* How it works strip */}
      <section aria-label="How compliance gap check works">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center text-xs">
          <div className="rounded-[var(--radius-md)] border border-border bg-surface p-3 space-y-1">
            <span className="font-technical text-[11px] font-bold text-primary">01</span>
            <p className="font-medium text-text">Product Specs</p>
            <p className="text-[11px] text-text-muted">Provide materials & use</p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-border bg-surface p-3 space-y-1">
            <span className="font-technical text-[11px] font-bold text-primary">02</span>
            <p className="font-medium text-text">Standards Match</p>
            <p className="text-[11px] text-text-muted">Identify relevant BIS specs</p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-border bg-surface p-3 space-y-1">
            <span className="font-technical text-[11px] font-bold text-success">03</span>
            <p className="font-medium text-text">Matched Clauses</p>
            <p className="text-[11px] text-text-muted">Satisfied requirements</p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-border bg-surface p-3 space-y-1">
            <span className="font-technical text-[11px] font-bold text-warning">04</span>
            <p className="font-medium text-text">Missing Gaps</p>
            <p className="text-[11px] text-text-muted">Unverified test items</p>
          </div>
        </div>
      </section>

      {/* Input Form */}
      <section aria-label="Product description input">
        <ProductDescriptionForm
          value={productDescription}
          onChange={setProductDescription}
          onSubmit={handleAnalyze}
          loading={loading}
        />
      </section>

      {/* Results Section */}
      <section aria-label="Compliance gap analysis results" className="space-y-6">
        {/* Loading Skeleton */}
        {loading && <GapResultsSkeleton />}

        {/* Blocking Error State */}
        {!loading && error && (
          <ErrorState
            message={
              error.kind === 'validation'
                ? 'Please check your product description input and submit again.'
                : error.kind === 'rate_limited'
                ? 'The assistant is temporarily rate-limited (60 requests/min limit). Please wait a moment and try again.'
                : error.kind === 'unavailable'
                ? 'The compliance analysis engine is temporarily unavailable. Please try again shortly.'
                : error.message || 'Failed to complete compliance check.'
            }
            requestId={error.requestId}
            onRetry={() => handleAnalyze(productDescription)}
          />
        )}

        {/* Zero Results / No Standards Matched */}
        {!loading && !error && hasSubmitted && response && applicableStandards.length === 0 && (
          <Card className="p-6 text-center">
            <EmptyState
              icon={SearchX}
              title="No matching Indian Standards found"
              description="We couldn't confidently match this product description to any standard in the currently indexed BIS repository. The product domain may not be indexed yet in this environment."
              action={
                <Link
                  to="/standards"
                  className={buttonClasses({ variant: 'secondary', size: 'sm', className: 'mt-3' })}
                >
                  <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
                  Search standards repository directly
                </Link>
              }
            />
          </Card>
        )}

        {/* Success Results View */}
        {!loading && !error && response && applicableStandards.length > 0 && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* A. Executive Gap Summary Card */}
            <GapSummaryCard
              summary={response.summary}
              confidence={response.confidence}
              matchedCount={matchedRequirements.length}
              missingCount={missingRequirements.length}
              standardsCount={applicableStandards.length}
            />

            {/* B. Applicable Standards List */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                  <BookOpen className="h-4 w-4 text-primary" aria-hidden="true" />
                  Applicable Indian Standards ({applicableStandards.length})
                </h2>
                <span className="text-xs text-text-muted hidden sm:inline">
                  Click a standard for full details & lifecycle
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {applicableStandards.map((std) => (
                  <Card
                    key={std}
                    className="p-4 flex flex-col justify-between gap-3 border-border hover:border-primary/40 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-technical text-base font-bold text-primary">
                        {std}
                      </span>
                      <Badge tone="primary">Applicable</Badge>
                    </div>

                    <div className="flex items-center justify-between gap-2 pt-2 border-t border-border/50 text-xs">
                      <Link
                        to={`/standards/${encodeURIComponent(std)}`}
                        className="font-medium text-primary hover:text-primary-dark"
                      >
                        Standard Details →
                      </Link>

                      <Link
                        to={`/?q=${encodeURIComponent(`What does ${std} require?`)}`}
                        className="inline-flex items-center gap-1 text-text-muted hover:text-text"
                        title={`Ask a grounded question about ${std}`}
                      >
                        <MessageSquareText className="h-3 w-3" aria-hidden="true" />
                        Ask AI
                      </Link>
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            {/* C. Matched Requirements */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-success flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  Matched & Satisfied Requirements ({matchedRequirements.length})
                </h2>
                <span className="text-xs text-text-muted">
                  Identified in product specifications
                </span>
              </div>

              {matchedRequirements.length > 0 ? (
                <div className="space-y-2.5">
                  {matchedRequirements.map((req, i) => (
                    <RequirementItem key={i} rawText={req} type="matched" />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">
                  No verified requirements were explicitly satisfied in the provided specification text.
                </p>
              )}
            </div>

            {/* D. Missing Requirements / Gaps */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-warning flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" aria-hidden="true" />
                  Missing / Unaddressed Requirements ({missingRequirements.length})
                </h2>
                <span className="text-xs text-text-muted">
                  Requires validation or lab test proof
                </span>
              </div>

              {missingRequirements.length > 0 ? (
                <div className="space-y-2.5">
                  {missingRequirements.map((req, i) => (
                    <RequirementItem key={i} rawText={req} type="missing" />
                  ))}
                </div>
              ) : (
                <p className="text-xs text-text-muted italic">
                  No missing standard requirements were flagged for this specification.
                </p>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

export default GapCheckerPage
