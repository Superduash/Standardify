import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, FileSearch, FileText, Network, X } from 'lucide-react'
import { buttonClasses } from '../ui/Button'


/**
 * Interactive citation detail dialog showing standard, clause, page,
 * and quick actions into Standard Detail, Search, and Graph.
 *
 * @param {{
 *   citation: import('../../api/types').CitedStandard | null,
 *   isOpen: boolean,
 *   onClose: () => void,
 * }} props
 */
export function CitationDetailPanel({ citation, isOpen, onClose }) {
  const modalRef = useRef(null)
  const closeButtonRef = useRef(null)
  const previouslyFocusedElementRef = useRef(null)

  // Focus trap, Escape handling, and focus restoration
  useEffect(() => {
    if (!isOpen) return

    previouslyFocusedElementRef.current = document.activeElement
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    // Focus close button initially
    const timer = setTimeout(() => {
      closeButtonRef.current?.focus()
    }, 50)

    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }

      // Tab trap inside modal
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        const focusableArr = Array.from(focusable).filter(
          (el) => !el.hasAttribute('disabled') && !el.getAttribute('aria-hidden')
        )

        if (focusableArr.length === 0) return

        const firstElement = focusableArr[0]
        const lastElement = focusableArr[focusableArr.length - 1]

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault()
            lastElement.focus()
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault()
            firstElement.focus()
          }
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = prevOverflow
      if (previouslyFocusedElementRef.current instanceof HTMLElement) {
        previouslyFocusedElementRef.current.focus()
      }
    }
  }, [isOpen, onClose])

  if (!isOpen || !citation) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-150"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-modal-title"
        className="relative w-full max-w-lg rounded-[var(--radius-lg)] border border-border bg-surface p-6 shadow-2xl space-y-5 text-left animate-panel-in"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border pb-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-primary-light text-primary">
              <FileText className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                Source Citation Reference
              </span>
              <h2 id="citation-modal-title" className="font-technical text-lg font-bold text-primary">
                {citation.standard_no}
              </h2>
            </div>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="rounded-[var(--radius-sm)] p-1 text-text-muted hover:bg-bg hover:text-text"
            aria-label="Close citation details"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {/* Citation Metadata Grid */}
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-text-muted">Document / Clause Title</label>
            <p className="mt-0.5 text-sm font-semibold text-text">{citation.title}</p>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="rounded-[var(--radius-md)] border border-border bg-bg p-3">
              <span className="text-xs text-text-muted">Clause Number</span>
              <p className="font-technical mt-0.5 text-base font-bold text-text">
                Clause {citation.clause_no}
              </p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-border bg-bg p-3">
              <span className="text-xs text-text-muted">Document Page</span>
              <p className="font-technical mt-0.5 text-base font-bold text-text">
                Page {citation.page}
              </p>
            </div>
          </div>

          <p className="text-xs text-text-muted leading-relaxed pt-1">
            This clause snippet was extracted from the officially indexed BIS standard and used as grounding evidence for the response.
          </p>
        </div>

        {/* Action Actions (Detail, Search, Graph, Ask) */}
        <div className="space-y-2 border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Quick Actions
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <Link
              to={`/standards/${encodeURIComponent(citation.standard_no)}`}
              onClick={onClose}
              className={buttonClasses({
                variant: 'primary',
                size: 'sm',
                className: 'justify-center text-xs',
              })}
            >
              <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
              Standard Details
            </Link>

            <Link
              to={`/graph?focus=${encodeURIComponent(citation.standard_no)}`}
              onClick={onClose}
              className={buttonClasses({
                variant: 'secondary',
                size: 'sm',
                className: 'justify-center text-xs',
              })}
            >
              <Network className="h-3.5 w-3.5" aria-hidden="true" />
              Relationships
            </Link>

            <Link
              to={`/standards?q=${encodeURIComponent(citation.standard_no)}`}
              onClick={onClose}
              className={buttonClasses({
                variant: 'secondary',
                size: 'sm',
                className: 'justify-center text-xs',
              })}
            >
              <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
              Search
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
