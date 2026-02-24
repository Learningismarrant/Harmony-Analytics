"use client";

import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { crewApi, recruitmentApi, queryKeys } from "@harmony/api";
import type { SimulationPreviewOut } from "@harmony/types";
import { useState, Suspense } from "react";
import { Sidebar } from "@/components/layout/Sidebar";

// Lazy-load the 3D canvas — Three.js is large and SSR-incompatible
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

function SociogramPageContent() {
  const searchParams = useSearchParams();
  const yachtIdParam = searchParams.get("yacht");
  const yachtId = yachtIdParam ? parseInt(yachtIdParam, 10) : null;

  const queryClient = useQueryClient();
  const [simulationPreview, setSimulationPreview] =
    useState<SimulationPreviewOut | null>(null);
  const [simulatingFor, setSimulatingFor] = useState<number | null>(null);

  // ── Data fetching ──────────────────────────────────────────────────────────
  const { data: sociogram, isLoading, error } = useQuery({
    queryKey: queryKeys.crew.sociogram(yachtId ?? 0),
    queryFn: () => crewApi.getSociogram(yachtId!),
    enabled: yachtId !== null,
  });

  // ── Simulation mutation ────────────────────────────────────────────────────
  const simulateMutation = useMutation({
    mutationFn: (crewProfileId: number) =>
      recruitmentApi.simulateImpact(yachtId!, crewProfileId),
    onSuccess: (preview) => {
      setSimulationPreview(preview);
    },
  });

  const handleSimulationRequest = (crewProfileId: number) => {
    setSimulatingFor(crewProfileId);
    simulateMutation.mutate(crewProfileId);
  };

  const handleCancelSimulation = () => {
    setSimulationPreview(null);
    setSimulatingFor(null);
  };

  // Hire mutation
  const hireMutation = useMutation({
    mutationFn: async () => {
      // Find the open campaign for this yacht (simplified: use first open campaign)
      // In production: pass campaignId explicitly
      if (!simulatingFor) throw new Error("No candidate selected");
    },
    onSuccess: () => {
      setSimulationPreview(null);
      setSimulatingFor(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.crew.sociogram(yachtId ?? 0) });
    },
  });

  // ── Render ─────────────────────────────────────────────────────────────────
  if (!yachtId) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted">
        <div className="text-center">
          <p className="text-4xl mb-3">◉</p>
          <p className="font-medium mb-1">No vessel selected</p>
          <p className="text-sm">Select a vessel from the dashboard to view its molecule.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-primary/30 border-t-brand-primary
                        rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !sociogram) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted">
        <p>Failed to load sociogram. Is the crew assigned to this vessel?</p>
      </div>
    );
  }

  return (
    <SociogramCanvas
      sociogram={sociogram}
      simulationPreview={simulationPreview}
      onSimulationRequest={handleSimulationRequest}
      onHireCandidate={() => hireMutation.mutate()}
      onCancelSimulation={handleCancelSimulation}
      loadingSimulation={simulateMutation.isPending || hireMutation.isPending}
      className="flex-1 h-full"
    />
  );
}

export default function SociogramPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="h-14 border-b border-bg-border flex items-center px-6 gap-4 shrink-0">
          <h1 className="font-semibold">Team Molecule</h1>
          <span className="text-xs text-muted">
            Interactive 3D sociogram — click a node to inspect, drag to orbit
          </span>
        </div>

        <Suspense
          fallback={
            <div className="flex-1 flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-brand-primary/30 border-t-brand-primary
                              rounded-full animate-spin" />
            </div>
          }
        >
          <SociogramPageContent />
        </Suspense>
      </div>
    </div>
  );
}
