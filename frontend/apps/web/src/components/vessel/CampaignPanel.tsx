"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { CampaignOut, MatchResultOut, YachtPosition } from "@harmony/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

const CONFIDENCE_CLS: Record<string, string> = {
  HIGH: "badge-success",
  MEDIUM: "badge-warning",
  LOW: "badge-danger",
};

function deltaColor(v: number | null) {
  return (v ?? 0) >= 0 ? "text-green-400" : "text-red-400";
}

// ── New-campaign inline form ───────────────────────────────────────────────────

const POSITIONS: YachtPosition[] = [
  "Captain",
  "First Mate",
  "Bosun",
  "Deckhand",
  "Chief Engineer",
  "2nd Engineer",
  "Chief Stewardess",
  "Stewardess",
  "Chef",
];

interface NewCampaignFormProps {
  yachtId: number;
  onCreated: (campaign: CampaignOut) => void;
  onCancel: () => void;
}

function NewCampaignForm({ yachtId, onCreated, onCancel }: NewCampaignFormProps) {
  const [title, setTitle] = useState("");
  const [position, setPosition] = useState<string>(POSITIONS[3]); // Deckhand default

  const mutation = useMutation({
    mutationFn: () =>
      recruitmentApi.createCampaign({ title, position, yacht_id: yachtId }),
    onSuccess: (campaign) => onCreated(campaign),
  });

  return (
    <div className="p-3 border-b border-bg-border bg-bg-elevated space-y-2">
      <p className="text-xs font-semibold text-muted uppercase tracking-wider">New campaign</p>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Campaign title"
        className="w-full bg-bg-primary border border-bg-border rounded px-2 py-1.5
                   text-sm text-text-primary placeholder:text-muted
                   focus:outline-none focus:border-brand-primary transition-colors"
      />
      <select
        value={position}
        onChange={(e) => setPosition(e.target.value)}
        className="w-full bg-bg-primary border border-bg-border rounded px-2 py-1.5
                   text-sm text-text-primary focus:outline-none focus:border-brand-primary"
      >
        {POSITIONS.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
      <div className="flex gap-2">
        <button
          onClick={() => mutation.mutate()}
          disabled={!title.trim() || mutation.isPending}
          className="btn-primary text-xs py-1.5 px-3 flex-1 justify-center disabled:opacity-40"
        >
          {mutation.isPending ? "Creating…" : "Create"}
        </button>
        <button onClick={onCancel} className="btn-ghost text-xs py-1.5 px-3">
          Cancel
        </button>
      </div>
    </div>
  );
}

// ── Candidate card ─────────────────────────────────────────────────────────────

interface CandidateCardProps {
  candidate: MatchResultOut;
  campaignId: number;
  isSimulating: boolean;
  onSimulate: (crewProfileId: number, campaignId: number) => void;
}

function CandidateCard({
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
      <div className="p-2 rounded-lg bg-bg-elevated border border-bg-border opacity-60">
        <div className="flex items-center gap-2">
          <AvatarBubble name={c.name} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium truncate">{c.name}</p>
          </div>
          <span className="badge badge-success text-xs">Hired</span>
        </div>
      </div>
    );
  }

  if (c.is_rejected) return null;

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("crew_profile_id", String(c.crew_profile_id));
        e.dataTransfer.setData("campaign_id", String(campaignId));
        e.dataTransfer.effectAllowed = "copy";
      }}
      className="p-2 rounded-lg bg-bg-elevated border border-bg-border
                 hover:border-brand-primary/40 transition-colors cursor-grab active:cursor-grabbing
                 select-none"
    >
      {/* Header row */}
      <div className="flex items-center gap-2 mb-1.5">
        {/* Drag handle */}
        <span className="text-muted text-sm shrink-0">⠿</span>
        <AvatarBubble name={c.name} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{c.name}</p>
          {c.location && (
            <p className="text-xs text-muted truncate">{c.location}</p>
          )}
        </div>
        <span className={`badge text-xs ${CONFIDENCE_CLS[c.team_integration.confidence ?? "LOW"]}`}>
          {c.team_integration.confidence ?? "—"}
        </span>
      </div>

      {/* Score row */}
      <div className="flex items-center gap-3 text-xs pl-7">
        <span className="text-muted">
          Fit <span className="text-text-primary font-medium">{Math.round(c.profile_fit.g_fit)}</span>
        </span>
        <span className="text-muted">
          Ŷ <span className="text-text-primary font-medium">
            {c.team_integration.y_success != null ? Math.round(c.team_integration.y_success) : "—"}
          </span>
        </span>
        {c.team_integration.team_delta != null && (
          <span className={`font-medium ${deltaColor(c.team_integration.team_delta)}`}>
            {c.team_integration.team_delta >= 0 ? "+" : ""}{c.team_integration.team_delta.toFixed(1)} ΔTeam
          </span>
        )}
      </div>

      {/* Safety flags */}
      {c.profile_fit.safety_flags.length > 0 && (
        <div className="flex gap-1 mt-1.5 pl-7 flex-wrap">
          {c.profile_fit.safety_flags.slice(0, 2).map((f) => (
            <span key={f} className="badge badge-warning text-xs">⚠ {f}</span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-1.5 mt-2 pl-7">
        <button
          onClick={() => onSimulate(c.crew_profile_id, campaignId)}
          disabled={isSimulating}
          className="btn-primary text-xs py-1 px-2 flex-1 justify-center disabled:opacity-40"
        >
          {isSimulating ? "Simulating…" : "Simulate ◉"}
        </button>
        <button
          onClick={() => rejectMutation.mutate()}
          disabled={rejectMutation.isPending}
          className="btn-ghost text-xs py-1 px-2 text-red-400 hover:text-red-300"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

function AvatarBubble({ name }: { name: string }) {
  return (
    <div className="w-6 h-6 rounded-full bg-brand-primary/20 border border-brand-primary/30
                    flex items-center justify-center shrink-0">
      <span className="text-brand-primary text-xs font-medium">
        {name.charAt(0).toUpperCase()}
      </span>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

interface CampaignPanelProps {
  yachtId: number;
  activeCampaignId: number | null;
  onSelectCampaign: (id: number | null) => void;
  simulatingFor: number | null;
  onSimulateCandidate: (crewProfileId: number, campaignId: number) => void;
}

export function CampaignPanel({
  yachtId,
  activeCampaignId,
  onSelectCampaign,
  simulatingFor,
  onSimulateCandidate,
}: CampaignPanelProps) {
  const queryClient = useQueryClient();
  const [showNewForm, setShowNewForm] = useState(false);

  // All campaigns — filtered client-side by yacht_id
  const { data: allCampaigns, isLoading: campaignsLoading } = useQuery({
    queryKey: queryKeys.recruitment.campaigns(),
    queryFn: recruitmentApi.getCampaigns,
  });

  const campaigns = (allCampaigns ?? []).filter(
    (c) => c.yacht_id === yachtId && !c.is_archived,
  );

  // Active campaign matching results
  const { data: candidates, isLoading: matchingLoading } = useQuery({
    queryKey: queryKeys.recruitment.matching(activeCampaignId ?? 0),
    queryFn: () => recruitmentApi.getMatching(activeCampaignId!),
    enabled: activeCampaignId !== null,
    retry: false,
  });

  const handleCampaignCreated = (campaign: CampaignOut) => {
    setShowNewForm(false);
    queryClient.invalidateQueries({ queryKey: queryKeys.recruitment.campaigns() });
    onSelectCampaign(campaign.id);
  };

  // Sort candidates: hired last, rejected hidden, rest by y_success desc
  const sortedCandidates = [...(candidates ?? [])].sort((a, b) => {
    if (a.is_hired && !b.is_hired) return 1;
    if (!a.is_hired && b.is_hired) return -1;
    return (b.team_integration.y_success ?? 0) - (a.team_integration.y_success ?? 0);
  });

  return (
    <aside className="w-72 flex flex-col border-l border-bg-border bg-bg-secondary overflow-hidden shrink-0">

      {/* Header */}
      <div className="h-14 border-b border-bg-border flex items-center px-3 gap-2 shrink-0">
        <span className="text-sm font-semibold flex-1">Recruitment</span>
        <button
          onClick={() => setShowNewForm((v) => !v)}
          className="btn-primary text-xs py-1 px-2.5"
        >
          + New
        </button>
      </div>

      {/* New campaign form (slide-down) */}
      {showNewForm && (
        <NewCampaignForm
          yachtId={yachtId}
          onCreated={handleCampaignCreated}
          onCancel={() => setShowNewForm(false)}
        />
      )}

      {/* Campaign tabs */}
      <div className="border-b border-bg-border shrink-0">
        {campaignsLoading ? (
          <div className="p-3 flex gap-2">
            {[0, 1].map((i) => (
              <div key={i} className="h-7 w-20 rounded bg-bg-elevated animate-pulse" />
            ))}
          </div>
        ) : campaigns.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-xs text-muted">No campaigns for this vessel.</p>
            <button
              onClick={() => setShowNewForm(true)}
              className="text-xs text-brand-primary hover:underline mt-1"
            >
              Create the first one
            </button>
          </div>
        ) : (
          <div className="flex overflow-x-auto px-2 py-2 gap-1.5 scrollbar-none">
            {campaigns.map((c) => (
              <button
                key={c.id}
                onClick={() => onSelectCampaign(activeCampaignId === c.id ? null : c.id)}
                className={`shrink-0 text-xs px-2.5 py-1.5 rounded-lg transition-colors border ${
                  activeCampaignId === c.id
                    ? "bg-brand-primary/15 border-brand-primary/40 text-brand-primary font-medium"
                    : "border-bg-border text-muted hover:text-text-primary hover:bg-bg-elevated"
                }`}
              >
                {c.position}
                <span className="ml-1.5 text-muted text-xs">{c.candidate_count}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Candidate list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {activeCampaignId === null ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <p className="text-3xl mb-3 text-muted">⊕</p>
            <p className="text-sm text-muted">Select a campaign to see candidates</p>
            <p className="text-xs text-muted mt-1">
              Drag a candidate onto the molecule to preview their team impact
            </p>
          </div>
        ) : matchingLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-20 rounded-lg bg-bg-elevated animate-pulse" />
            ))}
          </div>
        ) : sortedCandidates.length === 0 ? (
          <div className="text-center py-8 text-muted">
            <p className="text-2xl mb-2">⊘</p>
            <p className="text-xs">No candidates yet.</p>
            <p className="text-xs mt-1">Share the invite link to attract applicants.</p>
          </div>
        ) : (
          sortedCandidates.map((candidate) => (
            <CandidateCard
              key={candidate.crew_profile_id}
              candidate={candidate}
              campaignId={activeCampaignId}
              isSimulating={simulatingFor === candidate.crew_profile_id}
              onSimulate={onSimulateCandidate}
            />
          ))
        )}
      </div>

      {/* Campaign invite link */}
      {activeCampaignId !== null && campaigns.find((c) => c.id === activeCampaignId) && (
        <div className="border-t border-bg-border p-3 shrink-0">
          <p className="text-xs text-muted mb-1">Invite link</p>
          <code className="text-xs text-brand-primary break-all">
            {campaigns.find((c) => c.id === activeCampaignId)?.invite_token}
          </code>
        </div>
      )}
    </aside>
  );
}
