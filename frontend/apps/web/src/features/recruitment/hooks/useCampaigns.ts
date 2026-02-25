import { useQuery } from "@tanstack/react-query";
import { recruitmentApi, queryKeys } from "@harmony/api";
import type { CampaignOut } from "@harmony/types";

export function useCampaigns(yachtId: number): {
  campaigns: CampaignOut[];
  isLoading: boolean;
} {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.recruitment.campaigns(),
    queryFn: recruitmentApi.getCampaigns,
  });

  const campaigns = (data ?? []).filter(
    (c) => c.yacht_id === yachtId && !c.is_archived,
  );

  return { campaigns, isLoading };
}
