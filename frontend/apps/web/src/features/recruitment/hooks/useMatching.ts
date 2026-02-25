import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { MatchResultOut } from "@harmony/types";

export function useMatching(campaignId: number | null): {
  candidates: MatchResultOut[];
  isLoading: boolean;
  reject: (crewProfileId: number) => void;
} {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.recruitment.matching(campaignId ?? 0),
    queryFn: () => recruitmentApi.getMatching(campaignId!),
    enabled: campaignId !== null,
    retry: false,
  });

  // Sort: hired last, rejected hidden, rest by y_success desc
  const candidates = [...(data ?? [])].sort((a, b) => {
    if (a.is_hired && !b.is_hired) return 1;
    if (!a.is_hired && b.is_hired) return -1;
    return (b.team_integration.y_success ?? 0) - (a.team_integration.y_success ?? 0);
  });

  const rejectMutation = useMutation({
    mutationFn: (crewProfileId: number) =>
      recruitmentApi.reject(campaignId!, crewProfileId),
    onSuccess: () => {
      if (campaignId !== null) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.recruitment.matching(campaignId),
        });
      }
    },
  });

  return {
    candidates,
    isLoading,
    reject: (crewProfileId) => rejectMutation.mutate(crewProfileId),
  };
}
