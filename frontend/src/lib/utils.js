import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge conditional class names and resolve Tailwind conflicts sanely.
 * Standard `clsx` + `tailwind-merge` pairing — avoids hand-rolling this.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/** Format a 0-1 confidence value as a whole-number percentage string. */
export function formatConfidence(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—'
  return `${Math.round(value * 100)}%`
}

/** Format milliseconds as a short human string, e.g. "420ms" or "1.8s". */
export function formatLatency(ms) {
  if (typeof ms !== 'number' || Number.isNaN(ms)) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
