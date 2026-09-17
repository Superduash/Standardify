import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * RouteFocusManager handles application-level focus and scroll restoration on route navigation.
 *
 * Requirements (Phase 7 §3):
 * 1. Scrolls to top of the page on route transition.
 * 2. Shifts focus to the primary <h1> on the new page with tabIndex={-1} so screen readers
 *    announce the new context without cluttering regular tab order.
 * 3. Does not steal focus if an active modal/dialog is present.
 */
export function RouteFocusManager() {
  const { pathname, search } = useLocation()

  useEffect(() => {
    // Scroll window to top
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })

    // If an open modal or dialog is already managing focus, don't steal it
    const hasOpenModal = document.querySelector('[role="dialog"][aria-modal="true"]')
    if (hasOpenModal) return

    // Find main page heading
    const timer = setTimeout(() => {
      const heading = document.querySelector('main h1, h1, [role="main"] h1')
      if (heading instanceof HTMLElement) {
        if (!heading.hasAttribute('tabindex')) {
          heading.setAttribute('tabindex', '-1')
        }
        heading.focus({ preventScroll: true })
      }
    }, 50)

    return () => clearTimeout(timer)
  }, [pathname, search])

  return null
}

export default RouteFocusManager
