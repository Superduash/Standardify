import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BookOpen,
  Eye,
  GitFork,
  MessageSquareText,
  Target,
  X,
} from 'lucide-react'
import { StatusBadge } from '../ui/StatusBadge'
import { Badge } from '../ui/Badge'
import { Button, buttonClasses } from '../ui/Button'
import { cn } from '../../lib/utils'

/**
 * Extract connected edges and neighbor nodes for a specific node.
 *
 * @param {import('../../api/types').GraphNode} node
 * @param {import('../../api/types').GraphEdge[]} edges
 * @param {Map<string, import('../../api/types').GraphNode>} nodesMap
 */
function getConnectedNeighbors(node, edges = [], nodesMap = new Map()) {
  if (!node || !node.id) return []

  const nodeId = node.id.trim()
  const results = []
  const seen = new Set()

  edges.forEach((edge) => {
    if (!edge || !edge.source || !edge.target) return
    const source = typeof edge.source === 'object' ? edge.source.id : edge.source
    const target = typeof edge.target === 'object' ? edge.target.id : edge.target
    const relation = edge.relation || 'references'

    let neighborId = null
    let displayRelation = relation

    if (source === nodeId) {
      neighborId = target
      displayRelation = relation
    } else if (target === nodeId) {
      neighborId = source
      if (relation === 'supersedes') displayRelation = 'superseded_by'
      else if (relation === 'references') displayRelation = 'referenced_by'
      else displayRelation = relation
    }

    if (neighborId && !seen.has(`${neighborId}-${displayRelation}`)) {
      seen.add(`${neighborId}-${displayRelation}`)
      const neighborNode = nodesMap.get(neighborId) || { id: neighborId, label: neighborId }
      results.push({
        id: neighborId,
        label: neighborNode.label || neighborNode.title || neighborId,
        status: neighborNode.status,
        relation: displayRelation,
      })
    }
  })

  return results
}

/**
 * Contextual inspection panel for the currently selected graph node.
 *
 * @param {{
 *   node: import('../../api/types').GraphNode | null,
 *   focusedStandardNo?: string | null,
 *   edges?: import('../../api/types').GraphEdge[],
 *   nodesMap?: Map<string, import('../../api/types').GraphNode>,
 *   onClose: () => void,
 *   onFocusNode: (standardNo: string) => void,
 *   className?: string,
 * }} props
 */
export function GraphNodePanel({
  node,
  focusedStandardNo,
  edges = [],
  nodesMap = new Map(),
  onClose,
  onFocusNode,
  className,
}) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!node) return null

  const isFocused = Boolean(focusedStandardNo && focusedStandardNo === node.id)
  const neighbors = getConnectedNeighbors(node, edges, nodesMap)

  return (
    <div
      role="region"
      aria-label={`Node details for ${node.id}`}
      className={cn(
        'rounded-[var(--radius-lg)] border border-border bg-surface/95 p-5 shadow-xl backdrop-blur-xs space-y-4 text-left animate-panel-in transition-all duration-150',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-border/60 pb-3">
        <div className="space-y-1 min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-technical text-lg font-bold text-primary">
              {node.id}
            </h3>
            {node.status && <StatusBadge status={node.status} />}
            {isFocused && (
              <Badge tone="primary">Current Focus</Badge>
            )}
          </div>
          {node.label && node.label !== node.id && (
            <p className="text-xs text-text-body font-medium leading-snug line-clamp-2">
              {node.label}
            </p>
          )}
          {node.category && (
            <Badge tone="neutral" className="mt-1">
              <BookOpen className="h-3 w-3 text-text-muted" aria-hidden="true" />
              {node.category}
            </Badge>
          )}
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-text-muted hover:bg-bg hover:text-text shrink-0"
          aria-label="Close node panel"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {/* Connected Relationships in currently loaded graph */}
      <div className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-text">
          <GitFork className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
          <span>Direct Connections ({neighbors.length})</span>
        </div>

        {neighbors.length > 0 ? (
          <ul className="max-h-40 overflow-y-auto space-y-1.5 text-xs">
            {neighbors.map((n) => (
              <li
                key={`${n.id}-${n.relation}`}
                className="flex items-center justify-between gap-2 rounded-[var(--radius-sm)] border border-border/60 bg-bg px-2.5 py-1.5"
              >
                <div className="min-w-0 flex items-center gap-2">
                  <span className="font-technical font-semibold text-primary">
                    {n.id}
                  </span>
                  <span className="text-[10px] uppercase font-semibold text-text-muted">
                    ({n.relation})
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => onFocusNode(n.id)}
                  className="font-technical text-[10px] text-primary hover:underline shrink-0"
                  title={`Focus graph on ${n.id}`}
                >
                  Focus →
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-text-muted italic">
            No connected edges in the current graph slice.
          </p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="space-y-2 border-t border-border/60 pt-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <Link
            to={`/standards/${encodeURIComponent(node.id)}`}
            className={buttonClasses({
              variant: 'primary',
              size: 'sm',
              className: 'justify-center text-xs',
            })}
          >
            <Eye className="h-3.5 w-3.5" aria-hidden="true" />
            Standard Details
          </Link>

          {!isFocused ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onFocusNode(node.id)}
              className="justify-center text-xs"
            >
              <Target className="h-3.5 w-3.5" aria-hidden="true" />
              Focus Graph
            </Button>
          ) : (
            <Link
              to={`/standards?q=${encodeURIComponent(node.id)}`}
              className={buttonClasses({
                variant: 'secondary',
                size: 'sm',
                className: 'justify-center text-xs',
              })}
            >
              <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
              Search Repository
            </Link>
          )}
        </div>

        <Link
          to={`/?q=${encodeURIComponent(`What does ${node.id} require?`)}`}
          className={buttonClasses({
            variant: 'ghost',
            size: 'sm',
            className: 'w-full justify-center text-xs text-text-body hover:text-primary',
          })}
        >
          <MessageSquareText className="h-3.5 w-3.5" aria-hidden="true" />
          Ask AI about {node.id}
          <ArrowRight className="h-3 w-3" aria-hidden="true" />
        </Link>
      </div>
    </div>
  )
}
