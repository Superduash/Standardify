import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

export function MobileNav({ open, onClose, items }) {
  // Respect Escape to close, lock body scroll while open — standard drawer behavior.
  useEffect(() => {
    if (!open) return undefined

    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <button
        type="button"
        aria-label="Close navigation menu"
        className="absolute inset-0 bg-text/40"
        onClick={onClose}
      />
      <div className="absolute right-0 top-0 flex h-full w-72 max-w-[85vw] flex-col border-l border-border bg-surface p-4 shadow-[var(--shadow-card-hover)]">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-text">Menu</span>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="inline-flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] text-text-body hover:bg-bg"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav className="flex flex-col gap-1" aria-label="Primary">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-light text-primary-dark'
                    : 'text-text-body hover:bg-bg hover:text-text'
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <a
          href="https://github.com/Superduash/Standardify"
          target="_blank"
          rel="noreferrer"
          className="mt-auto rounded-[var(--radius-md)] border border-border px-3 py-2.5 text-center text-sm font-medium text-text-body hover:bg-bg"
        >
          View source on GitHub
        </a>
      </div>
    </div>
  )
}
