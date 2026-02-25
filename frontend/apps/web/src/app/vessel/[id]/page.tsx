"use client";

import { use, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { Sidebar } from "@/shared/components/Sidebar";
import { CockpitStrip } from "@/features/vessel/components/CockpitStrip";
import { CampaignPanel } from "@/features/recruitment/components/CampaignPanel";
import { useVessel } from "@/features/vessel/hooks/useVessel";
import { useCockpit } from "@/features/sociogram/hooks/useCockpit";
import { useSimulation } from "@/features/vessel/hooks/useSimulation";

// Three.js canvas — SSR-incompatible, lazy-loaded on client only
const SociogramCanvas = dynamic(
  () =>
    import("@/features/sociogram/components/SociogramCanvas").then(
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

  // ── UI state ──────────────────────────────────────────────────────────────
  const [activeCampaignId, setActiveCampaignId] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);

  // ── Data hooks ────────────────────────────────────────────────────────────
  const { vessel } = useVessel(yachtId);
  const { sociogram, dashboard, sociogramLoading } = useCockpit(yachtId);
  const {
    simulationPreview,
    simulatingFor,
    isMutating,
    handleSimulateCandidate,
    handleHire,
    handleCancelSimulation,
  } = useSimulation(yachtId, activeCampaignId, setActiveCampaignId);

  // ── Drag handlers ─────────────────────────────────────────────────────────
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
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
                  onHireCandidate={handleHire}
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
