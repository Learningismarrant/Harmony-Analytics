"use client";

import type { PhysicsNode, PhysicsEdge } from "../physics";

interface NodeInfoPanelProps {
  node: PhysicsNode;
  edges: PhysicsEdge[];
  onClose: () => void;
  onSimulate?: (node: PhysicsNode) => void;
  isCandidate?: boolean;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value);
  const colorClass =
    pct >= 75 ? "bg-green-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted">{label}</span>
        <span className="font-medium">{pct}</span>
      </div>
      <div className="h-1 bg-bg-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function NodeInfoPanel({
  node,
  edges,
  onClose,
  onSimulate,
  isCandidate,
}: NodeInfoPanelProps) {
  // Edges involving this node
  const nodeEdges = edges.filter(
    (e) =>
      e.source.id === node.id ||
      e.target.id === node.id,
  );

  const avgDyadScore =
    nodeEdges.length > 0
      ? nodeEdges.reduce((sum, e) => sum + e.dyadScore, 0) / nodeEdges.length
      : null;

  const { data } = node;

  return (
    <div
      className="absolute top-4 right-4 w-64 card animate-slide-up z-10"
      style={{ backdropFilter: "blur(12px)" }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-sm">{data.name}</h3>
          <p className="text-xs text-muted mt-0.5">{data.position}</p>
        </div>
        <button
          onClick={onClose}
          className="text-muted hover:text-text-primary text-lg leading-none -mt-0.5"
          aria-label="Close"
        >
          ×
        </button>
      </div>

      {isCandidate && (
        <div className="badge badge-info mb-3 text-xs">Simulation candidate</div>
      )}

      {/* Scores */}
      <div className="space-y-2.5 mb-4">
        <ScoreBar label="Individual perf. (P_ind)" value={data.p_ind} />
        <ScoreBar label="Data completeness" value={data.psychometric_completeness * 100} />
        {avgDyadScore !== null && (
          <ScoreBar label="Avg team compatibility" value={avgDyadScore} />
        )}
      </div>

      {/* Dyad list */}
      {nodeEdges.length > 0 && (
        <div>
          <p className="text-xs text-muted mb-2">Dyad compatibility</p>
          <div className="space-y-1.5">
            {nodeEdges.slice(0, 5).map((e) => {
              const peer = e.source.id === node.id ? e.target : e.source;
              const score = Math.round(e.dyadScore);
              return (
                <div key={`${e.source.id}-${e.target.id}`} className="flex justify-between text-xs">
                  <span className="text-muted truncate">{peer.data.name.split(" ")[0]}</span>
                  <span
                    className={
                      score >= 75
                        ? "text-green-400"
                        : score >= 50
                          ? "text-amber-400"
                          : "text-red-400"
                    }
                  >
                    {score}
                    {e.riskFlags.length > 0 && " ⚠"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Simulate button */}
      {onSimulate && !isCandidate && (
        <button
          onClick={() => onSimulate(node)}
          className="btn-primary w-full justify-center mt-4 text-xs py-1.5"
        >
          ◎ Simulate adding to crew
        </button>
      )}
    </div>
  );
}
