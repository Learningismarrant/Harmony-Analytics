import { useState, useEffect } from "react";
import { Alert } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assessmentApi, queryKeys } from "@harmony/api";
import type { ResponseIn } from "@harmony/types";

export function useTakeTest(testId: number) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});

  const { data: questions, isLoading } = useQuery({
    queryKey: queryKeys.assessment.questions(testId),
    queryFn: () => assessmentApi.getQuestions(testId),
  });

  useEffect(() => {
    setQuestionStartTime(Date.now());
  }, [currentIndex]);

  const submitMutation = useMutation({
    mutationFn: () => {
      const responseList: ResponseIn[] = Object.entries(responses).map(
        ([questionId, value]) => ({
          question_id: parseInt(questionId, 10),
          valeur_choisie: value,
          seconds_spent: timeSpent[parseInt(questionId, 10)],
        }),
      );
      return assessmentApi.submit({ test_id: testId, responses: responseList });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.assessment.myResults() });
      queryClient.invalidateQueries({ queryKey: queryKeys.identity.fullProfile(0) });
      router.replace(`/(candidate)/assessment/result?score=${Math.round(result.global_score)}`);
    },
    onError: () => {
      Alert.alert("Error", "Failed to submit test. Please try again.");
    },
  });

  function selectAnswer(questionId: number, value: string) {
    const elapsed = (Date.now() - questionStartTime) / 1000;
    setTimeSpent((prev) => ({ ...prev, [questionId]: elapsed }));
    setResponses((prev) => ({ ...prev, [questionId]: value }));
  }

  function goNext() {
    if (questions && currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
    }
  }

  function goPrev() {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
    }
  }

  function handleSubmit() {
    const unanswered = questions?.filter((q) => !responses[q.id]).length ?? 0;
    if (unanswered > 0) {
      Alert.alert(
        "Incomplete",
        `${unanswered} question(s) still unanswered. Submit anyway?`,
        [
          { text: "Review", style: "cancel" },
          { text: "Submit", onPress: () => submitMutation.mutate() },
        ],
      );
    } else {
      submitMutation.mutate();
    }
  }

  return {
    questions,
    isLoading,
    currentIndex,
    responses,
    submitMutation,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
  };
}
