import { createContext, useCallback, useContext, useRef, useState } from 'react'

/**
 * @typedef {Object} ToastItem
 * @property {string} id
 * @property {"info"|"success"|"error"|"warning"} variant
 * @property {string} message
 */

const ToastContext = createContext(/** @type {{
  toasts: ToastItem[],
  showToast: (message: string, variant?: ToastItem['variant']) => void,
  dismissToast: (id: string) => void,
} | null} */ (null))

const AUTO_DISMISS_MS = 5000

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState(/** @type {ToastItem[]} */ ([]))
  const timers = useRef(/** @type {Record<string, ReturnType<typeof setTimeout>>} */ ({}))

  const dismissToast = useCallback((id) => {
    setToasts((current) => current.filter((t) => t.id !== id))
    if (timers.current[id]) {
      clearTimeout(timers.current[id])
      delete timers.current[id]
    }
  }, [])

  const showToast = useCallback(
    (message, variant = 'info') => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
      setToasts((current) => [...current, { id, message, variant }])
      timers.current[id] = setTimeout(() => dismissToast(id), AUTO_DISMISS_MS)
    },
    [dismissToast]
  )

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within a ToastProvider')
  return ctx
}
