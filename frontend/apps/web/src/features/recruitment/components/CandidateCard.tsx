"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { MatchResultOut } from "@harmony/types";
import { AvatarBubble } from "./AvatarBubble";
import { ScoreBar } from "./ScoreBar";

const CONFIDENCE_CLS: Record<string, string> = {
  HIGH: "badge-success",
  MEDIUM: "badge-warning",
  LOW: "badge-danger",
};

function deltaColor(v: number | null) {
  return (v ?? 0) >= 0 ? "text-emerald-500/70" : "text-red-500/60";
}

export interface CandidateCardProps {
  candidate: MatchResultOut;
  campaignId: number;
  isSimulating: boolean;
  onSimulate: (crewProfileId: number, campaignId: number) => void;
}

export function CandidateCard({
  candidate: c,
  campaignId,
  isSimulating,
  onSimulate,
}: CandidateCardProps) {
  const queryClient = useQueryClient();

  const rejectMutation = useMutation({
    mutationFn: () => recruitmentApi.reject(campaignId, c.crew_profile_id),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: queryKeys.recruitment.matching(campaignId),
      }),
  });

  if (c.is_hired) {
    return (
      <div className="p-3 rounded-xl bg-bg-elevated border border-bg-border opacity-50">
        <div className="flex items-center gap-2.5">
          <AvatarBubble name={c.name} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate text-text-primary">{c.name}</p>
            {c.location && <p className="text-xs text-muted truncate">{c.location}</p>}
          </div>
          <span className="badge badge-success text-xs">Hired</span>
        </div>
      </div>
    );
  }

  if (c.is_rejected) return null;

  const fitColor =
    c.profile_fit.g_fit >= 75 ? "#3D9A6A" :
    c.profile_fit.g_fit >= 50 ? "#A88540" : "#9A4848";

  const successColor =
    (c.team_integration.y_success ?? 0) >= 75 ? "#3D9A6A" :
    (c.team_integration.y_success ?? 0) >= 50 ? "#A88540" : "#9A4848";

  const subtitle = [
    c.experience_years ? `${c.experience_years} yrs` : null,
    c.location,
  ].filter(Boolean).join(" · ");

  const factors: { label: string; value: number | null; isDelta?: boolean }[] = [
    { label: "F_team", value: c.team_integration.f_team },
    { label: "F_env",  value: c.team_integration.f_env },
    { label: "F_lmx",  value: c.team_integration.f_lmx },
    { label: "ΔTeam",  value: c.team_integration.team_delta, isDelta: true },
  ];

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("crew_profile_id", String(c.crew_profile_id));
        e.dataTransfer.setData("campaign_id", String(campaignId));
        e.dataTransfer.effectAllowed = "copy";
      }}
      className="rounded-xl bg-bg-elevated border border-bg-border
                 hover:border-brand-primary/30 transition-all duration-200
                 cursor-grab active:cursor-grabbing select-none overflow-hidden"
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-start gap-2.5 px-3 pt-3 pb-2.5">
        <AvatarBubble name={c.name} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate text-text-primary leading-tight">
            {c.name}
          </p>
          {subtitle && (
            <p className="text-xs text-muted truncate mt-0.5">{subtitle}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          {c.team_integration.confidence ? (
            <span className={`badge text-xs ${CONFIDENCE_CLS[c.team_integration.confidence]}`}>
              {c.team_integration.confidence}
            </span>
          ) : (
            <span className="badge badge-info text-xs">
              {c.test_status === "pending" ? "Pending" : "—"}
            </span>
          )}
          <span className="text-muted/40 text-xs leading-none">⠿</span>
        </div>
      </div>

      {/* ── Score duo ───────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-px mx-3 mb-2.5 rounded-lg overflow-hidden border border-bg-border">
        {/* Profile Fit */}
        <div className="bg-bg-primary/60 px-2.5 py-2">
          <p className="text-xs text-muted/70 mb-1">Profile Fit</p>
          <p className="text-2xl font-bold leading-none" style={{ color: fitColor }}>
            {Math.round(c.profile_fit.g_fit)}
          </p>
          <p className="text-xs text-muted/60 truncate mt-0.5">{c.profile_fit.fit_label}</p>
          <ScoreBar value={c.profile_fit.g_fit} color={fitColor} />
        </div>
        {/* Team Success */}
        <div className="bg-bg-primary/60 px-2.5 py-2 border-l border-bg-border">
          <p className="text-xs text-muted/70 mb-1">Team Success</p>
          {c.team_integration.y_success != null ? (
            <>
              <p className="text-2xl font-bold leading-none" style={{ color: successColor }}>
                {Math.round(c.team_integration.y_success)}
                <span className="text-sm font-normal">%</span>
              </p>
              <p className="text-xs text-muted/60 truncate mt-0.5">
                {c.team_integration.success_label ?? "—"}
              </p>
              <ScoreBar value={c.team_integration.y_success} color={successColor} />
            </>
          ) : (
            <p className="text-xs text-muted/40 mt-1">
              {c.team_integration.available ? "Computing…" : "No team data"}
            </p>
          )}
        </div>
      </div>

      {/* ── Factor micro-grid ───────────────────────────────────── */}
      {c.team_integration.available && (
        <div className="grid grid-cols-4 gap-1 mx-3 mb-2.5">
          {factors.map(({ label, value, isDelta }) => (
            <div key={label} className="bg-bg-primary/40 rounded-lg px-1.5 py-1.5 text-center">
              <p className="text-xs text-muted/50 leading-none mb-1">{label}</p>
              <p className={`text-xs font-semibold leading-none ${isDelta ? deltaColor(value) : "text-text-primary"}`}>
                {value != null
                  ? isDelta
                    ? `${value >= 0 ? "+" : ""}${value.toFixed(1)}`
                    : value.toFixed(2)
                  : "—"}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* ── Safety flags ────────────────────────────────────────── */}
      {c.profile_fit.safety_flags.length > 0 && (
        <div className="flex gap-1 mx-3 mb-2.5 flex-wrap">
          {c.profile_fit.safety_flags.slice(0, 3).map((f) => (
            <span key={f} className="badge badge-warning text-xs">⚠ {f}</span>
          ))}
        </div>
      )}

      {/* ── Actions ─────────────────────────────────────────────── */}
      <div className="flex gap-1.5 px-3 pb-3">
        <button
          onClick={() => onSimulate(c.crew_profile_id, campaignId)}
          disabled={isSimulating}
          className="btn-primary text-xs py-1.5 px-3 flex-1 justify-center disabled:opacity-40"
        >
          {isSimulating ? "Simulating…" : "Simulate ◉"}
        </button>
        <button
          onClick={() => rejectMutation.mutate()}
          disabled={rejectMutation.isPending}
          className="btn-ghost text-xs py-1.5 px-2.5 text-red-400/60 hover:text-red-400 transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
