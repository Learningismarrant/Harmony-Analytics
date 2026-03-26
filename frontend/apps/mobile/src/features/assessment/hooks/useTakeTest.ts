import { useState, useEffect, useCallback } from "react";
import { Alert, BackHandler } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assessmentApi, queryKeys } from "@harmony/api";
import type { ResponseIn } from "@harmony/types";
import { useLastResultStore } from "@/features/assessment/store/useLastResultStore";

export function useTakeTest(testId: number) {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showInstructions, setShowInstructions] = useState(true);

  // ── SÉCURITÉ 1 : Reset complet quand on change de test ────────────────────
  // Sans ça, naviguer du test 3 vers le test 7 conserverait currentIndex,
  // responses, et isSubmitted du test précédent.
  useEffect(() => {
    setCurrentIndex(0);
    setResponses({});
    setTimeSpent({});
    setIsSubmitted(false);
    setShowInstructions(true);
  }, [testId]);

  const { data: questions, isLoading: isLoadingQuestions } = useQuery({
    queryKey: queryKeys.assessment.questions(testId),
    queryFn: () => assessmentApi.getQuestions(testId),
    gcTime: 0, // Pas de cache vieux — évite les flashs de data entre tests
  });

  const { data: catalogue, isLoading: isLoadingCatalogue } = useQuery({
    queryKey: queryKeys.assessment.catalogue(),
    queryFn: () => assessmentApi.getCatalogue(),
    staleTime: Infinity,
  });

  const testInfo = catalogue?.find((t) => t.id === testId);
  const isLoading = isLoadingQuestions || isLoadingCatalogue;

  // Reset le timer quand on passe à une nouvelle question
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
      useLastResultStore.getState().setLastResult(result);
      queryClient.invalidateQueries({ queryKey: queryKeys.assessment.myResults() });
      queryClient.invalidateQueries({ queryKey: queryKeys.identity.fullProfile(0) });
      setIsSubmitted(true);
    },
    onError: () => {
      Alert.alert("Erreur", "Échec de l'envoi. Veuillez réessayer.");
    },
  });

  // ── SÉCURITÉ 2 : BackHandler Android ─────────────────────────────────────
  // Intercepte le bouton retour physique pendant un test en cours
  // pour éviter une perte de progression accidentelle.
  useFocusEffect(
    useCallback(() => {
      const onBackPress = () => {
        // Laisser passer sans bloquer si on est sur les instructions ou après soumission
        if (showInstructions || isSubmitted || submitMutation.isPending) return false;

        Alert.alert(
          "Analyse en cours",
          "Quitter maintenant annulera votre progression dans ce test.",
          [
            { text: "Rester", style: "cancel" },
            {
              text: "Quitter",
              style: "destructive",
              onPress: () => router.replace("/(candidate)/assessment"),
            },
          ],
        );
        return true; // Bloque le retour natif
      };

      const subscription = BackHandler.addEventListener("hardwareBackPress", onBackPress);
      return () => subscription.remove();
    }, [showInstructions, isSubmitted, submitMutation.isPending, router]),
  );

  const currentQuestionId = questions?.[currentIndex]?.id;
  const canGoNext = currentQuestionId !== undefined && responses[currentQuestionId] !== undefined;
  const canSubmit = questions !== undefined && questions.length > 0 &&
    questions.every((q) => responses[q.id] !== undefined);

  function selectAnswer(questionId: number, value: string) {
    // ── SÉCURITÉ 3 : Guard données ────────────────────────────────────────
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

  /** Sélectionne une réponse et avance automatiquement à la paire suivante.
   *  Conçu pour l'UX swipe T-IRT — appeler depuis onChoose de SwipePairCard.
   *  Sur la dernière question, ne soumet pas automatiquement. */
  function selectAndAdvance(questionId: number, value: string) {
    selectAnswer(questionId, value);
    if (questions && currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
    }
  }

  function handleSubmit() {
    if (!canSubmit) {
      const unanswered = questions?.filter((q) => responses[q.id] === undefined).length ?? 0;
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
    questions,
    testInfo,
    isLoading,
    isSubmitted,
    showInstructions,
    setShowInstructions,
    currentIndex,
    responses,
    canGoNext,
    canSubmit,
    submitMutation,
    selectAnswer,
    selectAndAdvance,
    goNext,
    goPrev,
    handleSubmit,
  };
}
