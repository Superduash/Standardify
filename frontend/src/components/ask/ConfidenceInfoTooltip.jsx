import { useEffect, useRef, useState } from 'react'
import { HelpCircle, Info, X } from 'lucide-react'
import { cn, formatConfidence } from '../../lib/utils'

const CONFIDENCE_DESCRIPTIONS = {
  high: {
    title: 'High Confidence',
    text: 'Strong evidence match directly retrieved from the indexed Indian Standards. The grounded answer closely reflects the cited clauses.',
    tone: 'text-success',
  },
  medium: {
    title: 'Medium Confidence',
    text: 'A relevant match was found in the indexed standards, but cross-verifying the cited clause and context is recommended.',
    tone: 'text-warning',
  },
  low: {
    title: 'Low Confidence',
    text: 'Limited evidence match in the indexed material. Please verify the cited standard numbers and clauses carefully before relying on this response.',
    tone: 'text-danger',
  },
}

/**
 * Accessible info popover explaining the grounding confidence score.
 *
 * @param {{
 *   confidence?: number,
 *   confidenceLabel?: "high" | "medium" | "low" | string,
 *   className?: string,
 * }} props
 */
export function ConfidenceInfoTooltip({
  confidence,
  confidenceLabel = 'medium',
  className,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const popoverRef = useRef(null)
  const buttonRef = useRef(null)

  const labelKey = (confidenceLabel || '').toLowerCase()
  const info = CONFIDENCE_DESCRIPTIONS[labelKey] || CONFIDENCE_DESCRIPTIONS.medium

  // Handle outside click & Escape key to close popover
  useEffect(() => {
    if (!isOpen) return

    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsOpen(false)
        buttonRef.current?.focus()
      }
    }

    function handleClickOutside(e) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  return (
    <div className={cn('relative inline-flex items-center', className)}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label="How confidence is calculated"
        className="flex h-5 w-5 items-center justify-center rounded-full text-text-muted transition-colors hover:bg-bg hover:text-text focus-visible:ring-2 focus-visible:ring-primary"
      >
        <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-label="Confidence score explanation"
          className="absolute bottom-full left-0 z-50 mb-2 w-72 rounded-[var(--radius-lg)] border border-border bg-surface p-3.5 shadow-lg ring-1 ring-black/5 text-left text-xs sm:left-auto sm:right-0"
        >
          <div className="flex items-center justify-between pb-2 border-b border-border/60">
            <div className="flex items-center gap-1.5 font-semibold text-text">
              <Info className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
              <span>Grounding Confidence</span>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded p-0.5 text-text-muted hover:bg-bg hover:text-text"
              aria-label="Close confidence explanation"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          </div>

          <div className="pt-2 space-y-2">
            <div className="flex items-center justify-between">
              <span className={cn('font-semibold capitalize', info.tone)}>
                {info.title}
              </span>
              {typeof confidence === 'number' && (
                <span className="font-technical text-[11px] text-text-muted">
                  Raw Score: {formatConfidence(confidence)}
                </span>
              )}
            </div>

            <p className="text-xs text-text-body leading-relaxed">{info.text}</p>

            <div className="pt-1 text-[10px] text-text-muted border-t border-border/40">
              Score is calculated based on cosine similarity of retrieved BIS standard clauses against your inquiry.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
