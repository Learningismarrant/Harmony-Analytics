import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { surveyApi, queryKeys } from "@harmony/api";
import type { SurveyResponseIn } from "@harmony/types";

export function useSurvey() {
  const queryClient = useQueryClient();

  const pendingQuery = useQuery({
    queryKey: queryKeys.survey.pending(),
    queryFn: () => surveyApi.getPending(),
  });

  const respondMutation = useMutation({
    mutationFn: ({ surveyId, body }: { surveyId: number; body: SurveyResponseIn }) =>
      surveyApi.respond(surveyId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.survey.pending() });
    },
  });

  return {
    pendingSurveys: pendingQuery.data ?? [],
    isLoading: pendingQuery.isLoading,
    isError: pendingQuery.isError,
    respond: respondMutation.mutateAsync,
    isSubmitting: respondMutation.isPending,
  };
}
