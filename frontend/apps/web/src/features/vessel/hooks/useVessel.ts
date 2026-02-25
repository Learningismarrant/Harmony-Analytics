import { useQuery } from "@tanstack/react-query";
import { vesselApi, queryKeys } from "@harmony/api";
import type { YachtOut } from "@harmony/types";

export function useVessel(yachtId: number): {
  vessel: YachtOut | undefined;
  isLoading: boolean;
} {
  const { data: vessel, isLoading } = useQuery({
    queryKey: queryKeys.vessel.byId(yachtId),
    queryFn: () => vesselApi.getById(yachtId),
  });
  return { vessel, isLoading };
}
