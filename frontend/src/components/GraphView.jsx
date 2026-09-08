import { useState, useEffect, useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { fetchGraph } from "../lib/api";

const CATEGORY_COLORS = {
  "Electrical Safety": "#f59e0b",
  "Consumer Products": "#10b981",
  "Food and Beverage": "#06b6d4",
  "Automotive Safety": "#f43f5e",
  "Household Appliances": "#8b5cf6",
};

export default function GraphView() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const containerRef = useRef(null);
  const fgRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);

    fetchGraph()
      .then((data) => {
        // Exclude self-referencing category links from visual clutter if desired
        const cleanLinks = (data.edges || []).filter(
          (e) => e.source !== e.target
        );
        setGraphData({
          nodes: (data.nodes || []).map((n) => ({
            ...n,
            color: CATEGORY_COLORS[n.category] || "#6366f1",
            val: 8,
          })),
          links: cleanLinks.map((l) => ({
            ...l,
            color: l.relation === "supersedes" ? "#ef4444" : "#6366f1",
          })),
        });
      })
      .catch((err) => {
        setError(err.message || "Failed to load standards relationship graph.");
      })
      .finally(() => setIsLoading(false));

    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2.5, 1000);
    }
  };

  const getConnectedEdges = (nodeId) => {
    return graphData.links.filter(
      (l) =>
        (typeof l.source === "object" ? l.source.id : l.source) === nodeId ||
        (typeof l.target === "object" ? l.target.id : l.target) === nodeId
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden relative" ref={containerRef}>
      {/* Top Controls Bar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur flex items-center justify-between z-10">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            Standards Relationship Graph
          </h1>
          <p className="text-xs text-slate-400">
            Visualizing dependencies, cross-references, and supersession among BIS standards.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 flex-wrap text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span className="text-slate-300">Supersedes</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
            <span className="text-slate-300">References</span>
          </div>
          <button
            onClick={() => {
              if (fgRef.current) {
                fgRef.current.zoomToFit(400);
                setSelectedNode(null);
              }
            }}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            Reset View
          </button>
        </div>
      </div>

      {/* Graph Area */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-20">
            <div className="flex flex-col items-center gap-2 text-indigo-400">
              <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span className="text-sm text-slate-300">Loading graph topology...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center p-6 z-20">
            <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-xl text-rose-300 text-sm max-w-md">
              {error}
            </div>
          </div>
        )}

        {!isLoading && !error && graphData.nodes.length > 0 && (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel={(n) => `${n.standard_no}: ${n.title}`}
            nodeColor={(n) => n.color}
            nodeRelSize={6}
            linkColor={(l) => l.color}
            linkWidth={1.5}
            linkDirectionalArrowLength={4}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            cooldownTicks={100}
            nodeCanvasObjectMode={() => "after"}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.standard_no || node.id;
              const fontSize = 11 / globalScale;
              ctx.font = `${fontSize}px Inter, sans-serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "middle";
              ctx.fillStyle = "#ffffff";
              ctx.fillText(label, node.x, node.y + 12);
            }}
          />
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute right-4 top-20 bottom-4 w-80 bg-slate-900/95 backdrop-blur border border-slate-800 rounded-2xl p-5 shadow-2xl z-20 flex flex-col justify-between overflow-y-auto">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold uppercase px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800">
                  {selectedNode.category || "Standard"}
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  {selectedNode.standard_no}
                </h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-white"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div>
              <p className="text-xs text-slate-400 font-medium">Standard Title</p>
              <p className="text-sm text-slate-200 mt-0.5">{selectedNode.title}</p>
            </div>

            <div className="flex gap-4 text-xs text-slate-400">
              <div>
                <span className="block font-medium">Year</span>
                <span className="text-slate-200">{selectedNode.year || "N/A"}</span>
              </div>
              <div>
                <span className="block font-medium">Status</span>
                <span className={selectedNode.title?.includes("superseded") ? "text-rose-400" : "text-emerald-400"}>
                  {selectedNode.title?.includes("superseded") ? "Superseded" : "Active"}
                </span>
              </div>
            </div>

            {/* Connected Relations */}
            <div>
              <p className="text-xs text-slate-400 font-medium mb-2">Connected Relationships</p>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {getConnectedEdges(selectedNode.id).length > 0 ? (
                  getConnectedEdges(selectedNode.id).map((edge, idx) => {
                    const sourceId = typeof edge.source === "object" ? edge.source.id : edge.source;
                    const targetId = typeof edge.target === "object" ? edge.target.id : edge.target;
                    const isOutgoing = sourceId === selectedNode.id;
                    return (
                      <div
                        key={idx}
                        className="text-xs p-2 rounded bg-slate-800/80 border border-slate-700/60 flex items-center justify-between"
                      >
                        <span className="text-slate-300">
                          {isOutgoing ? `→ ${targetId}` : `← ${sourceId}`}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                          edge.relation === "supersedes"
                            ? "bg-rose-950 text-rose-300"
                            : "bg-indigo-950 text-indigo-300"
                        }`}>
                          {edge.label || edge.relation}
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-500 italic">No direct connections.</p>
                )}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            <button
              onClick={() => setSelectedNode(null)}
              className="w-full py-2 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            >
              Close Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
