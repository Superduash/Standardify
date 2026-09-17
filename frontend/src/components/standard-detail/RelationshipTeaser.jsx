import { Link } from 'react-router-dom'
import { ArrowUpRight, GitFork, Network, RotateCw } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { StatusBadge } from '../ui/StatusBadge'
import { Skeleton } from '../ui/Skeleton'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

const RELATION_CONFIG = {
  supersedes: { label: 'Supersedes', tone: 'warning' },
  superseded_by: { label: 'Superseded by', tone: 'warning' },
  references: { label: 'References', tone: 'primary' },
  referenced_by: { label: 'Referenced by', tone: 'teal' },
  same_category: { label: 'Same Category', tone: 'neutral' },
}

/**
 * Parses depth=1 neighborhood graph into a flat list of related standards.
 *
 * @param {import('../../api/types').GraphResponse} graphData
 * @param {string} currentStandardNo
 */
function extractRelationships(graphData, currentStandardNo) {
  if (!graphData || !Array.isArray(graphData.nodes) || !Array.isArray(graphData.edges)) {
    return []
  }

  const nodesById = new Map()
  graphData.nodes.forEach((n) => {
    if (n && n.id) {
      nodesById.set(n.id.trim(), n)
    }
  })

  const currentKey = (currentStandardNo || '').trim()
  const results = []
  const seen = new Set()

  graphData.edges.forEach((edge) => {
    if (!edge || !edge.source || !edge.target) return

    const source = edge.source.trim()
    const target = edge.target.trim()
    const relation = edge.relation || 'references'

    let relatedId = null
    let displayRelation = relation

    if (source === currentKey) {
      relatedId = target
      displayRelation = relation
    } else if (target === currentKey) {
      relatedId = source
      if (relation === 'supersedes') displayRelation = 'superseded_by'
      else if (relation === 'references') displayRelation = 'referenced_by'
      else displayRelation = relation
    }

    if (relatedId && relatedId !== currentKey && !seen.has(`${relatedId}-${displayRelation}`)) {
      seen.add(`${relatedId}-${displayRelation}`)
      const nodeInfo = nodesById.get(relatedId) || { id: relatedId, label: relatedId }
      results.push({
        id: relatedId,
        title: nodeInfo.label || nodeInfo.title || relatedId,
        status: nodeInfo.status,
        category: nodeInfo.category,
        relation: displayRelation,
      })
    }
  })

  return results
}

/**
 * @param {{
 *   graphData: import('../../api/types').GraphResponse | null,
 *   standardNo: string,
 *   loading?: boolean,
 *   error?: import('../../api/client').NormalizedApiError | null,
 *   onRetry?: () => void,
 *   className?: string,
 * }} props
 */
export function RelationshipTeaser({
  graphData,
  standardNo,
  loading = false,
  error = null,
  onRetry,
  className,
}) {
  const relationships = extractRelationships(graphData, standardNo)

  return (
    <Card className={cn('space-y-4', className)}>
      <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-0">
        <div>
          <div className="flex items-center gap-2">
            <GitFork className="h-4 w-4 text-primary" aria-hidden="true" />
            <CardTitle>Related Standards (1-Hop Subgraph)</CardTitle>
          </div>
          <CardDescription>
            Standards that reference, supersede, or share a domain with {standardNo}.
          </CardDescription>
        </div>

        <Link
          to={`/graph?focus=${encodeURIComponent(standardNo)}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:text-primary-dark shrink-0"
        >
          <Network className="h-3.5 w-3.5" aria-hidden="true" />
          View full graph
          <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
        </Link>
      </CardHeader>

      {/* Loading state */}
      {loading && (
        <div className="space-y-2.5 pt-2" role="status" aria-label="Loading related standards">
          <Skeleton className="h-14 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-14 w-full rounded-[var(--radius-md)]" />
          <Skeleton className="h-14 w-full rounded-[var(--radius-md)]" />
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center gap-2 rounded-[var(--radius-md)] border border-border bg-bg p-4 text-center">
          <p className="text-xs text-text-muted">
            {error.message || "Couldn't load relationships for this standard."}
          </p>
          {onRetry && (
            <Button variant="secondary" size="sm" onClick={onRetry} className="h-7 text-xs">
              <RotateCw className="h-3 w-3" aria-hidden="true" />
              Retry
            </Button>
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && relationships.length === 0 && (
        <div className="rounded-[var(--radius-md)] border border-dashed border-border bg-bg p-6 text-center">
          <p className="text-sm font-medium text-text">No direct relationships found</p>
          <p className="mt-1 text-xs text-text-muted">
            This standard does not have recorded supersessions or direct references in the currently indexed graph.
          </p>
        </div>
      )}

      {/* Success list */}
      {!loading && !error && relationships.length > 0 && (
        <ul className="divide-y divide-border/60 rounded-[var(--radius-md)] border border-border bg-bg">
          {relationships.map((rel) => {
            const relConfig = RELATION_CONFIG[rel.relation] || {
              label: rel.relation,
              tone: 'neutral',
            }

            return (
              <li
                key={`${rel.id}-${rel.relation}`}
                className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 transition-colors hover:bg-surface"
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/standards/${encodeURIComponent(rel.id)}`}
                      className="font-technical text-sm font-semibold text-primary hover:underline"
                    >
                      {rel.id}
                    </Link>
                    <Badge tone={relConfig.tone}>{relConfig.label}</Badge>
                    {rel.status && <StatusBadge status={rel.status} />}
                  </div>
                  {rel.title && rel.title !== rel.id && (
                    <p className="truncate text-xs text-text-body">{rel.title}</p>
                  )}
                </div>

                <Link
                  to={`/standards/${encodeURIComponent(rel.id)}`}
                  className="flex items-center gap-1 text-xs font-medium text-text-muted transition-colors group-hover:text-primary shrink-0 self-end sm:self-center"
                >
                  Details
                  <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
