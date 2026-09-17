import { Badge } from './Badge'

/**
 * Status vocabulary is Title Case, per FRONTEND_CONTRACT.md §3.7 —
 * "Active" | "Superseded" | "Withdrawn" | "Under Revision". Matched
 * case-insensitively here so a stray casing difference never falls through
 * to the unstyled fallback.
 */
const STATUS_CONFIG = {
  active: { tone: 'success', text: 'ACTIVE' },
  superseded: { tone: 'warning', text: 'SUPERSEDED' },
  withdrawn: { tone: 'danger', text: 'WITHDRAWN' },
  'under revision': { tone: 'warning', text: 'UNDER REVISION' },
}

/**
 * @param {{ status: import('../../api/types').StandardStatus | string }} props
 */
export function StatusBadge({ status }) {
  const key = (status || '').toLowerCase()
  const config = STATUS_CONFIG[key] ?? { tone: 'neutral', text: (status || 'UNKNOWN').toUpperCase() }
  return (
    <Badge tone={config.tone} mono>
      {config.text}
    </Badge>
  )
}
