import { forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const VARIANTS = {
  primary:
    'bg-primary text-white hover:bg-primary-dark active:bg-primary-dark disabled:bg-primary/50',
  secondary:
    'bg-surface text-primary border border-border hover:bg-primary-light disabled:opacity-50',
  ghost:
    'bg-transparent text-text-body hover:bg-bg disabled:opacity-50',
  danger:
    'bg-surface text-danger border border-border hover:bg-red-50 disabled:opacity-50',
}

const SIZES = {
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
}

/**
 * Shared class builder so non-<button> elements (e.g. a router <Link> that
 * needs to *look* like a button) can reuse the exact same visual variants
 * instead of duplicating the style rules.
 */
export function buttonClasses({ variant = 'primary', size = 'md', className } = {}) {
  return cn(
    'inline-flex items-center justify-center rounded-[var(--radius-md)] font-medium transition-all duration-150 ease-out active:scale-[0.985] disabled:cursor-not-allowed disabled:active:scale-100',
    VARIANTS[variant],
    SIZES[size],
    className
  )
}

export const Button = forwardRef(function Button(
  { className, variant = 'primary', size = 'md', loading = false, disabled, children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={buttonClasses({ variant, size, className })}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
})
