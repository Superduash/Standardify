import { Clock, History, Trash2 } from 'lucide-react'
import { ConfidenceBadge } from '../ui/ConfidenceBadge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { cn } from '../../lib/utils'


const SESSION_STORAGE_KEY = 'standardify_ask_session_history'

/**
 * Reads and safely parses session history entries from sessionStorage.
 * @returns {Array<{id: string, question: string, response: import('../../api/types').AskResponse, timestamp: string}>}
 */
export function loadSessionHistory() {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

/**
 * Saves a new Ask interaction to sessionStorage.
 * @param {string} question
 * @param {import('../../api/types').AskResponse} response
 */
export function saveToSessionHistory(question, response) {
  if (!question || !response) return
  try {
    const existing = loadSessionHistory()
    // Prepend new item (capped at 10 items for memory efficiency)
    const updated = [
      {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        question,
        response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
      ...existing.filter((item) => item.question !== question),
    ].slice(0, 10)

    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // Gracefully ignore storage quota errors
  }
}

/**
 * Clears Ask session history from sessionStorage.
 */
export function clearSessionHistory() {
  try {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  } catch {
    // Ignore
  }
}

/**
 * Renders session history entries stored in sessionStorage.
 *
 * @param {{
 *   history: Array<{id: string, question: string, response: import('../../api/types').AskResponse, timestamp: string}>,
 *   onSelect: (item: {question: string, response: import('../../api/types').AskResponse}) => void,
 *   onClear: () => void,
 *   activeQuestion?: string,
 *   className?: string,
 * }} props
 */
export function SessionHistory({
  history = [],
  onSelect,
  onClear,
  activeQuestion,
  className,
}) {
  if (!history || history.length === 0) return null


  return (
    <Card
      className={cn('border-border/80 bg-surface/90 text-left p-4 space-y-3', className)}
      role="region"
      aria-label="Recent session inquiries"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-primary" aria-hidden="true" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-text">
            Inquiries This Session
          </h3>
          <span className="rounded-full bg-primary-light px-2 py-0.5 font-technical text-[10px] font-semibold text-primary">
            {history.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-text-muted hidden sm:inline">
            Tab session only · Clears on close
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="h-7 px-2 text-xs text-text-muted hover:text-danger hover:bg-red-50"
            title="Clear inquiries from this session"
            aria-label="Clear session inquiries"
          >
            <Trash2 className="h-3 w-3" aria-hidden="true" />
            Clear
          </Button>
        </div>
      </div>

      {/* History Items */}
      <ul className="space-y-2">
        {history.map((item) => {
          const isActive = item.question === activeQuestion
          const citationCount = item.response?.citations?.length || 0

          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item)}
                className={cn(
                  'w-full flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-[var(--radius-md)] border p-2.5 text-left transition-all',
                  isActive
                    ? 'border-primary/50 bg-primary-light/40 text-primary-dark shadow-xs'
                    : 'border-border bg-bg text-text hover:border-primary/30 hover:bg-surface'
                )}
                aria-pressed={isActive}
              >
                <div className="min-w-0 flex-1 space-y-0.5">
                  <p className="truncate text-xs font-medium text-text">{item.question}</p>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
                    <span className="flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5" aria-hidden="true" />
                      {item.timestamp}
                    </span>
                    <span>·</span>
                    <span>
                      {citationCount} citation{citationCount === 1 ? '' : 's'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  {item.response?.confidence_label && (
                    <ConfidenceBadge
                      label={item.response.confidence_label}
                      value={item.response.confidence}
                    />
                  )}
                  <span className="font-technical text-[10px] text-primary hover:underline">
                    Restore ↵
                  </span>
                </div>
              </button>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}
