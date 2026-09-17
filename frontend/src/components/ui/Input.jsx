import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

export const Input = forwardRef(function Input({ className, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={cn(
        'h-11 w-full rounded-[var(--radius-md)] border border-border bg-surface px-3.5 text-sm text-text placeholder:text-text-muted',
        'transition-colors duration-150 focus-visible:border-primary',
        className
      )}
      {...props}
    />
  )
})
