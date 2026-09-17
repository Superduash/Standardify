import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Reusable client-side rate-limit countdown hook (Phase 8 §7).
 * When a 429 response is encountered, triggers a visible countdown timer
 * and temporarily disables submission, automatically re-enabling when done.
 *
 * @param {number} defaultSeconds - Default cooldown duration in seconds
 * @returns {{
 *   isCoolingDown: boolean,
 *   cooldownRemaining: number,
 *   triggerCooldown: (seconds?: number) => void,
 *   resetCooldown: () => void,
 * }}
 */
export function useRateLimitCooldown(defaultSeconds = 10) {
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const timerRef = useRef(null)

  const triggerCooldown = useCallback((seconds = defaultSeconds) => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }

    setCooldownRemaining(seconds)

    timerRef.current = setInterval(() => {
      setCooldownRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current)
          timerRef.current = null
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [defaultSeconds])

  const resetCooldown = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setCooldownRemaining(0)
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  return {
    isCoolingDown: cooldownRemaining > 0,
    cooldownRemaining,
    triggerCooldown,
    resetCooldown,
  }
}

export default useRateLimitCooldown
