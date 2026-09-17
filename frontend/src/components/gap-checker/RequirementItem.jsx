import { Link } from 'react-router-dom'
import { AlertCircle, ArrowUpRight, CheckCircle2, FileText } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { cn } from '../../lib/utils'

/**
 * Safely parses requirement strings formatted like:
 * "[IS 9001:2025 Clause 4.1] Plastic containers shall be made from..."
 *
 * Falls back gracefully to raw text if the format does not match.
 *
 * @param {string} rawString
 * @returns {{ badgeText: string | null, standardNo: string | null, clauseNo: string | null, bodyText: string }}
 */
function parseRequirement(rawString) {
  if (typeof rawString !== 'string') {
    return { badgeText: null, standardNo: null, clauseNo: null, bodyText: String(rawString || '') }
  }

  const trimmed = rawString.trim()
  const match = trimmed.match(/^\[([^\]]+)\]\s*(.*)$/)

  if (!match) {
    return { badgeText: null, standardNo: null, clauseNo: null, bodyText: trimmed }
  }

  const badgeText = match[1].trim()
  const bodyText = match[2].trim()

  // Attempt to isolate standard number (e.g. "IS 9001:2025" from "IS 9001:2025 Clause 4.1")
  let standardNo = null
  let clauseNo = null

  const clauseMatch = badgeText.match(/^(IS\s*[^:]+:\d+|IS\s*\d+)\s*(?:Clause\s*(.*))?$/i)
  if (clauseMatch) {
    standardNo = clauseMatch[1].trim()
    clauseNo = clauseMatch[2]?.trim() || null
  } else if (badgeText.toUpperCase().startsWith('IS ')) {
    standardNo = badgeText.split(/\s+Clause\s+/i)[0].trim()
  }

  return { badgeText, standardNo, clauseNo, bodyText: bodyText || trimmed }
}

/**
 * @param {{
 *   rawText: string,
 *   type: 'matched' | 'missing',
 *   className?: string,
 * }} props
 */
export function RequirementItem({ rawText, type = 'matched', className }) {
  const isMatched = type === 'matched'
  const { badgeText, standardNo, bodyText } = parseRequirement(rawText)

  return (
    <div
      className={cn(
        'group flex flex-col sm:flex-row sm:items-start justify-between gap-3.5 rounded-[var(--radius-md)] border p-4 text-left transition-colors',
        isMatched
          ? 'border-green-200 bg-green-50/40 hover:bg-green-50/70'
          : 'border-amber-200 bg-amber-50/40 hover:bg-amber-50/70',
        className
      )}
    >
      <div className="flex items-start gap-3 flex-1 min-w-0">
        {/* Status Indicator Icon */}
        <div className="mt-0.5 shrink-0">
          {isMatched ? (
            <CheckCircle2 className="h-5 w-5 text-success" aria-hidden="true" />
          ) : (
            <AlertCircle className="h-5 w-5 text-warning" aria-hidden="true" />
          )}
        </div>

        {/* Content Area */}
        <div className="space-y-1.5 flex-1 min-w-0">
          {/* Badge & Standard Link (if successfully parsed) */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={isMatched ? 'success' : 'warning'}>
              {isMatched ? 'Satisfied in Spec' : 'Unaddressed in Spec'}
            </Badge>

            {badgeText && (
              <span className="font-technical text-xs font-semibold text-text">
                {standardNo ? (
                  <Link
                    to={`/standards/${encodeURIComponent(standardNo)}`}
                    className="text-primary hover:underline"
                    title={`View standard details for ${standardNo}`}
                  >
                    {badgeText}
                  </Link>
                ) : (
                  badgeText
                )}
              </span>
            )}
          </div>

          {/* Requirement Body Description */}
          <p className="text-sm leading-relaxed text-text">
            {bodyText}
          </p>
        </div>
      </div>

      {/* Action Links if standard parsed */}
      {standardNo && (
        <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-end sm:self-start pt-1 text-xs">
          <Link
            to={`/standards/${encodeURIComponent(standardNo)}`}
            className="flex items-center gap-1 font-medium text-primary hover:text-primary-dark"
            title={`View full standard details for ${standardNo}`}
          >
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Details</span>
          </Link>

          <Link
            to={`/?q=${encodeURIComponent(`What does ${standardNo} require regarding ${bodyText.slice(0, 60)}?`)}`}
            className="flex items-center gap-1 font-medium text-text-muted hover:text-text"
            title={`Ask AI about ${standardNo} requirement`}
          >
            <span>Ask AI</span>
            <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
          </Link>

          <Link
            to={`/graph?focus=${encodeURIComponent(standardNo)}`}
            className="flex items-center gap-1 font-medium text-text-muted hover:text-text"
            title={`Explore relationship graph for ${standardNo}`}
          >
            <span>Graph</span>
            <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
          </Link>
        </div>
      )}
    </div>
  )
}
