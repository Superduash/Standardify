import { Link } from 'react-router-dom'
import { AlertCircle, AlertTriangle, ArrowRight, Calendar, CheckCircle2, ShieldAlert } from 'lucide-react'
import { StatusBadge } from '../ui/StatusBadge'
import { cn } from '../../lib/utils'

/**
 * Renders the prominent lifecycle status banner for a standard.
 *
 * @param {{
 *   statusInfo: import('../../api/types').StatusResponse,
 *   className?: string,
 * }} props
 */
export function LifecycleBanner({ statusInfo, className }) {
  if (!statusInfo) return null

  const status = (statusInfo.status || '').toLowerCase()
  const supersededBy = statusInfo.superseded_by
  const lastAmended = statusInfo.last_amended_date

  if (status === 'active') {
    return (
      <div
        className={cn(
          'flex flex-col gap-3 rounded-[var(--radius-lg)] border border-green-200 bg-green-50/60 p-4 sm:flex-row sm:items-center sm:justify-between',
          className
        )}
        role="region"
        aria-label="Active standard lifecycle notice"
      >
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" aria-hidden="true" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-success">
                Current & Active Standard
              </span>
              <StatusBadge status={statusInfo.status} />
            </div>
            <p className="mt-0.5 text-xs text-text-body">
              This document is officially active in the Bureau of Indian Standards (BIS) registry and valid for certification.
            </p>
          </div>
        </div>

        {lastAmended && (
          <div className="flex items-center gap-1.5 rounded-[var(--radius-md)] border border-green-200 bg-surface/80 px-3 py-1.5 text-xs text-text-body shrink-0">
            <Calendar className="h-3.5 w-3.5 text-text-muted" aria-hidden="true" />
            <span>Last amended: <strong className="font-technical font-medium">{lastAmended}</strong></span>
          </div>
        )}
      </div>
    )
  }

  if (status === 'superseded') {
    return (
      <div
        className={cn(
          'flex flex-col gap-3 rounded-[var(--radius-lg)] border border-amber-300 bg-amber-50 p-4 sm:p-5',
          className
        )}
        role="alert"
        aria-label="Superseded standard notice"
      >
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-warning" aria-hidden="true" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-warning">
                This Standard Has Been Superseded
              </span>
              <StatusBadge status={statusInfo.status} />
            </div>
            <p className="text-xs text-text-body leading-relaxed">
              This version has been replaced by a newer standard edition. It remains available for historical reference and legacy contract compliance.
            </p>

            {supersededBy && (
              <div className="pt-2">
                <Link
                  to={`/standards/${encodeURIComponent(supersededBy)}`}
                  className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-surface px-3 py-1.5 text-xs font-semibold text-primary transition-colors hover:bg-primary-light"
                >
                  <span>Go to successor standard:</span>
                  <span className="font-technical">{supersededBy}</span>
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </div>
            )}
          </div>
        </div>

        {lastAmended && (
          <div className="flex items-center gap-1.5 pt-2 border-t border-amber-200/80 text-xs text-text-muted">
            <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Last amendment recorded: <strong className="font-technical">{lastAmended}</strong></span>
          </div>
        )}
      </div>
    )
  }

  if (status === 'withdrawn') {
    return (
      <div
        className={cn(
          'flex flex-col gap-3 rounded-[var(--radius-lg)] border border-red-300 bg-red-50 p-4 sm:p-5',
          className
        )}
        role="alert"
        aria-label="Withdrawn standard notice"
      >
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-danger" aria-hidden="true" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-danger">
                This Standard Has Been Withdrawn
              </span>
              <StatusBadge status={statusInfo.status} />
            </div>
            <p className="text-xs text-text-body leading-relaxed">
              The Bureau of Indian Standards has formally withdrawn this document. It is no longer valid for new product compliance or BIS ISI mark certification.
            </p>
          </div>
        </div>

        {lastAmended && (
          <div className="flex items-center gap-1.5 pt-2 border-t border-red-200/80 text-xs text-text-muted">
            <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Withdrawal / last amended date: <strong className="font-technical">{lastAmended}</strong></span>
          </div>
        )}
      </div>
    )
  }

  if (status === 'under revision') {
    return (
      <div
        className={cn(
          'flex flex-col gap-3 rounded-[var(--radius-lg)] border border-amber-300 bg-amber-50 p-4 sm:p-5',
          className
        )}
        role="alert"
        aria-label="Under revision standard notice"
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-warning" aria-hidden="true" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-warning">
                Standard Under Active Revision
              </span>
              <StatusBadge status={statusInfo.status} />
            </div>
            <p className="text-xs text-text-body leading-relaxed">
              The sectional committee is actively drafting updates or amendments for this standard. The current version remains in force until a revised edition is gazetted.
            </p>
          </div>
        </div>

        {lastAmended && (
          <div className="flex items-center gap-1.5 pt-2 border-t border-amber-200/80 text-xs text-text-muted">
            <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Last amended date: <strong className="font-technical">{lastAmended}</strong></span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-2 rounded-[var(--radius-md)] border border-border bg-surface p-3', className)}>
      <StatusBadge status={statusInfo.status} />
      {lastAmended && (
        <span className="text-xs text-text-muted">
          Last amended: <strong className="font-technical">{lastAmended}</strong>
        </span>
      )}
    </div>
  )
}
