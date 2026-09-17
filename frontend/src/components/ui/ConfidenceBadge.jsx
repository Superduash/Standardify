import { Badge } from './Badge'
import { formatConfidence } from '../../lib/utils'

const LABEL_TONE = {
  high: 'success',
  medium: 'warning',
  low: 'danger',
}

const LABEL_TEXT = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
}

/**
 * @param {{ label: 'high'|'medium'|'low', value?: number }} props
 */
export function ConfidenceBadge({ label, value }) {
  const tone = LABEL_TONE[label] ?? 'neutral'
  const text = LABEL_TEXT[label] ?? 'Unknown confidence'

  return (
    <Badge tone={tone}>
      {text}
      {typeof value === 'number' && (
        <span className="font-technical opacity-80">· {formatConfidence(value)}</span>
      )}
    </Badge>
  )
}
