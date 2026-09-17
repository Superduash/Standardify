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
