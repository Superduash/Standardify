import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, ExternalLink, GitFork, Network, Search, Target } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { StatusBadge } from '../ui/StatusBadge'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'


const RELATION_BADGE = {
  references: { label: 'References', tone: 'primary' },
  supersedes: { label: 'Supersedes', tone: 'warning' },
  same_category: { label: 'Same Category', tone: 'teal' },
}

/**
 * Screen-reader friendly, keyboard-operable semantic list equivalent
 * of the currently loaded Graph nodes and edges.
 *
 * @param {{
 *   nodes: import('../../api/types').GraphNode[],
 *   edges: import('../../api/types').GraphEdge[],
 *   focusedStandardNo?: string | null,
 *   onFocusNode: (standardNo: string) => void,
 *   className?: string,
 * }} props
 */
export function GraphAccessibleListView({
  nodes = [],
  edges = [],
  focusedStandardNo,
  onFocusNode,
  className,
}) {
  const [filterQuery, setFilterQuery] = useState('')

  const filteredNodes = nodes.filter((n) => {
    if (!filterQuery.trim()) return true
    const q = filterQuery.toLowerCase()
    return (
      (n.id && n.id.toLowerCase().includes(q)) ||
      (n.label && n.label.toLowerCase().includes(q)) ||
      (n.category && n.category.toLowerCase().includes(q)) ||
      (n.status && n.status.toLowerCase().includes(q))
    )
  })

  return (
    <div className={cn('space-y-6 text-left', className)} role="region" aria-label="Standards network accessible data view">
      {/* Search filter for accessible list */}
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-text-muted">
          <Search className="h-4 w-4" aria-hidden="true" />
        </div>
        <input
          type="text"
          value={filterQuery}
          onChange={(e) => setFilterQuery(e.target.value)}
          placeholder="Filter standards list by number, title, or category..."
          className="h-10 w-full rounded-[var(--radius-md)] border border-border bg-surface pl-9 pr-4 text-xs text-text placeholder:text-text-muted transition-colors focus-visible:border-primary"
          aria-label="Filter accessible graph list"
        />
      </div>

      {/* 1. Standards (Nodes) Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
            <Network className="h-4 w-4 text-primary" aria-hidden="true" />
            Standards in Current Graph ({filteredNodes.length})
          </h2>
          <span className="text-xs text-text-muted">
            {nodes.length} total indexed
          </span>
        </div>

        <ul className="divide-y divide-border/60 rounded-[var(--radius-lg)] border border-border bg-surface shadow-[var(--shadow-card)]">
          {filteredNodes.map((node) => {
            const isFocused = Boolean(focusedStandardNo && focusedStandardNo === node.id)

            return (
              <li
                key={node.id}
                className={cn(
                  'flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 transition-colors',
                  isFocused ? 'bg-primary-light/30' : 'hover:bg-bg'
                )}
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/standards/${encodeURIComponent(node.id)}`}
                      className="font-technical text-sm font-bold text-primary hover:underline"
                    >
                      {node.id}
                    </Link>
                    {node.status && <StatusBadge status={node.status} />}
                    {isFocused && <Badge tone="primary">Focused</Badge>}
                    {node.category && (
                      <Badge tone="neutral">
                        <BookOpen className="h-3 w-3 text-text-muted" aria-hidden="true" />
                        {node.category}
                      </Badge>
                    )}
                  </div>

                  {node.label && node.label !== node.id && (
                    <p className="text-xs text-text-body leading-relaxed">{node.label}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center pt-1 sm:pt-0">
                  <Link
                    to={`/standards/${encodeURIComponent(node.id)}`}
                    className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-dark"
                  >
                    Details
                    <ExternalLink className="h-3 w-3" aria-hidden="true" />
                  </Link>

                  {!isFocused && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onFocusNode(node.id)}
                      className="h-7 px-2.5 text-xs"
                    >
                      <Target className="h-3 w-3" aria-hidden="true" />
                      Focus
                    </Button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      </div>

      {/* 2. Relationships (Edges) Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
            <GitFork className="h-4 w-4 text-primary" aria-hidden="true" />
            Inter-Standard Relationships ({edges.length})
          </h2>
        </div>

        {edges.length > 0 ? (
          <ul className="divide-y divide-border/60 rounded-[var(--radius-lg)] border border-border bg-surface shadow-[var(--shadow-card)]">
            {edges.map((edge, i) => {
              const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source
              const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target
              const relation = edge.relation || 'references'
              const relConfig = RELATION_BADGE[relation] || { label: relation, tone: 'neutral' }

              return (
                <li
                  key={`${sourceId}-${targetId}-${relation}-${i}`}
                  className="flex flex-wrap items-center justify-between gap-3 p-3.5 text-xs hover:bg-bg transition-colors"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/standards/${encodeURIComponent(sourceId)}`}
                      className="font-technical font-semibold text-primary hover:underline"
                    >
                      {sourceId}
                    </Link>

                    <span className="text-text-muted">──</span>
                    <Badge tone={relConfig.tone}>{relConfig.label}</Badge>
                    <span className="text-text-muted">──▶</span>

                    <Link
                      to={`/standards/${encodeURIComponent(targetId)}`}
                      className="font-technical font-semibold text-primary hover:underline"
                    >
                      {targetId}
                    </Link>
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-text-muted">
                    <button
                      type="button"
                      onClick={() => onFocusNode(sourceId)}
                      className="hover:text-primary hover:underline"
                    >
                      Focus source
                    </button>
                    <span>·</span>
                    <button
                      type="button"
                      onClick={() => onFocusNode(targetId)}
                      className="hover:text-primary hover:underline"
                    >
                      Focus target
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="text-xs text-text-muted italic">
            No relationship edges in the loaded data slice.
          </p>
        )}
      </div>
    </div>
  )
}
