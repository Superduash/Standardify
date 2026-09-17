import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'
import { cn } from '../../../lib/utils'

const VARIANT_STYLES = {
  info: {
    icon: Info,
    classes: 'border-border bg-surface text-text',
    iconClasses: 'text-primary',
  },
  success: {
    icon: CheckCircle2,
    classes: 'border-border bg-surface text-text',
    iconClasses: 'text-success',
  },
  warning: {
    icon: AlertTriangle,
    classes: 'border-border bg-surface text-text',
    iconClasses: 'text-warning',
  },
  error: {
    icon: XCircle,
    classes: 'border-border bg-surface text-text',
    iconClasses: 'text-danger',
  },
}

export function Toast({ toast, onDismiss }) {
  const config = VARIANT_STYLES[toast.variant] ?? VARIANT_STYLES.info
  const Icon = config.icon

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'toast-enter pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-[var(--radius-md)] border px-4 py-3 shadow-[var(--shadow-card-hover)]',
        config.classes
      )}
    >
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', config.iconClasses)} aria-hidden="true" />
      <p className="flex-1 text-sm leading-snug text-text-body">{toast.message}</p>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        className="shrink-0 rounded-[var(--radius-sm)] p-1 text-text-muted transition-colors hover:bg-bg hover:text-text"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  )
}
