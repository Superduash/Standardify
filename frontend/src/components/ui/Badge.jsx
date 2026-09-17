import { cn } from '../../lib/utils'

const TONES = {
  neutral: 'bg-bg text-text-body border-border',
  primary: 'bg-primary-light text-primary-dark border-transparent',
  teal: 'bg-teal-light text-teal border-transparent',
  success: 'bg-green-50 text-success border-transparent',
  warning: 'bg-amber-50 text-warning border-transparent',
  danger: 'bg-red-50 text-danger border-transparent',
}

export function Badge({ className, tone = 'neutral', mono = false, children, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-[var(--radius-sm)] border px-2 py-0.5 text-xs font-medium',
        mono && 'font-technical',
        TONES[tone],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
