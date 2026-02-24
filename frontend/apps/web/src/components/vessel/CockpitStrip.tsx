"use client";

// ── Schema-agnostic normalisation ─────────────────────────────────────────────
// The frontend DashboardOut type and the backend schema use different field names.
// We cast to unknown and probe both variants so the strip works regardless.

interface NormalisedDash {
  performance: number;
  cohesion: number;
  stability: number;
  riskLevel: string;
  weatherStatus: string;
  weatherAvg: number | null;
  crewType: string;
  action: string;
  earlyWarning: string;
  fTeamGlobal: number | null;
}

function normalise(raw: Record<string, unknown>): NormalisedDash {
  const metrics = raw.harmony_metrics as Record<string, unknown> | undefined;
  const diagnosis = (raw.full_diagnosis ?? raw.diagnosis) as
    | Record<string, unknown>
    | undefined;
  const weather = raw.weather_trend;

  const performance = Number(
    metrics?.performance_index ?? metrics?.performance ?? 0,
  );
  const cohesion = Number(metrics?.cohesion_index ?? metrics?.cohesion ?? 0);
  const stability = Number(
    metrics?.stability_index ?? metrics?.data_quality ?? 0,
  );
  const riskLevel = String(
    metrics?.risk_level ?? diagnosis?.risk_level ?? "UNKNOWN",
  );

  const weatherStatus =
    typeof weather === "string"
      ? weather
      : String(
          (weather as Record<string, unknown> | undefined)?.status ?? "unknown",
        );
  const weatherAvg =
    typeof weather === "object" && weather !== null
      ? Number((weather as Record<string, unknown>).average ?? 0)
      : null;

  const crewType = String(
    diagnosis?.crew_type ?? diagnosis?.label ?? "—",
  );
  const action = String(
    diagnosis?.recommended_action ??
      (diagnosis?.recommendations as string[] | undefined)?.[0] ??
      "—",
  );
  const earlyWarning = String(diagnosis?.early_warning ?? "");

  // f_team_global might be in the sociogram, but backend dashboard may expose it
  const fTeamGlobal =
    raw.f_team_global != null ? Number(raw.f_team_global) : null;

  return {
    performance,
    cohesion,
    stability,
    riskLevel,
    weatherStatus,
    weatherAvg,
    crewType,
    action,
    earlyWarning,
    fTeamGlobal,
  };
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function MetricBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const pct = Math.min(100, Math.max(0, Math.round(value)));
  const color =
    pct >= 75 ? "#22C55E" : pct >= 50 ? "#F59E0B" : "#EF4444";

  return (
    <div className="flex flex-col gap-1 min-w-[80px]">
      <div className="flex items-end justify-between">
        <span className="text-xs text-muted">{label}</span>
        <span className="text-sm font-semibold" style={{ color }}>
          {pct}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-elevated overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

const RISK_STYLES: Record<string, string> = {
  LOW: "badge-success",
  MEDIUM: "badge-warning",
  HIGH: "badge-danger",
  CRITICAL: "badge-danger",
};

const WEATHER_ICONS: Record<string, string> = {
  improving: "↑",
  stable: "→",
  degrading: "↓",
  turbulent: "⚡",
  stable_turbulent: "~",
  critical: "⚠",
  unknown: "?",
};

// ── Main export ───────────────────────────────────────────────────────────────

interface CockpitStripProps {
  /** Raw DashboardOut (or undefined while loading) */
  dashboard: unknown;
  /** F_team score from the sociogram (more accurate than dashboard) */
  fTeamScore?: number;
}

export function CockpitStrip({ dashboard, fTeamScore }: CockpitStripProps) {
  if (!dashboard) {
    return (
      <div className="h-28 border-t border-bg-border bg-bg-secondary flex items-center px-6 gap-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 w-20 rounded bg-bg-elevated animate-pulse" />
        ))}
      </div>
    );
  }

  const d = normalise(dashboard as Record<string, unknown>);
  const riskCls = RISK_STYLES[d.riskLevel] ?? "badge-info";
  const weatherIcon = WEATHER_ICONS[d.weatherStatus] ?? "?";

  return (
    <div className="h-28 border-t border-bg-border bg-bg-secondary flex items-center px-5 gap-5 shrink-0 overflow-x-auto">

      {/* Metric bars */}
      <div className="flex gap-5 shrink-0">
        <MetricBar label="Performance" value={d.performance} />
        <MetricBar label="Cohesion" value={d.cohesion} />
        <MetricBar label="Stability" value={d.stability} />
      </div>

      <div className="w-px h-14 bg-bg-border shrink-0" />

      {/* Risk + Weather */}
      <div className="flex flex-col gap-1.5 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Risk</span>
          <span className={`badge text-xs ${riskCls}`}>{d.riskLevel}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Weather</span>
          <span className="text-xs font-medium text-text-primary">
            {weatherIcon} {d.weatherStatus}
          </span>
          {d.weatherAvg !== null && (
            <span className="text-xs text-muted">
              ({d.weatherAvg.toFixed(1)}/5)
            </span>
          )}
        </div>
      </div>

      {/* F_team */}
      {(fTeamScore !== undefined || d.fTeamGlobal !== null) && (
        <>
          <div className="w-px h-14 bg-bg-border shrink-0" />
          <div className="flex flex-col items-center shrink-0">
            <span className="text-2xl font-bold text-brand-primary">
              {Math.round(fTeamScore ?? d.fTeamGlobal ?? 0)}
            </span>
            <span className="text-xs text-muted">F_team</span>
          </div>
        </>
      )}

      <div className="w-px h-14 bg-bg-border shrink-0" />

      {/* Diagnosis */}
      <div className="flex-1 min-w-0">
        <p className="text-xs text-muted mb-0.5">Team diagnosis</p>
        <p className="text-sm font-medium text-text-primary truncate">{d.crewType}</p>
        <p className="text-xs text-muted truncate mt-0.5">{d.action}</p>
        {d.earlyWarning && (
          <p className="text-xs text-amber-400 mt-0.5 truncate">⚠ {d.earlyWarning}</p>
        )}
      </div>
    </div>
  );
}
