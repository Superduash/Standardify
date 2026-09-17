import { Link } from 'react-router-dom'
import { ArrowRight, HelpCircle, MessageSquareText, Sparkles } from 'lucide-react'
import { Card } from '../ui/Card'
import { buttonClasses } from '../ui/Button'
import { cn } from '../../lib/utils'

/**
 * Bridges the Standard Detail page into the Home Grounded Ask Experience
 * with pre-filled questions.
 *
 * @param {{
 *   standardNo: string,
 *   className?: string,
 * }} props
 */
export function AskAboutStandardCTA({ standardNo, className }) {
  const defaultPrompt = `What does ${standardNo} require?`
  const samplePrompts = [
    `What does ${standardNo} require?`,
    `What are the test methods specified in ${standardNo}?`,
    `What are the physical dimensions and tolerances in ${standardNo}?`,
  ]

  return (
    <Card
      className={cn(
        'relative overflow-hidden border-primary/30 bg-gradient-to-br from-primary-light/40 via-surface to-teal-light/20 p-6 shadow-[var(--shadow-card)]',
        className
      )}
      role="region"
      aria-label="Ask questions about this standard"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1.5 max-w-xl">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" aria-hidden="true" />
            <span className="text-xs font-semibold uppercase tracking-wider text-primary">
              AI Grounded Assistant
            </span>
          </div>
          <h2 className="text-lg font-bold text-text">
            Have questions about {standardNo}?
          </h2>
          <p className="text-xs text-text-body leading-relaxed">
            Ask natural language questions about exact clause requirements, testing procedures, or material specs grounded in the standard document.
          </p>
        </div>

        <Link
          to={`/?q=${encodeURIComponent(defaultPrompt)}`}
          className={buttonClasses({
            variant: 'primary',
            size: 'md',
            className: 'shrink-0 self-start sm:self-center font-medium shadow-sm',
          })}
        >
          <MessageSquareText className="h-4 w-4" aria-hidden="true" />
          Ask about this standard
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>

      {/* Quick sample prompt bridges */}
      <div className="mt-5 border-t border-border/60 pt-3">
        <p className="text-[11px] font-medium text-text-muted flex items-center gap-1 mb-2">
          <HelpCircle className="h-3 w-3" aria-hidden="true" />
          Or choose a common inquiry:
        </p>
        <div className="flex flex-wrap gap-2">
          {samplePrompts.map((prompt, i) => (
            <Link
              key={i}
              to={`/?q=${encodeURIComponent(prompt)}`}
              className="rounded-[var(--radius-sm)] border border-border bg-surface px-2.5 py-1 text-xs text-text-body transition-colors hover:border-primary/50 hover:bg-primary-light/60 hover:text-primary"
            >
              {prompt}
            </Link>
          ))}
        </div>
      </div>
    </Card>
  )
}
