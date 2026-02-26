import { useQuery } from "@tanstack/react-query";
import { assessmentApi, queryKeys } from "@harmony/api";

export function useAssessment() {
  const { data: catalogue, isLoading: loadingCatalogue } = useQuery({
    queryKey: queryKeys.assessment.catalogue(),
    queryFn: () => assessmentApi.getCatalogue(),
  });

  const { data: myResults, isLoading: loadingResults } = useQuery({
    queryKey: queryKeys.assessment.myResults(),
    queryFn: () => assessmentApi.getMyResults(),
  });

  const completedTestIds = new Set(myResults?.map((r) => r.test_id) ?? []);
  const isLoading = loadingCatalogue || loadingResults;

  return { catalogue, myResults, completedTestIds, isLoading };
}
