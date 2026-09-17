import { AlertCircle, RotateCw } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Button } from './Button'

/**
 * Inline, blocking error state — for errors that prevent a whole section
 * from rendering. Transient errors (network/429/503) should ALSO surface a
 * toast; this component is for the "there is nothing else to show" case.
 */
export function ErrorState({ message, requestId, onRetry, className }) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center gap-3 rounded-[var(--radius-lg)] border border-danger/30 bg-red-50 px-6 py-8 text-center',
        className
      )}
    >
      <AlertCircle className="h-6 w-6 text-danger" aria-hidden="true" />
      <p className="max-w-sm text-sm text-text-body">
        {message || 'Something went wrong. Please try again.'}
      </p>
      {requestId && (
        <p className="font-technical text-xs text-text-muted">Reference: {requestId}</p>
      )}
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
          Try again
        </Button>
      )}
    </div>
  )
}
