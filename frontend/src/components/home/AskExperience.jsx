import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { askQuestion } from '../../api/endpoints'
import { normalizeApiError } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { ErrorState } from '../ui/ErrorState'
import { ExamplePrompts } from './ExamplePrompts'
import { AnswerPanel } from './AnswerPanel'

/**
 * Owns all state for the Home page's core Ask interaction: the question
 * text, the in-flight request, and the resulting answer/error. Nothing
 * outside this component needs that state, so it isn't lifted any higher
 * (see frontendplan.md §4).
 */
export function AskExperience() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(/** @type {import('../../api/types').AskResponse | null} */ (null))
  const [blockingError, setBlockingError] = useState(/** @type {string | null} */ (null))
  const [errorRequestId, setErrorRequestId] = useState(/** @type {string | undefined} */ (undefined))
  const inputRef = useRef(/** @type {HTMLInputElement | null} */ (null))
  const { showToast } = useToast()

  // Global "/" focuses the Ask input, unless the user is already typing
  // somewhere else — a small, real keyboard-accessibility affordance.
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
      } catch (err) {
        const normalized = normalizeApiError(err)
        setErrorRequestId(normalized.requestId)
        if (normalized.kind === 'validation') {
          // The question itself was rejected — block the answer area so the
          // user knows to fix their input.
          setBlockingError(normalized.message)
        } else {
          // Transient error (network/429/503/timeout) — toast only; the form
          // stays visible and usable. Don't also set blockingError so we don't
          // show the same message twice (frontendplan.md §6).
          showToast(normalized.message, 'error')
        }
      } finally {
        setLoading(false)
      }
    },
    [loading, showToast]
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    runAsk(question)
  }

  const handleExampleSelect = (prompt) => {
    setQuestion(prompt)
    inputRef.current?.focus()
    runAsk(prompt)
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row" aria-label="Ask Standardify a question">
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
            className="h-14 pr-12 text-base"
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
        <Button type="submit" size="lg" loading={loading} disabled={!question.trim()} className="h-14 shrink-0">
          {!loading && (
            <>
              Ask
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </>
          )}
        </Button>
      </form>

      <div className="mt-4">
        <ExamplePrompts onSelect={handleExampleSelect} disabled={loading} />
      </div>

      <div className="mt-6">
        {blockingError && !loading && !response && (
          <ErrorState message={blockingError} requestId={errorRequestId} onRetry={() => runAsk(question)} />
        )}
        <AnswerPanel loading={loading} response={response} />
      </div>
    </div>
  )
}
