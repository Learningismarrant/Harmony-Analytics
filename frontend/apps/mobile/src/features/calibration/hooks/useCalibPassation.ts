import { useState, useEffect, useCallback } from "react";
import { Alert, BackHandler } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibSessionOut, CalibQuestionOut } from "@harmony/types";

export function useCalibPassation(catalogueId: number, realSession: CalibSessionOut | null) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, number>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  // Reset complet si catalogueId change
  useEffect(() => {
    setCurrentIndex(0);
    setResponses({});
    setTimeSpent({});
    setIsSubmitted(false);
    setShowInstructions(true);
  }, [catalogueId]);

  // Reset le timer quand on change de question
  useEffect(() => {
    setQuestionStartTime(Date.now());
  }, [currentIndex]);

  // Query questions — activée seulement si session existe et n'est pas encore complète
  const { data: questions, isLoading: isLoadingQuestions } = useQuery({
    queryKey: calibrationQueryKeys.questions(catalogueId),
    queryFn: () => calibrationApi.getQuestions(catalogueId),
    enabled: realSession !== null && realSession.completed_at === null,
    gcTime: 0,
  });

  // Mutation submitResponses
  const submitMutation = useMutation({
    mutationFn: () => {
      if (!realSession) throw new Error("Pas de session active");
      const responseList = Object.entries(responses).map(([qId, val]) => ({
        question_id: parseInt(qId, 10),
        response_value: String(val),
        seconds_spent: timeSpent[parseInt(qId, 10)] ?? 0,
      }));
      return calibrationApi.submitResponses(realSession.id, { responses: responseList });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
      setIsSubmitted(true);
      if (realSession) {
        router.replace(`/(calibrator)/session/result/${realSession.id}` as never);
      }
    },
    onError: (error: unknown) => {
      // 409 = session déjà complète → rediriger vers les résultats plutôt qu'afficher une erreur
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 409 && realSession) {
        queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
        router.replace(`/(calibrator)/session/result/${realSession.id}` as never);
        return;
      }
      Alert.alert("Erreur", "Échec de l'envoi. Veuillez réessayer.");
    },
  });

  const isLoading = isLoadingQuestions;

  // BackHandler Android — identique à useTakeTest
  useFocusEffect(
    useCallback(() => {
      const onBackPress = () => {
        if (showInstructions || isSubmitted || submitMutation.isPending) return false;

        Alert.alert(
          "Session en cours",
          "Quitter maintenant annulera votre progression dans ce test.",
          [
            { text: "Rester", style: "cancel" },
            {
              text: "Quitter",
              style: "destructive",
              onPress: () => router.replace("/(calibrator)/catalogues" as never),
            },
          ],
        );
        return true;
      };

      const subscription = BackHandler.addEventListener("hardwareBackPress", onBackPress);
      return () => subscription.remove();
    }, [showInstructions, isSubmitted, submitMutation.isPending, router]),
  );

  const currentQuestionId = questions?.[currentIndex]?.id;
  const canGoNext = currentQuestionId !== undefined && responses[currentQuestionId] !== undefined;
  const canSubmit = questions !== undefined && questions.length > 0 &&
    questions.every((q: CalibQuestionOut) => responses[q.id] !== undefined);

  function selectAnswer(questionId: number, value: number) {
    if (!questions || questions.length === 0) return;

    const elapsed = (Date.now() - questionStartTime) / 1000;
    setTimeSpent((prev) => ({ ...prev, [questionId]: elapsed }));
    setResponses((prev) => ({ ...prev, [questionId]: value }));
  }

  function goNext() {
    if (!canGoNext) return;
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
    if (!canSubmit) {
      const unanswered = questions?.filter((q: CalibQuestionOut) => responses[q.id] === undefined).length ?? 0;
      Alert.alert(
        "Test incomplet",
        `${unanswered} question(s) sans réponse. Veuillez répondre à toutes les questions avant de soumettre.`,
        [{ text: "OK" }],
      );
      return;
    }
    submitMutation.mutate();
  }

  return {
    session: realSession,
    questions,
    isLoading,
    currentIndex,
    responses,
    isSubmitted,
    showInstructions,
    setShowInstructions,
    canGoNext,
    canSubmit,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
    submitMutation,
  };
}
