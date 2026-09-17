import {
  ArrowLeft,
  List,
  Network,
  Plus,
  Maximize2,
  ZoomIn,
  ZoomOut,
} from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

/**
 * Control toolbar for Graph visualization: View modes, Depth 1-3 selection,
 * Zoom controls, and Pagination.
 *
 * @param {{
 *   viewMode: 'canvas' | 'list',
 *   onViewModeChange: (mode: 'canvas' | 'list') => void,
 *   isFocusedMode: boolean,
 *   focusedStandardNo?: string | null,
 *   depth?: number,
 *   onDepthChange?: (depth: number) => void,
 *   onClearFocus?: () => void,
 *   onLoadMore?: () => void,
 *   loadingMore?: boolean,
 *   totalNodes?: number,
 *   totalEdges?: number,
 *   onZoomIn?: () => void,
 *   onZoomOut?: () => void,
 *   onFitView?: () => void,
 *   className?: string,
 * }} props
 */
export function GraphControls({
  viewMode = 'canvas',
  onViewModeChange,
  isFocusedMode = false,
  _focusedStandardNo,
  depth = 1,
  onDepthChange,
  onClearFocus,
  onLoadMore,
  loadingMore = false,
  totalNodes = 0,
  totalEdges = 0,
  onZoomIn,
  onZoomOut,
  onFitView,
  className,
}) {

  return (
    <div
      className={cn(
        'flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-border bg-surface p-3.5 shadow-[var(--shadow-card)]',
        className
      )}
      role="toolbar"
      aria-label="Standards graph navigation controls"
    >
      {/* Left: View Mode Toggle & Mode Status */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-[var(--radius-md)] border border-border bg-bg p-0.5">
          <button
            type="button"
            onClick={() => onViewModeChange('canvas')}
            className={cn(
              'flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1 text-xs font-semibold transition-colors',
              viewMode === 'canvas'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-text-muted hover:text-text'
            )}
            aria-pressed={viewMode === 'canvas'}
          >
            <Network className="h-3.5 w-3.5" aria-hidden="true" />
            Graph Canvas
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange('list')}
            className={cn(
              'flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1 text-xs font-semibold transition-colors',
              viewMode === 'list'
                ? 'bg-surface text-primary shadow-xs'
                : 'text-text-muted hover:text-text'
            )}
            aria-pressed={viewMode === 'list'}
          >
            <List className="h-3.5 w-3.5" aria-hidden="true" />
            Accessible List
          </button>
        </div>

        {/* Node & Edge count telemetry */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-text-muted">
          <span>·</span>
          <span>
            <strong className="font-technical text-text font-semibold">{totalNodes}</strong> nodes,{' '}
            <strong className="font-technical text-text font-semibold">{totalEdges}</strong> edges
          </span>
        </div>
      </div>

      {/* Right: Depth Selector (Focused Mode) OR Load More (Full Mode) */}
      <div className="flex flex-wrap items-center gap-2">
        {isFocusedMode ? (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-text-muted hidden md:inline">
              BFS Depth:
            </span>
            <div className="inline-flex rounded-[var(--radius-md)] border border-border bg-bg p-0.5" role="group" aria-label="Graph exploration depth">
              {[1, 2, 3].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => onDepthChange && onDepthChange(d)}
                  className={cn(
                    'px-2.5 py-1 text-xs font-technical font-semibold transition-colors rounded-[var(--radius-sm)]',
                    depth === d
                      ? 'bg-primary text-white shadow-xs'
                      : 'text-text-muted hover:text-text'
                  )}
                  aria-pressed={depth === d}
                >
                  Depth {d}
                </button>
              ))}
            </div>

            {onClearFocus && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearFocus}
                className="h-8 px-2 text-xs text-text-muted hover:text-text"
                title="Return to full network graph"
              >
                <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
                Full Network
              </Button>
            )}
          </div>
        ) : (
          onLoadMore && (
            <Button
              variant="secondary"
              size="sm"
              loading={loadingMore}
              onClick={onLoadMore}
              className="h-8 text-xs font-medium"
            >
              {!loadingMore && <Plus className="h-3.5 w-3.5" aria-hidden="true" />}
              Load more standards
            </Button>
          )
        )}

        {/* Canvas Zoom Controls (Only active in canvas mode) */}
        {viewMode === 'canvas' && (
          <div className="hidden sm:flex items-center gap-1 border-l border-border pl-2">
            {onZoomIn && (
              <button
                type="button"
                onClick={onZoomIn}
                className="rounded p-1 text-text-muted hover:bg-bg hover:text-text"
                title="Zoom in"
                aria-label="Zoom in"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
            )}
            {onZoomOut && (
              <button
                type="button"
                onClick={onZoomOut}
                className="rounded p-1 text-text-muted hover:bg-bg hover:text-text"
                title="Zoom out"
                aria-label="Zoom out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
            )}
            {onFitView && (
              <button
                type="button"
                onClick={onFitView}
                className="rounded p-1 text-text-muted hover:bg-bg hover:text-text"
                title="Fit graph to view"
                aria-label="Fit graph to view"
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
