import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Check, Copy, FileSearch, FileX2 } from 'lucide-react'
import { getStandardStatus, getGraphForStandard } from '../api/endpoints'

import { normalizeApiError } from '../api/client'
import { useToast } from '../context/ToastContext'
import { LifecycleBanner } from '../components/standard-detail/LifecycleBanner'
import { RelationshipTeaser } from '../components/standard-detail/RelationshipTeaser'
import { AskAboutStandardCTA } from '../components/standard-detail/AskAboutStandardCTA'
import { StatusBadge } from '../components/ui/StatusBadge'
import { Button, buttonClasses } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Skeleton } from '../components/ui/Skeleton'
import { ErrorState } from '../components/ui/ErrorState'


/** Skeleton loading view for StandardDetailPage */
function StandardDetailSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading standard details">
      {/* Breadcrumb Skeleton */}
      <Skeleton className="h-4 w-36" />

      {/* Header Skeleton */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-44" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
        <Skeleton className="h-4 w-72" />
      </div>

      {/* Lifecycle Banner Skeleton */}
      <Skeleton className="h-20 w-full rounded-[var(--radius-lg)]" />

      {/* Relationship Teaser Skeleton */}
      <Card className="space-y-3">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-64" />
        <div className="space-y-2 pt-2">
          <Skeleton className="h-12 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-12 w-full rounded-[var(--radius-md)]" />
        </div>
      </Card>

      {/* CTA Skeleton */}
      <Skeleton className="h-32 w-full rounded-[var(--radius-lg)]" />
    </div>
  )
}

export function StandardDetailPage() {
  const { standardNo: rawStandardNo } = useParams()
  const navigate = useNavigate()
  const { showToast } = useToast()

  const standardNo = decodeURIComponent(rawStandardNo || '').trim()

  const [statusData, setStatusData] = useState(null)
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [statusError, setStatusError] = useState(null)
  const [graphError, setGraphError] = useState(null)
  const [isNotFound, setIsNotFound] = useState(false)
  const [copied, setCopied] = useState(false)

  const loadData = useCallback(async () => {
    if (!standardNo) {
      setIsNotFound(true)
      setLoading(false)
      return
    }

    setLoading(true)
    setStatusError(null)
    setGraphError(null)
    setIsNotFound(false)

    // Parallel fetch status and depth=1 relationship subgraph
    const [statusResult, graphResult] = await Promise.allSettled([
      getStandardStatus(standardNo),
      getGraphForStandard(standardNo, 1),
    ])

    // Handle Status result
    if (statusResult.status === 'fulfilled') {
      setStatusData(statusResult.value)
    } else {
      const normErr = normalizeApiError(statusResult.reason)
      if (normErr.kind === 'not_found' || normErr.status === 404) {
        setIsNotFound(true)
      } else {
        setStatusError(normErr)
      }
    }

    // Handle Graph result (soft failure — doesn't block status page)
    if (graphResult.status === 'fulfilled') {
      setGraphData(graphResult.value)
    } else {
      setGraphError(normalizeApiError(graphResult.reason))
    }

    setLoading(false)
  }, [standardNo])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(standardNo)
      setCopied(true)
      showToast(`${standardNo} copied to clipboard`, 'success')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast('Could not copy to clipboard', 'error')
    }
  }

  // 1. Loading state
  if (loading) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
        <StandardDetailSkeleton />
      </main>
    )
  }

  // 2. 404 / Dedicated Not Found state
  if (isNotFound) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-50 border border-amber-200 text-warning">
          <FileX2 className="h-7 w-7" aria-hidden="true" />
        </div>
        <h1 className="mt-4 text-2xl font-bold text-text sm:text-3xl">
          Standard Not in BIS Registry
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-text-muted">
          The standard <strong className="font-technical text-text">{standardNo || 'Unknown'}</strong> isn't in the indexed Bureau of Indian Standards registry. It may be unindexed, mistyped, or not yet published.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            to="/standards"
            className={buttonClasses({ variant: 'primary', size: 'md' })}
          >
            <FileSearch className="h-4 w-4" aria-hidden="true" />
            Search all standards
          </Link>
          <Button
            variant="secondary"
            size="md"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Go back
          </Button>
        </div>
      </main>
    )
  }

  // 3. Blocking Server/Network Error state
  if (statusError && !statusData) {
    return (
      <main className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16">
        <ErrorState
          message={statusError.message || 'Failed to load standard information.'}
          requestId={statusError.requestId}
          onRetry={loadData}
        />
      </main>
    )
  }

  // 4. Success State
  return (
    <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10 space-y-6">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-text-muted">
        <Link to="/" className="hover:text-primary">
          Home
        </Link>
        <span>/</span>
        <Link to="/standards" className="hover:text-primary">
          Standards
        </Link>
        <span>/</span>
        <span className="font-technical text-text font-medium truncate" aria-current="page">
          {standardNo}
        </span>
      </nav>

      {/* Header with Standard Identifier & Action Buttons */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-6">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="font-technical text-2xl sm:text-3xl font-bold text-text">
              {standardNo}
            </h1>
            {statusData?.status && <StatusBadge status={statusData.status} />}
          </div>
          <p className="text-xs text-text-muted">
            Bureau of Indian Standards · Verified Document Record
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-xs font-medium text-text-body transition-colors hover:bg-bg hover:text-text"
            aria-label="Copy standard number to clipboard"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-success" aria-hidden="true" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
                Copy number
              </>
            )}
          </button>

          <Link
            to="/standards"
            className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-xs font-medium text-text-body transition-colors hover:bg-bg hover:text-text"
          >
            <ArrowLeft className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
            Back to search
          </Link>
        </div>
      </header>

      {/* Lifecycle Status Banner */}
      {statusData && (
        <section aria-label="Standard lifecycle status">
          <LifecycleBanner statusInfo={statusData} />
        </section>
      )}

      {/* 1-Hop Subgraph Relationship Teaser */}
      <section aria-label="Related standards">
        <RelationshipTeaser
          graphData={graphData}
          standardNo={standardNo}
          loading={loading}
          error={graphError}
          onRetry={loadData}
        />
      </section>

      {/* Ask Grounded Assistant CTA Bridge */}
      <section aria-label="Ask about this standard">
        <AskAboutStandardCTA standardNo={standardNo} />
      </section>
    </main>
  )
}

export default StandardDetailPage
