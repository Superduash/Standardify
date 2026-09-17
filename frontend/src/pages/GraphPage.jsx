import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowLeft, SearchX } from 'lucide-react'
import { getFullGraph, getGraphForStandard } from '../api/endpoints'
import { normalizeApiError } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Breadcrumbs } from '../components/layout/Breadcrumbs'
import { GraphCanvas } from '../components/graph/GraphCanvas'
import { GraphControls } from '../components/graph/GraphControls'
import { GraphLegend } from '../components/graph/GraphLegend'
import { GraphNodePanel } from '../components/graph/GraphNodePanel'
import { GraphAccessibleListView } from '../components/graph/GraphAccessibleListView'
import { Card } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button, buttonClasses } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Skeleton } from '../components/ui/Skeleton'

/** Skeleton loading view for Graph page */
function GraphPageSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading standards relationship graph">
      <Skeleton className="h-4 w-48" />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-8 w-44" />
      </div>
      <Skeleton className="h-12 w-full rounded-[var(--radius-lg)]" />
      <Skeleton className="h-[520px] w-full rounded-[var(--radius-lg)]" />
    </div>
  )
}

export function GraphPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const focusParam = searchParams.get('focus') || ''
  const focusedStandardNo = focusParam.trim() ? decodeURIComponent(focusParam.trim()) : null

  const { showToast } = useToast()

  // State
  const [depth, setDepth] = useState(1)
  const [viewMode, setViewMode] = useState('canvas')
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [offset, setOffset] = useState(0)

  // Container dimensions
  const containerRef = useRef(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 550 })
  const graphCanvasRef = useRef(null)

  // Resize observer to ensure responsive graph canvas
  useEffect(() => {
    if (!containerRef.current) return
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          const w = Math.max(Math.floor(entry.contentRect.width), 320)
          const h = Math.max(Math.min(Math.floor(window.innerHeight * 0.65), 650), 450)
          setDimensions({ width: w, height: h })
        }
      }
    })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  // Load Graph Data based on Mode (Focused vs Full)
  const loadGraph = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSelectedNode(null)

    try {
      if (focusedStandardNo) {
        // Focused 1-3 hop subgraph
        const data = await getGraphForStandard(focusedStandardNo, depth)
        const fetchedNodes = Array.isArray(data?.nodes) ? data.nodes : []
        const fetchedEdges = Array.isArray(data?.edges) ? data.edges : []

        setNodes(fetchedNodes)
        setEdges(fetchedEdges)
        setHasMore(false)
      } else {
        // Full paginated graph
        const data = await getFullGraph({ limit: 100, offset: 0 })
        const fetchedNodes = Array.isArray(data?.nodes) ? data.nodes : []
        const fetchedEdges = Array.isArray(data?.edges) ? data.edges : []

        setNodes(fetchedNodes)
        setEdges(fetchedEdges)
        setOffset(fetchedNodes.length)
        setHasMore(fetchedNodes.length >= 100)
      }
    } catch (err) {
      const normalized = normalizeApiError(err)
      setError(normalized)
      setNodes([])
      setEdges([])
      showToast(normalized.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [focusedStandardNo, depth, showToast])

  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  // Incremental pagination for Full Graph mode
  const handleLoadMore = async () => {
    if (loadingMore || focusedStandardNo) return
    setLoadingMore(true)

    try {
      const data = await getFullGraph({ limit: 100, offset })
      const newNodes = Array.isArray(data?.nodes) ? data.nodes : []
      const newEdges = Array.isArray(data?.edges) ? data.edges : []

      if (newNodes.length === 0) {
        setHasMore(false)
        showToast('All available indexed standards loaded.', 'success')
      } else {
        // Merge without duplicates
        setNodes((prevNodes) => {
          const nodeMap = new Map()
          prevNodes.forEach((n) => nodeMap.set(n.id, n))
          newNodes.forEach((n) => nodeMap.set(n.id, n))
          return Array.from(nodeMap.values())
        })

        setEdges((prevEdges) => {
          const edgeMap = new Map()
          const makeKey = (e) => {
            const s = typeof e.source === 'object' ? e.source.id : e.source
            const t = typeof e.target === 'object' ? e.target.id : e.target
            return `${s}-${t}-${e.relation || ''}`
          }
          prevEdges.forEach((e) => edgeMap.set(makeKey(e), e))
          newEdges.forEach((e) => edgeMap.set(makeKey(e), e))
          return Array.from(edgeMap.values())
        })

        setOffset((prev) => prev + newNodes.length)
        setHasMore(newNodes.length >= 100)
        showToast(`Loaded ${newNodes.length} additional standards into graph.`, 'success')
      }
    } catch (err) {
      const normalized = normalizeApiError(err)
      showToast(normalized.message, 'error')
    } finally {
      setLoadingMore(false)
    }
  }

  // Handle Focus change via URL searchParams
  const handleFocusNode = (standardNo) => {
    const params = new URLSearchParams(searchParams)
    params.set('focus', standardNo)
    setSearchParams(params)
  }

  const handleClearFocus = () => {
    const params = new URLSearchParams(searchParams)
    params.delete('focus')
    setSearchParams(params)
  }

  const handleDepthChange = (newDepth) => {
    setDepth(newDepth)
  }

  // Zoom control helpers
  const handleZoomIn = () => {
    if (graphCanvasRef.current?.zoom) {
      graphCanvasRef.current.zoom(graphCanvasRef.current.zoom() * 1.3, 300)
    }
  }

  const handleZoomOut = () => {
    if (graphCanvasRef.current?.zoom) {
      graphCanvasRef.current.zoom(graphCanvasRef.current.zoom() / 1.3, 300)
    }
  }

  const handleFitView = () => {
    if (graphCanvasRef.current?.zoomToFit) {
      graphCanvasRef.current.zoomToFit(400, 40)
    }
  }

  // Node Map for fast lookup
  const nodesMap = useMemo(() => {
    const map = new Map()
    nodes.forEach((n) => {
      if (n && n.id) map.set(n.id, n)
    })
    return map
  }, [nodes])

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10 space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumbs
        items={
          focusedStandardNo
            ? [
                { label: 'Standards', to: '/standards' },
                {
                  label: focusedStandardNo,
                  to: `/standards/${encodeURIComponent(focusedStandardNo)}`,
                  isCode: true,
                },
                { label: 'Relationships', current: true },
              ]
            : [{ label: 'Standards', to: '/standards' }, { label: 'Relationship Graph', current: true }]
        }
      />

      {/* Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-5 text-left">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full border border-primary/20 bg-primary-light px-3 py-0.5 text-xs font-medium text-primary">
              Knowledge Graph
            </span>
            {focusedStandardNo && (
              <Badge tone="primary">Focused Subgraph</Badge>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text">
            {focusedStandardNo ? (
              <>
                Exploring Relationships for{' '}
                <span className="font-technical text-primary">{focusedStandardNo}</span>
              </>
            ) : (
              'Standards Relationship Network'
            )}
          </h1>
          <p className="text-xs text-text-muted">
            {focusedStandardNo
              ? `Exploring immediate and multi-hop connections (depth ${depth}) for ${focusedStandardNo}.`
              : 'Interactive network map visualizing supersessions, references, and domain categories across Indian Standards.'}
          </p>
        </div>

        {/* Header Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {focusedStandardNo && (
            <Link
              to={`/standards/${encodeURIComponent(focusedStandardNo)}`}
              className={buttonClasses({ variant: 'secondary', size: 'sm', className: 'text-xs' })}
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              Back to Standard
            </Link>
          )}

          <Link
            to="/standards"
            className="inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-border bg-surface px-3 py-1.5 text-xs font-medium text-text-body transition-colors hover:bg-bg hover:text-text"
          >
            Search standards
          </Link>
        </div>
      </header>

      {/* Control Toolbar */}
      <section aria-label="Graph controls and view toggles">
        <GraphControls
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          isFocusedMode={Boolean(focusedStandardNo)}
          focusedStandardNo={focusedStandardNo}
          depth={depth}
          onDepthChange={handleDepthChange}
          onClearFocus={handleClearFocus}
          onLoadMore={hasMore ? handleLoadMore : undefined}
          loadingMore={loadingMore}
          totalNodes={nodes.length}
          totalEdges={edges.length}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onFitView={handleFitView}
        />
      </section>

      {/* Main Graph Content Area */}
      <div ref={containerRef} className="relative min-h-[450px]">
        {/* Loading State */}
        {loading && <GraphPageSkeleton />}

        {/* Error State */}
        {!loading && error && (
          <ErrorState
            message={error.message || 'Failed to load graph relationships.'}
            requestId={error.requestId}
            onRetry={loadGraph}
          />
        )}

        {/* Empty State */}
        {!loading && !error && nodes.length === 0 && (
          <Card className="p-8 text-center">
            <EmptyState
              icon={SearchX}
              title={focusedStandardNo ? `No relationships found for ${focusedStandardNo}` : 'No graph nodes found'}
              description={
                focusedStandardNo
                  ? `Standard "${focusedStandardNo}" has no recorded superseding or referencing relationships in the current indexed BIS knowledge graph.`
                  : 'The standards relationship repository is currently empty.'
              }
              action={
                focusedStandardNo ? (
                  <Button variant="secondary" size="sm" onClick={handleClearFocus} className="mt-3">
                    View full graph
                  </Button>
                ) : (
                  <Link to="/standards" className={buttonClasses({ variant: 'secondary', size: 'sm', className: 'mt-3' })}>
                    Search standards repository
                  </Link>
                )
              }
            />
          </Card>
        )}

        {/* Success View: Canvas Mode */}
        {!loading && !error && nodes.length > 0 && viewMode === 'canvas' && (
          <div className="relative">
            <GraphCanvas
              ref={graphCanvasRef}
              nodes={nodes}
              edges={edges}
              focusedStandardNo={focusedStandardNo}
              selectedNode={selectedNode}
              onNodeClick={(node) => setSelectedNode(node)}
              onBackgroundClick={() => setSelectedNode(null)}
              width={dimensions.width}
              height={dimensions.height}
            />

            {/* Floating Legend (Bottom Left) */}
            <div className="absolute bottom-3 left-3 z-30 max-w-[260px]">
              <GraphLegend />
            </div>

            {/* Floating Selected Node Detail Panel (Top/Bottom Right) */}
            {selectedNode && (
              <div className="absolute top-3 right-3 z-30 w-80 sm:w-96 max-w-[calc(100%-24px)]">
                <GraphNodePanel
                  node={selectedNode}
                  focusedStandardNo={focusedStandardNo}
                  edges={edges}
                  nodesMap={nodesMap}
                  onClose={() => setSelectedNode(null)}
                  onFocusNode={(stdNo) => {
                    setSelectedNode(null)
                    handleFocusNode(stdNo)
                  }}
                />
              </div>
            )}
          </div>
        )}

        {/* Success View: Accessible Semantic List Mode */}
        {!loading && !error && nodes.length > 0 && viewMode === 'list' && (
          <GraphAccessibleListView
            nodes={nodes}
            edges={edges}
            focusedStandardNo={focusedStandardNo}
            onFocusNode={handleFocusNode}
          />
        )}
      </div>
    </main>
  )
}

export default GraphPage
