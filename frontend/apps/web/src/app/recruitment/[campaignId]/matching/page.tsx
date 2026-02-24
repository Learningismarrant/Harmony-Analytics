"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import Link from "next/link";

interface PageProps {
  params: Promise<{ campaignId: string }>;
}

function ConfidenceBadge({ confidence }: { confidence: string | null }) {
  const styles: Record<string, string> = {
    HIGH: "badge-success",
    MEDIUM: "badge-warning",
    LOW: "badge-danger",
  };
  if (!confidence) return null;
  return <span className={`badge ${styles[confidence] ?? "badge-info"}`}>{confidence}</span>;
}

function ScoreRing({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value);
  const color =
    pct >= 75 ? "#22C55E" : pct >= 55 ? "#F59E0B" : "#EF4444";
  const circumference = 2 * Math.PI * 16;
  const dashOffset = circumference * (1 - pct / 100);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={40} height={40} viewBox="0 0 40 40">
        <circle cx={20} cy={20} r={16} fill="none" stroke="#1E2733" strokeWidth={3} />
        <circle
          cx={20}
          cy={20}
          r={16}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 20 20)"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
        <text
          x={20}
          y={24}
          textAnchor="middle"
          fontSize={9}
          fill={color}
          fontWeight="600"
        >
          {pct}
        </text>
      </svg>
      <span className="text-muted text-xs">{label}</span>
    </div>
  );
}

export default function MatchingPage({ params }: PageProps) {
  const { campaignId } = use(params);
  const id = parseInt(campaignId, 10);

  const { data: results, isLoading } = useQuery({
    queryKey: queryKeys.recruitment.matching(id),
    queryFn: () => recruitmentApi.getMatching(id),
  });

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* Back */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="h-14 border-b border-bg-border flex items-center px-6 gap-3 shrink-0">
          <Link href="/recruitment" className="text-muted hover:text-text-primary text-sm">
            ← Campaigns
          </Link>
          <span className="text-bg-border">/</span>
          <h1 className="font-semibold text-sm">Matching results</h1>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="card h-24 animate-pulse bg-bg-elevated" />
              ))}
            </div>
          ) : (
            <div className="space-y-3 max-w-3xl">
              {results?.map((r, idx) => (
                <div
                  key={r.crew_profile_id}
                  className="card flex items-center gap-4 hover:border-brand-primary/30 transition-colors"
                >
                  {/* Rank */}
                  <div className="w-7 h-7 rounded-full bg-bg-elevated border border-bg-border
                                  flex items-center justify-center text-xs text-muted shrink-0">
                    {idx + 1}
                  </div>

                  {/* Avatar placeholder */}
                  <div className="w-9 h-9 rounded-full bg-brand-primary/20 border border-brand-primary/30
                                  flex items-center justify-center shrink-0">
                    <span className="text-brand-primary text-sm font-medium">
                      {r.name.charAt(0)}
                    </span>
                  </div>

                  {/* Identity */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="font-medium text-sm">{r.name}</p>
                      <ConfidenceBadge confidence={r.team_integration.confidence} />
                      {r.test_status === "pending" && (
                        <span className="badge badge-warning">Tests pending</span>
                      )}
                    </div>
                    <p className="text-xs text-muted">
                      {r.experience_years} yr exp
                      {r.location ? ` · ${r.location}` : ""}
                    </p>
                    {r.profile_fit.safety_flags.length > 0 && (
                      <div className="flex gap-1 mt-1">
                        {r.profile_fit.safety_flags.slice(0, 2).map((flag) => (
                          <span key={flag} className="badge badge-warning text-xs">
                            ⚠ {flag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Scores */}
                  <div className="flex gap-4 shrink-0">
                    <ScoreRing value={r.profile_fit.g_fit} label="Fit" />
                    <ScoreRing value={r.team_integration.y_success ?? 0} label="Ŷ" />
                    {r.team_integration.team_delta != null && (
                      <div className="flex flex-col items-center gap-1">
                        <div
                          className={`text-sm font-semibold ${
                            r.team_integration.team_delta >= 0 ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {r.team_integration.team_delta >= 0 ? "+" : ""}
                          {r.team_integration.team_delta.toFixed(1)}
                        </div>
                        <span className="text-muted text-xs">ΔTeam</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  {!r.is_hired && !r.is_rejected && (
                    <div className="flex gap-2 shrink-0">
                      <button className="btn-primary text-xs py-1.5 px-3">Hire</button>
                      <button className="btn-ghost text-xs py-1.5 px-3">Reject</button>
                    </div>
                  )}
                  {r.is_hired && <span className="badge badge-success">Hired</span>}
                  {r.is_rejected && <span className="badge badge-danger">Rejected</span>}
                </div>
              ))}

              {results?.length === 0 && (
                <div className="text-center text-muted py-12">
                  <p className="text-3xl mb-3">⊘</p>
                  <p>No candidates found. Share the invite link to attract applicants.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
