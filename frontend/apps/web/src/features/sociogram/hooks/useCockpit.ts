import { useQuery } from "@tanstack/react-query";
import { crewApi, queryKeys } from "@harmony/api";
import type { SociogramOut, DashboardOut } from "@harmony/types";

export function useCockpit(yachtId: number): {
  sociogram: SociogramOut | undefined;
  dashboard: DashboardOut | undefined;
  sociogramLoading: boolean;
} {
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

  return { sociogram, dashboard, sociogramLoading };
}
