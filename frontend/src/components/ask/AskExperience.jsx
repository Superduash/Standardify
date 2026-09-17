import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AlertCircle, ArrowRight } from 'lucide-react'
import { askQuestion } from '../../api/endpoints'
import { normalizeApiError } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { useRateLimitCooldown } from '../../hooks/useRateLimitCooldown'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { ErrorState } from '../ui/ErrorState'
import { ExamplePrompts } from './ExamplePrompts'
import { AnswerPanel } from './AnswerPanel'
import {
  SessionHistory,
  clearSessionHistory,
  loadSessionHistory,
  saveToSessionHistory,
} from './SessionHistory'

/**
 * Maps normalized API error kind to distinct user-facing guidance.
 * Prioritizes actionable backend detail (e.g. missing API keys or initialization status).
 */
function getErrorExplanation(normalized) {
  if (!normalized) return 'Something went wrong. Please try again.'

  if (normalized.detail && typeof normalized.detail === 'string') {
    return normalized.detail
  }

  switch (normalized.kind) {
    case 'network':
      return "Could not connect to the Standardify backend. Please ensure the backend server is running on http://127.0.0.1:8000."
    case 'timeout':
      return 'The request timed out. On the very first run, the local BGE-M3 model downloads/initializes in memory (~1.1 GB). Please try again once initialized.'
    case 'validation':
      return normalized.detail || 'Please check your question syntax and try again.'
    case 'rate_limited':
      return 'Rate limit reached (60 req/min). Please wait for the cooldown before asking again.'
    case 'unavailable':
      return normalized.detail || normalized.message || 'AI inference is currently unavailable. Standards Search, Registry, Gap Checker, and Graph remain available offline.'
    default:
      return normalized.detail || normalized.message || 'Something went wrong on our end. Please try again.'
  }
}

/**
 * Standardify Primary AI Grounded Q&A Workspace.
 * Hardened in Phase 8 with 429 cooldown timer, race condition protection, and clean error states.
 */
