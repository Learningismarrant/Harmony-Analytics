import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { SimulationPreviewOut } from "@harmony/types";

export function useSimulation(
  yachtId: number,
  activeCampaignId: number | null,
  onCampaignChange: (id: number) => void,
): {
  simulationPreview: SimulationPreviewOut | null;
  simulatingFor: number | null;
  isMutating: boolean;
  handleSimulateCandidate: (crewProfileId: number, campaignId?: number) => void;
  handleHire: () => void;
  handleCancelSimulation: () => void;
} {
  const queryClient = useQueryClient();

  const [simulationPreview, setSimulationPreview] =
    useState<SimulationPreviewOut | null>(null);
  const [simulatingFor, setSimulatingFor] = useState<number | null>(null);

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

  const handleSimulateCandidate = (crewProfileId: number, campaignId?: number) => {
    setSimulatingFor(crewProfileId);
    if (campaignId !== undefined) onCampaignChange(campaignId);
    simulateMutation.mutate(crewProfileId);
  };

  return {
    simulationPreview,
    simulatingFor,
    isMutating: simulateMutation.isPending || hireMutation.isPending,
    handleSimulateCandidate,
    handleHire: () => hireMutation.mutate(),
    handleCancelSimulation: () => {
      setSimulationPreview(null);
      setSimulatingFor(null);
    },
  };
}
