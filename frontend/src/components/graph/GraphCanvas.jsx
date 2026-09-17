import { forwardRef, useCallback, useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { STATUS_COLORS, RELATION_COLORS } from './GraphLegend'


/**
 * 2D Canvas Force Graph renderer for Standardify Standards Relationships.
 */
export const GraphCanvas = forwardRef(function GraphCanvas(
  {
    nodes = [],
    edges = [],
    focusedStandardNo,
    selectedNode,
    onNodeClick,
    onBackgroundClick,
    width = 800,
    height = 550,
  },
  ref
) {
  // Format links array ensuring source & target keys for ForceGraph2D
  const graphData = useMemo(() => {
    const formattedNodes = nodes.map((n) => ({
      ...n,
      id: n.id,
      name: n.label || n.id,
    }))

    const validNodeIds = new Set(formattedNodes.map((n) => n.id))

    const formattedLinks = edges
      .filter((e) => e && e.source && e.target)
      .map((e) => {
        const sourceId = typeof e.source === 'object' ? e.source.id : e.source
        const targetId = typeof e.target === 'object' ? e.target.id : e.target
        return {
          source: sourceId,
          target: targetId,
          relation: e.relation || 'references',
        }
      })
      .filter((link) => validNodeIds.has(link.source) && validNodeIds.has(link.target))

    return { nodes: formattedNodes, links: formattedLinks }
  }, [nodes, edges])

  // Custom node canvas painting
  const paintNode = useCallback(
    (node, ctx, globalScale) => {
      const isFocused = focusedStandardNo && node.id === focusedStandardNo
      const isSelected = selectedNode && node.id === selectedNode.id
      const statusKey = (node.status || '').toLowerCase()
      const statusConfig = STATUS_COLORS[statusKey] || STATUS_COLORS.active

      const radius = isFocused ? 9 : 6.5

      // Outer focus/selected halo ring
      if (isFocused || isSelected) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius + 4 / globalScale, 0, 2 * Math.PI, false)
        ctx.strokeStyle = isFocused ? '#264796' : '#147D76'
        ctx.lineWidth = 2.5 / globalScale
        ctx.stroke()

        if (isFocused) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, radius + 7 / globalScale, 0, 2 * Math.PI, false)
          ctx.strokeStyle = 'rgba(38, 71, 150, 0.35)'
          ctx.lineWidth = 1.5 / globalScale
          ctx.stroke()
        }
      }

      // Main node circle
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
      ctx.fillStyle = statusConfig.bg
      ctx.fill()
      ctx.strokeStyle = '#FFFFFF'
      ctx.lineWidth = 1.5 / globalScale
      ctx.stroke()

      // Node label
      const fontSize = Math.max(10 / globalScale, 3)
      ctx.font = `${isFocused || isSelected ? 'bold' : 'normal'} ${fontSize}px "IBM Plex Mono", monospace`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'

      // Background label pill for legibility
      const labelText = node.id
      const textWidth = ctx.measureText(labelText).width
      const pad = 2 / globalScale

      ctx.fillStyle = 'rgba(255, 255, 255, 0.92)'
      ctx.fillRect(
        node.x - textWidth / 2 - pad,
        node.y + radius + 2 / globalScale,
        textWidth + pad * 2,
        fontSize + pad
      )

      ctx.fillStyle = isFocused ? '#264796' : '#172033'
      ctx.fillText(labelText, node.x, node.y + radius + 3 / globalScale)
    },
    [focusedStandardNo, selectedNode]
  )

  // Link styling
  const getLinkColor = useCallback((link) => {
    const relKey = link.relation || 'references'
    return RELATION_COLORS[relKey]?.color || '#264796'
  }, [])

  return (
    <div className="relative overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface shadow-[var(--shadow-card)]">
      <ForceGraph2D
        ref={ref}
        graphData={graphData}
        width={width}
        height={height}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          ctx.fillStyle = color
          ctx.beginPath()
          ctx.arc(node.x, node.y, 14, 0, 2 * Math.PI, false)
          ctx.fill()
        }}
        linkColor={getLinkColor}
        linkWidth={1.5}
        linkDirectionalArrowLength={4.5}
        linkDirectionalArrowRelPos={0.9}
        linkDirectionalArrowColor={getLinkColor}
        onNodeClick={(node) => onNodeClick && onNodeClick(node)}
        onBackgroundClick={() => onBackgroundClick && onBackgroundClick()}
        cooldownTicks={120}
        d3AlphaDecay={0.03}
        d3VelocityDecay={0.3}
      />
    </div>
  )
})
