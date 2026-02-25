"use client";

import type { SimulationPreviewOut } from "@harmony/types";

interface SimulationOverlayProps {
  preview: SimulationPreviewOut;
  onAccept: () => void;
  onCancel: () => void;
  loading?: boolean;
}

function DeltaBadge({ value, label }: { value: number; label: string }) {
  const positive = value >= 0;
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted">{label}</span>
      <span
        className={`text-xs font-semibold ${positive ? "text-green-400" : "text-red-400"}`}
      >
        {positive ? "+" : ""}
        {value.toFixed(1)}
      </span>
    </div>
  );
}

const RECOMMENDATION_STYLE: Record<string, string> = {
  STRONG_FIT: "badge-success",
  MODERATE_FIT: "badge-info",
  WEAK_FIT: "badge-warning",
  RISK: "badge-danger",
};

export function SimulationOverlay({
  preview,
  onAccept,
  onCancel,
  loading,
}: SimulationOverlayProps) {
  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-80 card animate-slide-up z-10">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">Impact simulation</h3>
        <span className={`badge ${RECOMMENDATION_STYLE[preview.recommendation] ?? "badge-info"}`}>
          {preview.recommendation.replace("_", " ")}
        </span>
      </div>

      <p className="text-xs text-muted mb-3">
        Adding <strong className="text-text-primary">{preview.candidate_name}</strong> to the crew:
      </p>

      <div className="space-y-1.5 mb-4">
        <DeltaBadge value={preview.delta_f_team} label="Team score (F_team)" />
        <DeltaBadge value={preview.delta_cohesion} label="Cohesion" />
      </div>

      {preview.impact_flags.length > 0 && (
        <div className="mb-3">
          {preview.impact_flags.map((flag) => (
            <div
              key={flag}
              className="badge badge-warning mb-1 text-xs"
            >
              ⚠ {flag}
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="btn-ghost flex-1 text-xs py-1.5 justify-center"
        >
          Cancel
        </button>
        <button
          onClick={onAccept}
          disabled={loading}
          className="btn-primary flex-1 text-xs py-1.5 justify-center"
        >
          {loading ? "Hiring…" : "Hire candidate"}
        </button>
      </div>
    </div>
  );
}
