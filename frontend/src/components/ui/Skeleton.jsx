import { cn } from '../../lib/utils'

export function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn('animate-pulse rounded-[var(--radius-sm)] bg-border/60', className)}
      aria-hidden="true"
      {...props}
    />
  )
}

/** A skeleton shaped like the AnswerPanel, shown while /ask is in flight. */
export function AnswerSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading answer">
      <Skeleton className="h-4 w-24" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-11/12" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="flex gap-2 pt-1">
        <Skeleton className="h-6 w-28 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
    </div>
  )
}

/** A skeleton shaped like a SearchResultCard. */
export function SearchResultSkeleton() {
  return (
    <div className="rounded-[var(--radius-lg)] border border-border bg-surface p-5 shadow-[var(--shadow-card)] space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <Skeleton className="h-4 w-16" />
      </div>
      <Skeleton className="h-5 w-3/4" />
      <div className="flex items-center justify-between pt-1">
        <Skeleton className="h-5 w-24 rounded-full" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  )
}

/** Multiple skeletons for the search results loading state. */
export function SearchResultsSkeleton({ count = 4 }) {
  return (
    <div className="space-y-3" role="status" aria-label="Loading search results">
      {Array.from({ length: count }).map((_, i) => (
        <SearchResultSkeleton key={i} />
      ))}
    </div>
  )
}

