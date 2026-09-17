import { useState } from 'react'
import { ChevronDown, ChevronUp, Info } from 'lucide-react'
import { cn } from '../../lib/utils'

export const STATUS_COLORS = {
  active: { bg: '#177245', text: 'text-success', label: 'Active' },
  superseded: { bg: '#A15C00', text: 'text-warning', label: 'Superseded' },
  withdrawn: { bg: '#C62828', text: 'text-danger', label: 'Withdrawn' },
  'under revision': { bg: '#A15C00', text: 'text-warning', label: 'Under Revision' },
}

export const RELATION_COLORS = {
  references: { color: '#264796', label: 'References', style: 'solid' },
  supersedes: { color: '#A15C00', label: 'Supersedes', style: 'solid' },
  same_category: { color: '#147D76', label: 'Same Category', style: 'dashed' },
}

/**
 * Standardify Graph Visual Legend.
 * Explains node lifecycle status colors and edge relationship types.
 *
 * @param {{ className?: string }} props
 */
export function GraphLegend({ className }) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div
      className={cn(
        'rounded-[var(--radius-md)] border border-border bg-surface/95 p-3 text-xs shadow-md backdrop-blur-xs transition-all',
        className
      )}
      role="region"
      aria-label="Standards graph color and relationship legend"
    >
      <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-2">
        <div className="flex items-center gap-1.5 font-semibold text-text">
          <Info className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
          <span>Graph Legend</span>
        </div>
        <button
          type="button"
          onClick={() => setIsCollapsed((prev) => !prev)}
          className="rounded p-0.5 text-text-muted hover:bg-bg hover:text-text"
          aria-expanded={!isCollapsed}
          aria-label={isCollapsed ? 'Expand graph legend' : 'Collapse graph legend'}
        >
          {isCollapsed ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="pt-2 space-y-3">
          {/* Node Statuses */}
          <div className="space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Node Status
            </span>
            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#177245] shrink-0" />
                <span className="text-text">Active</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#A15C00] shrink-0" />
                <span className="text-text">Superseded</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#C62828] shrink-0" />
                <span className="text-text">Withdrawn</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#A15C00] shrink-0" />
                <span className="text-text">Under Revision</span>
              </div>
            </div>
          </div>

          {/* Edge Relations */}
          <div className="space-y-1.5 border-t border-border/50 pt-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Relationship Type
            </span>
            <div className="space-y-1 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-[#264796] shrink-0" />
                <span className="text-text">References</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-0.5 w-4 bg-[#A15C00] shrink-0" />
                <span className="text-text">Supersedes</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-0.5 w-4 border-b border-dashed border-[#147D76] shrink-0" />
                <span className="text-text">Same Category</span>
              </div>
            </div>
          </div>

          {/* Focused Node Indicator */}
          <div className="border-t border-border/50 pt-1.5 text-[10px] text-text-muted flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-full border-2 border-primary bg-primary-light shrink-0" />
            <span>Double ring indicates currently focused standard</span>
          </div>
        </div>
      )}
    </div>
  )
}