export function AskExperience() {
  const [searchParams] = useSearchParams()
  const initialQ = (searchParams.get('q') || searchParams.get('question') || '').trim()

  const [question, setQuestion] = useState(initialQ)
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)
  const [blockingError, setBlockingError] = useState(null)
  const [errorRequestId, setErrorRequestId] = useState(undefined)
  const [sessionHistory, setSessionHistory] = useState(() => loadSessionHistory())

  const inputRef = useRef(null)
  const hasAutoRunRef = useRef(false)
  const isRequestInFlightRef = useRef(false)
  const { showToast } = useToast()
  const { isCoolingDown, cooldownRemaining, triggerCooldown } = useRateLimitCooldown(10)

  // Global "/" keyboard shortcut focuses the Ask input
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key !== '/') return
      const active = document.activeElement
      const isTyping =
        active instanceof HTMLElement &&
        (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)
      if (isTyping) return
      e.preventDefault()
      inputRef.current?.focus()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  // Execute Grounded Ask Request
  const runAsk = useCallback(
    async (questionText) => {
      const trimmed = questionText.trim()
      if (!trimmed || isRequestInFlightRef.current || isCoolingDown) return

      isRequestInFlightRef.current = true
      setLoading(true)
      setBlockingError(null)
      setErrorRequestId(undefined)
      setResponse(null)

      try {
        const result = await askQuestion(trimmed)
        setResponse(result)

        // Save successful query to sessionStorage
        saveToSessionHistory(trimmed, result)
        setSessionHistory(loadSessionHistory())
      } catch (err) {
        const normalized = normalizeApiError(err)
        setErrorRequestId(normalized.requestId)

        if (normalized.kind === 'rate_limited') {
          triggerCooldown(10)
        }

        const explanation = getErrorExplanation(normalized)

        if (normalized.kind === 'validation' || normalized.kind === 'rate_limited' || normalized.kind === 'unavailable') {
          setBlockingError(explanation)
        } else {
          showToast(explanation, 'error')
          setBlockingError(explanation)
        }
      } finally {
        isRequestInFlightRef.current = false
        setLoading(false)
      }
    },
    [isCoolingDown, triggerCooldown, showToast]
  )

  // Auto-run if query param is present on mount (Bridge from Standard Detail)
  useEffect(() => {
    if (initialQ && !hasAutoRunRef.current) {
      hasAutoRunRef.current = true
      setQuestion(initialQ)
      runAsk(initialQ)
    }
  }, [initialQ, runAsk])

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    runAsk(question)
  }

  const handleExampleSelect = (prompt) => {
    setQuestion(prompt)
    inputRef.current?.focus()
    runAsk(prompt)
  }

  // Restore previous inquiry from session history (Zero network call)
  const handleRestoreSessionEntry = ({ question: savedQ, response: savedResp }) => {
    setQuestion(savedQ)
    setResponse(savedResp)
    setBlockingError(null)
    setErrorRequestId(undefined)
    showToast('Restored previous answer from this session.', 'success')
  }

  const handleClearHistory = () => {
    clearSessionHistory()
    setSessionHistory([])
    showToast('Session inquiries cleared.', 'success')
  }

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6">
      {/* Rate limit cooldown notice */}
      {isCoolingDown && (
        <div
          className="flex items-center gap-2 rounded-[var(--radius-md)] border border-amber-300 bg-amber-50 p-3 text-xs text-warning"
          role="status"
          aria-live="polite"
        >
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          <span>
            Rate limit active. Please wait{' '}
            <strong className="font-technical font-bold">{cooldownRemaining}s</strong> before submitting another question.
          </span>
        </div>
      )}

      {/* Ask Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-2.5 sm:flex-row sm:gap-3"
        aria-label="Ask Standardify a grounded question"
      >
        <label htmlFor="ask-input" className="sr-only">
          Ask a question about an Indian Standard
        </label>
        <div className="relative flex-1">
          <Input
            id="ask-input"
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading || isCoolingDown}
            placeholder="e.g. Which standard applies to ceiling fans?"
            className="h-13 sm:h-14 pr-12 text-base shadow-2xs border-border/85 bg-surface text-text placeholder:text-text-muted/75 transition-all duration-150 focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
            autoComplete="off"
          />
          {!question && !isCoolingDown && (
            <kbd
              className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 rounded border border-border/80 bg-bg px-2 py-0.5 font-technical text-[11px] font-semibold text-text-muted"
              aria-hidden="true"
            >
              /
            </kbd>
          )}
        </div>
        <Button
          type="submit"
          size="lg"
          loading={loading}
          disabled={!question.trim() || isCoolingDown}
          className="h-13 sm:h-14 shrink-0 px-7 font-semibold shadow-2xs transition-all duration-150"
        >
          {!loading && (
            <>
              {isCoolingDown ? `Wait (${cooldownRemaining}s)` : 'Ask'}
              {!isCoolingDown && <ArrowRight className="h-4 w-4" aria-hidden="true" />}
            </>
          )}
        </Button>
      </form>

      {/* Example Prompt Chips */}
      <div>
        <ExamplePrompts onSelect={handleExampleSelect} disabled={loading} />
      </div>

      {/* Blocking Error View */}
      {blockingError && !loading && !response && (
        <ErrorState
          message={blockingError}
          requestId={errorRequestId}
          onRetry={() => runAsk(question)}
        />
      )}

      {/* Answer Panel View (includes loading skeleton, warnings, multi-standard citations) */}
      <AnswerPanel loading={loading} response={response} />

      {/* Session History (Scoped to sessionStorage) */}
      {!loading && sessionHistory.length > 0 && (
        <div className="pt-2">
          <SessionHistory
            history={sessionHistory}
            onSelect={handleRestoreSessionEntry}
            onClear={handleClearHistory}
            activeQuestion={question}
          />
        </div>
      )}
    </div>
  )
}

export default AskExperience
