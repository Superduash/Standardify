import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { askQuestion } from '../../api/endpoints'
import { normalizeApiError } from '../../api/client'
import { useToast } from '../../context/ToastContext'
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
 * Per Phase 3 requirement §9.
 */
function getErrorExplanation(normalized) {
  if (!normalized) return 'Something went wrong. Please try again.'

  switch (normalized.kind) {
    case 'network':
      return "We couldn't reach the assistant. Check your connection and try again."
    case 'timeout':
      return 'The request took too long to process. Please try again.'
    case 'validation':
      return normalized.detail || 'Please check your question and try again.'
    case 'rate_limited':
      return 'The assistant is temporarily rate-limited. Standardify enforces a rate limit of 60 requests per minute per client. Please wait a moment and try again.'
    case 'unavailable':
      return 'The assistant is temporarily unavailable. Please try again shortly.'
    default:
      return normalized.message || 'Something went wrong on our end. Please try again.'
  }
}

/**
 * Standardify Primary AI Grounded Q&A Workspace.
 * Elevated in Phase 3 with session history, interactive citations, and multi-standard presentation.
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
  const { showToast } = useToast()


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
      if (!trimmed || loading) return

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

        const explanation = getErrorExplanation(normalized)

        if (normalized.kind === 'validation' || normalized.kind === 'rate_limited' || normalized.kind === 'unavailable') {
          setBlockingError(explanation)
        } else {
          showToast(explanation, 'error')
          setBlockingError(explanation)
        }
      } finally {
        setLoading(false)
      }
    },
    [loading, showToast]
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
      {/* Ask Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-3 sm:flex-row"
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
            placeholder="e.g. Which standard applies to ceiling fans?"
            className="h-14 pr-12 text-base shadow-xs"
            autoComplete="off"
          />
          {!question && (
            <kbd
              className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 rounded border border-border bg-bg px-1.5 py-0.5 font-technical text-[11px] text-text-muted"
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
          disabled={!question.trim()}
          className="h-14 shrink-0 px-6 font-semibold"
        >
          {!loading && (
            <>
              Ask
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
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
