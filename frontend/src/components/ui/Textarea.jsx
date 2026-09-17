import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

export const Textarea = forwardRef(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        'w-full resize-none rounded-[var(--radius-md)] border border-border bg-surface px-3.5 py-3 text-sm text-text placeholder:text-text-muted',
        'transition-colors duration-150 focus-visible:border-primary',
        className
      )}
      {...props}
    />
  )
})
