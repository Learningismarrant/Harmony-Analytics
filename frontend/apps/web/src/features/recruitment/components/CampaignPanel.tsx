"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { CampaignOut } from "@harmony/types";
import { CandidateCard } from "./CandidateCard";
import { NewCampaignForm } from "./NewCampaignForm";

export interface CampaignPanelProps {
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
