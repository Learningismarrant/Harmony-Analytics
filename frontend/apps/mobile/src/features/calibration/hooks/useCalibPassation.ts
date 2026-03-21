import { useState, useEffect, useCallback } from "react";
import { Alert, BackHandler } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibSessionOut, CalibQuestionOut } from "@harmony/types";

export function useCalibPassation(catalogueId: number) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [session, setSession] = useState<CalibSessionOut | null>(null);
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
    setSession(null);
  }, [catalogueId]);

  // Reset le timer quand on change de question
  useEffect(() => {
    setQuestionStartTime(Date.now());
  }, [currentIndex]);

  // Query questions — activée seulement si session existe
  const { data: questions, isLoading: isLoadingQuestions } = useQuery({
    queryKey: calibrationQueryKeys.questions(catalogueId),
    queryFn: () => calibrationApi.getQuestions(catalogueId),
    enabled: session !== null,
    gcTime: 0,
  });

  // Mutation startSession — appelée au mount si session est null
  const startSessionMutation = useMutation({
    mutationFn: () => calibrationApi.startSession(catalogueId),
    onSuccess: (newSession) => {
      setSession(newSession);
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
    },
    onError: () => {
      Alert.alert("Erreur", "Impossible de démarrer la session. Réessayez.");
    },
  });

  // Lancer la session au mount si pas encore créée
  useEffect(() => {
    if (catalogueId > 0 && session === null && !startSessionMutation.isPending) {
      startSessionMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogueId]);

  // Mutation submitResponses
  const submitMutation = useMutation({
    mutationFn: () => {
      if (!session) throw new Error("Pas de session active");
      const responseList = Object.entries(responses).map(([qId, val]) => ({
        question_id: parseInt(qId, 10),
        valeur_choisie: String(val),
        seconds_spent: timeSpent[parseInt(qId, 10)] ?? 0,
      }));
      return calibrationApi.submitSession({
        session_id: session.id,
        responses: responseList,
      });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
      setIsSubmitted(true);
      if (session) {
        router.replace(`/(calibrator)/session/result/${session.id}` as never);
      }
    },
    onError: () => {
      Alert.alert("Erreur", "Échec de l'envoi. Veuillez réessayer.");
    },
  });

  const isLoading = isLoadingQuestions || startSessionMutation.isPending;

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

  function selectAnswer(questionId: number, value: number) {
    if (!questions || questions.length === 0) return;

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
    const unanswered = questions?.filter((q: CalibQuestionOut) => responses[q.id] === undefined).length ?? 0;
    if (unanswered > 0) {
      Alert.alert(
        "Test incomplet",
        `${unanswered} question(s) sans réponse. Soumettre quand même ?`,
        [
          { text: "Revoir", style: "cancel" },
          { text: "Soumettre", onPress: () => submitMutation.mutate() },
        ],
      );
    } else {
      submitMutation.mutate();
    }
  }

  return {
    session,
    questions,
    isLoading,
    currentIndex,
    responses,
    isSubmitted,
    showInstructions,
    setShowInstructions,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
    submitMutation,
  };
}
