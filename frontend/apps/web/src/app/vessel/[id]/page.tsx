"use client";

import { use, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { vesselApi, crewApi, recruitmentApi, queryKeys } from "@harmony/api";
import type { SimulationPreviewOut } from "@harmony/types";
import { Sidebar } from "@/components/layout/Sidebar";
import { CockpitStrip } from "@/components/vessel/CockpitStrip";
import { CampaignPanel } from "@/components/vessel/CampaignPanel";

// Three.js canvas — SSR-incompatible, lazy-loaded on client only
const SociogramCanvas = dynamic(
  () =>
    import("@/components/sociogram/SociogramCanvas").then(
      (m) => m.SociogramCanvas,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-brand-primary/30 border-t-brand-primary
                          rounded-full animate-spin mx-auto mb-3" />
          <p className="text-muted text-sm">Loading molecule…</p>
        </div>
      </div>
    ),
  },
);

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function VesselCockpitPage({ params }: PageProps) {
  const { id } = use(params);
  const yachtId = parseInt(id, 10);
  const queryClient = useQueryClient();

  // ── UI state ──────────────────────────────────────────────────────────────
  const [activeCampaignId, setActiveCampaignId] = useState<number | null>(null);
  const [simulationPreview, setSimulationPreview] =
    useState<SimulationPreviewOut | null>(null);
  const [simulatingFor, setSimulatingFor] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // ── Queries ───────────────────────────────────────────────────────────────
  const { data: vessel } = useQuery({
    queryKey: queryKeys.vessel.byId(yachtId),
    queryFn: () => vesselApi.getById(yachtId),
  });

  const { data: sociogram, isLoading: sociogramLoading } = useQuery({
    queryKey: queryKeys.crew.sociogram(yachtId),
    queryFn: () => crewApi.getSociogram(yachtId),
    retry: false,
  });

  const { data: dashboard } = useQuery({
    queryKey: queryKeys.crew.dashboard(yachtId),
    queryFn: () => crewApi.getDashboard(yachtId),
    retry: false,
  });

  // ── Mutations ─────────────────────────────────────────────────────────────
  const simulateMutation = useMutation({
    mutationFn: (crewProfileId: number) =>
      recruitmentApi.simulateImpact(yachtId, crewProfileId),
    onSuccess: (preview) => setSimulationPreview(preview),
    onError: () => setSimulatingFor(null),
  });

  const hireMutation = useMutation({
    mutationFn: () => {
      if (!activeCampaignId || !simulatingFor)
        throw new Error("No campaign or candidate selected");
      return recruitmentApi.hire(activeCampaignId, simulatingFor);
    },
    onSuccess: () => {
      setSimulationPreview(null);
      setSimulatingFor(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.crew.sociogram(yachtId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.crew.dashboard(yachtId) });
      if (activeCampaignId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.recruitment.matching(activeCampaignId),
        });
      }
    },
  });

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleSimulateCandidate = (crewProfileId: number, campaignId?: number) => {
    setSimulatingFor(crewProfileId);
    if (campaignId !== undefined) setActiveCampaignId(campaignId);
    simulateMutation.mutate(crewProfileId);
  };

  const handleCancelSimulation = () => {
    setSimulationPreview(null);
    setSimulatingFor(null);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // dataTransfer is null for programmatically dispatched events (HTML spec §6.11.3)
    if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    // Only clear when leaving the drop zone itself, not child elements
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const crewProfileId = parseInt(e.dataTransfer.getData("crew_profile_id"), 10);
    const campaignId = parseInt(e.dataTransfer.getData("campaign_id"), 10);
    if (!isNaN(crewProfileId)) {
      handleSimulateCandidate(crewProfileId, isNaN(campaignId) ? undefined : campaignId);
    }
  };

  const isMutating = simulateMutation.isPending || hireMutation.isPending;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Top bar */}
        <div className="h-14 border-b border-bg-border flex items-center px-5 gap-3 shrink-0">
          <Link
            href="/dashboard"
            className="text-muted hover:text-text-primary text-sm transition-colors shrink-0"
          >
            ← Fleet
          </Link>
          <span className="text-bg-border">/</span>

          {vessel ? (
            <>
              <h1 className="font-semibold text-sm">{vessel.name}</h1>
              <span className="text-muted text-xs">{vessel.type} · {vessel.length}m</span>
            </>
          ) : (
            <div className="h-4 w-36 rounded bg-bg-elevated animate-pulse" />
          )}

          {simulatingFor !== null && !simulationPreview && (
            <span className="ml-auto badge badge-info animate-pulse text-xs">
              ◌ Running simulation…
            </span>
          )}
        </div>

        {/* Content row: canvas + campaign panel */}
        <div className="flex-1 flex overflow-hidden">

          {/* ── Canvas (center, drag-drop target) ────────────────────────── */}
          <div
            className="relative flex-1 flex flex-col"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {sociogramLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-12 h-12 border-2 border-brand-primary/30 border-t-brand-primary
                                  rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-muted text-sm">Loading team molecule…</p>
                </div>
              </div>
            ) : sociogram ? (
              <Suspense fallback={null}>
                <SociogramCanvas
                  sociogram={sociogram}
                  simulationPreview={simulationPreview}
                  onSimulationRequest={(crewProfileId) =>
                    handleSimulateCandidate(crewProfileId)
                  }
                  onHireCandidate={() => hireMutation.mutate()}
                  onCancelSimulation={handleCancelSimulation}
                  loadingSimulation={isMutating}
                  className="flex-1 h-full"
                />
              </Suspense>
            ) : (
              <div className="flex-1 flex items-center justify-center text-center px-8">
                <div>
                  <p className="text-5xl mb-4 text-muted">◈</p>
                  <p className="font-semibold text-text-primary mb-2">No crew data yet</p>
                  <p className="text-sm text-muted max-w-xs">
                    Assign crew members using the vessel boarding token, then collect
                    daily pulses to generate the team molecule.
                  </p>
                </div>
              </div>
            )}

            {/* Drop-zone overlay */}
            {dragOver && (
              <div className="absolute inset-0 z-10 pointer-events-none
                             bg-brand-primary/8 border-2 border-dashed border-brand-primary
                             flex items-center justify-center">
                <div className="card py-3 px-8 text-center">
                  <p className="text-brand-primary font-semibold text-base">
                    ◉ Drop to simulate impact
                  </p>
                  <p className="text-muted text-xs mt-0.5">
                    Preview how this candidate reshapes the team molecule
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* ── Campaign panel (right) ────────────────────────────────────── */}
          <CampaignPanel
            yachtId={yachtId}
            activeCampaignId={activeCampaignId}
            onSelectCampaign={setActiveCampaignId}
            simulatingFor={simulatingFor}
            onSimulateCandidate={handleSimulateCandidate}
          />
        </div>

        {/* ── Cockpit strip (bottom) ───────────────────────────────────────── */}
        <CockpitStrip
          dashboard={dashboard}
          fTeamScore={sociogram?.f_team_global}
        />
      </div>
    </div>
  );
}
