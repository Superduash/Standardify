import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

const SIZES = {
  sm: 'h-7 w-7',
  md: 'h-9 w-9',
  lg: 'h-11 w-11',
}

const VARIANTS = {
  ghost: 'text-text-muted hover:bg-bg hover:text-text',
  outline: 'border border-border text-text-muted hover:bg-bg hover:text-text',
  primary: 'bg-primary text-white hover:bg-primary-dark',
}

/**
 * Icon-only button — always requires an accessible `aria-label`.
 * Never renders visible text; the icon is purely decorative.
 */
export const IconButton = forwardRef(function IconButton(
  { className, size = 'md', variant = 'ghost', 'aria-label': ariaLabel, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type="button"
      aria-label={ariaLabel}
      className={cn(
        'inline-flex items-center justify-center rounded-[var(--radius-sm)] transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50',
        SIZES[size],
        VARIANTS[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
})
