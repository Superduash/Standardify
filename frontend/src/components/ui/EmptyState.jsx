import { SearchX } from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * Used both for genuine "no results" states and for evidence_found: false —
 * per the design brief, this must never imply the AI knows everything.
 */
export function EmptyState({ icon: Icon = SearchX, title, description, action, className }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-3 rounded-[var(--radius-lg)] border border-dashed border-border bg-bg px-6 py-10 text-center',
        className
      )}
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-surface border border-border">
        <Icon className="h-5 w-5 text-text-muted" aria-hidden="true" />
      </div>
      <div>
        <p className="text-sm font-medium text-text">{title}</p>
        {description && <p className="mt-1 max-w-sm text-sm text-text-muted">{description}</p>}
      </div>
      {action}
    </div>
  )
}
