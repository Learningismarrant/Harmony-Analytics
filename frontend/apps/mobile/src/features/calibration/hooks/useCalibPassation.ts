import { useState, useEffect, useCallback } from "react";
import { Alert, BackHandler } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibSessionOut, CalibQuestionOut } from "@harmony/types";

export function useCalibPassation(catalogueId: number, initialSessionId?: number) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [session, setSession] = useState<CalibSessionOut | null>(
    initialSessionId ? ({ id: initialSessionId, catalogue_id: catalogueId } as CalibSessionOut) : null,
  );
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, number>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  // Reset complet si catalogueId change — ne pas reset la session si initialSessionId fourni
  // (le useState a déjà initialisé la session, le useEffect ne doit pas l'écraser au mount)
  useEffect(() => {
    setCurrentIndex(0);
    setResponses({});
    setTimeSpent({});
    setIsSubmitted(false);
    setShowInstructions(true);
    if (!initialSessionId) {
      setSession(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // Lancer la session au mount si pas encore créée (skip si initialSessionId fourni)
  useEffect(() => {
    if (catalogueId > 0 && session === null && !initialSessionId && !startSessionMutation.isPending) {
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
        response_value: String(val),
        seconds_spent: timeSpent[parseInt(qId, 10)] ?? 0,
      }));
      return calibrationApi.submitResponses(session.id, { responses: responseList });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
      setIsSubmitted(true);
      if (session) {
        router.replace(`/(calibrator)/session/result/${session.id}` as never);
      }
    },
    onError: (error: unknown) => {
      // 409 = session déjà complète → rediriger vers les résultats plutôt qu'afficher une erreur
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 409 && session) {
        queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
        router.replace(`/(calibrator)/session/result/${session.id}` as never);
        return;
      }
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
    session,
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
