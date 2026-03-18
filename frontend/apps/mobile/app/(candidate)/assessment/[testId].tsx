import { useEffect } from "react";
import { View, Text, ActivityIndicator, TouchableOpacity } from "react-native";
import { useLocalSearchParams, Stack, useRouter } from "expo-router";
import { useTakeTest } from "@/features/assessment/hooks/useTakeTest";
import { useQuestionTransition } from "@/features/assessment/hooks/useQuestionTransition";
import { useLastResultStore } from "@/features/assessment/store/useLastResultStore";
import { AssessmentHeader } from "@/features/assessment/components/session/AssessmentHeader";
import { AssessmentFooter } from "@/features/assessment/components/session/AssessmentFooter";
import { AssessmentSuccess } from "@/features/assessment/components/session/AssessmentSuccess";
import { InstructionsView } from "@/features/assessment/components/session/InstructionsView";
import { QuestionCard } from "@/features/assessment/components/session/QuestionCard";
import { LikertQuestion } from "@/features/assessment/components/session/LikertQuestion";
import type { RavenMatrixConfig } from "@harmony/types";
import { RavenMatrix } from "@/features/assessment/components/session/RavenMatrix";

export default function TakeTestScreen() {
  const router = useRouter();
  const { testId } = useLocalSearchParams<{ testId: string }>();
  const id = parseInt(testId, 10);

  const {
    questions,
    testInfo,
    isLoading,
    isSubmitted,
    showInstructions,
    setShowInstructions,
    currentIndex,
    responses,
    submitMutation,
    selectAndAdvance,
    handleSubmit,
  } = useTakeTest(id);

  const { animatedStyle, triggerTransition, resetAnimation } = useQuestionTransition();

  useEffect(() => {
    resetAnimation();
  }, [id, resetAnimation]);

  // ── 1. Loading ────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#94A3B8" size="large" />
      </View>
    );
  }

  // ── 2. Succès ─────────────────────────────────────────────────────────────
  if (isSubmitted) {
    const lastResult = useLastResultStore.getState().lastResult;
    return (
      <>
        <Stack.Screen options={{ headerShown: false }} />
        <AssessmentSuccess
          onExit={() =>
            router.replace(
              `/(candidate)/assessment/result?score=${Math.round(lastResult?.global_score ?? 0)}`,
            )
          }
        />
      </>
    );
  }

  // ── 3. Instructions ───────────────────────────────────────────────────────
  if (showInstructions) {
    return (
      <>
        <Stack.Screen options={{ headerShown: false }} />
        <InstructionsView
          data={{
            name: testInfo?.name,
            instructions: testInfo?.instructions,
            test_type: testInfo?.test_type,
          }}
          onStart={() => setShowInstructions(false)}
        />
      </>
    );
  }

  if (!questions || questions.length === 0) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <Text className="text-muted">Aucune question disponible.</Text>
      </View>
    );
  }

  const question = questions[currentIndex];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(responses).length;
  const progress = (currentIndex + 1) / totalQuestions;
  const isLastQuestion = currentIndex === totalQuestions - 1;

  // ── 4. Mode Raven (matrices de raisonnement) ──────────────────────────────
  if (question.question_type === "raven") {
    const config = question.options as unknown as RavenMatrixConfig;

    return (
      <>
        <Stack.Screen
          options={{ title: `${currentIndex + 1} / ${totalQuestions}`, headerBackTitle: "Tests" }}
        />
        <View className="flex-1 bg-bg-primary">
          <AssessmentHeader current={currentIndex} total={totalQuestions} />

          <View className="px-5 pt-2 pb-1 flex-row items-center justify-between">
            <Text className="text-muted text-xs">
              {answeredCount} / {totalQuestions} répondues
            </Text>
            <Text className="text-muted text-xs">{Math.round(progress * 100)} %</Text>
          </View>

          <View className="flex-1 items-center justify-center px-4">
            {config ? (
              <RavenMatrix
                config={config}
                selectedAnswer={responses[question.id]}
                onSelect={(answerId) => selectAndAdvance(question.id, answerId)}
                disabled={submitMutation.isPending}
              />
            ) : (
              <Text className="text-muted">Configuration de la matrice indisponible.</Text>
            )}
          </View>

          {isLastQuestion && (
            <View className="px-5 pb-8 pt-2">
              <TouchableOpacity
                onPress={handleSubmit}
                disabled={submitMutation.isPending}
                className="bg-teak rounded-xl py-4 items-center"
                activeOpacity={0.85}
              >
                {submitMutation.isPending ? (
                  <ActivityIndicator color="#0D1B2A" />
                ) : (
                  <Text className="text-bg-primary font-bold tracking-wider">
                    SOUMETTRE LE TEST
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>
      </>
    );
  }

  // ── 6. Mode Likert (classique) ────────────────────────────────────────────
  return (
    <>
      <Stack.Screen
        options={{
          title: `Question ${currentIndex + 1} / ${totalQuestions}`,
          headerBackTitle: "Tests",
        }}
      />
      <View className="flex-1 bg-bg-primary">
        <AssessmentHeader current={currentIndex} total={totalQuestions} />

        <View className="flex-1 justify-center">
          <QuestionCard
            questionText={question.text}
            questionNumber={currentIndex + 1}
            totalQuestions={totalQuestions}
            animatedStyle={animatedStyle}
          />
        </View>

        {/* Échelle Likert horizontale */}
        <View className="px-6 pb-4">
          <LikertQuestion
            question={question}
            selectedValue={responses[question.id]}
            onSelect={(qId, val) => triggerTransition(() => selectAndAdvance(qId, val))}
          />
        </View>

        {/* Soumettre uniquement sur la dernière question */}
        {isLastQuestion && (
          <View className="px-5 pb-4">
            <TouchableOpacity
              onPress={handleSubmit}
              disabled={submitMutation.isPending}
              className="bg-teak rounded-xl py-4 items-center"
              activeOpacity={0.85}
            >
              {submitMutation.isPending ? (
                <ActivityIndicator color="#0D1B2A" />
              ) : (
                <Text className="text-bg-primary font-bold tracking-wider">SOUMETTRE LE TEST</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        <AssessmentFooter />
      </View>
    </>
  );
}
