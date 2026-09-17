import { useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { X } from 'lucide-react'
import { cn } from '../../lib/utils'

export function MobileNav({ open, onClose, items }) {
  const drawerRef = useRef(null)
  const closeBtnRef = useRef(null)
  const openerRef = useRef(null)

  // Respect Escape to close, lock body scroll while open, trap focus
  useEffect(() => {
    if (!open) return undefined

    openerRef.current = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    // Focus close button on open
    const timer = setTimeout(() => {
      closeBtnRef.current?.focus()
    }, 50)

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }

      if (e.key === 'Tab' && drawerRef.current) {
        const focusables = drawerRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        const focusableArr = Array.from(focusables).filter(
          (el) => !el.hasAttribute('disabled')
        )
        if (focusableArr.length === 0) return

        const first = focusableArr[0]
        const last = focusableArr[focusableArr.length - 1]

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }

    document.addEventListener('keydown', onKeyDown)

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      if (openerRef.current instanceof HTMLElement) {
        openerRef.current.focus()
      }
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 md:hidden" role="presentation">
      {/* Backdrop */}
      <button
        type="button"
        aria-label="Close navigation menu"
        className="absolute inset-0 bg-text/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className="absolute right-0 top-0 flex h-full w-72 max-w-[85vw] flex-col border-l border-border bg-surface p-4 shadow-2xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <span className="text-sm font-semibold text-text">Navigation</span>
          <button
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="inline-flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] text-text-body hover:bg-bg hover:text-text focus-visible:ring-2 focus-visible:ring-primary"
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
