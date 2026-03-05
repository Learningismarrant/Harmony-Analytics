import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useLocalSearchParams, Stack } from "expo-router";
import { useTakeTest } from "@/features/assessment/hooks/useTakeTest";
import { LikertQuestion } from "@/features/assessment/components/LikertQuestion";
import { SwipePairCard } from "@/features/assessment/components/SwipePairCard";
import type { ForcedChoiceOption } from "@harmony/types";

export default function TakeTestScreen() {
  const { testId } = useLocalSearchParams<{ testId: string }>();
  const id = parseInt(testId, 10);

  const {
    questions,
    isLoading,
    currentIndex,
    responses,
    submitMutation,
    selectAndAdvance,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
  } = useTakeTest(id);

  if (isLoading || !questions) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#4A90B8" size="large" />
        <Text className="text-muted mt-3">Loading questions…</Text>
      </View>
    );
  }

  const question = questions[currentIndex];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(responses).length;
  const progress = (currentIndex + 1) / totalQuestions;
  const isLastQuestion = currentIndex === totalQuestions - 1;

  // Mode swipe T-IRT : tous les forced_choice avec swipe auto-avancement
  const isSwipeMode = question?.question_type === "forced_choice";

  if (isSwipeMode) {
    const options = question.options as ForcedChoiceOption[] | null;
    const leftOption = options?.find((o) => o.side === "left");
    const rightOption = options?.find((o) => o.side === "right");

    return (
      <>
        <Stack.Screen
          options={{
            title: `${currentIndex + 1} / ${totalQuestions}`,
            headerBackTitle: "Tests",
          }}
        />

        <View className="flex-1 bg-bg-primary">
          {/* Barre de progression */}
          <View className="h-1 bg-bg-border">
            <View
              style={{ width: `${progress * 100}%`, backgroundColor: "#4A90B8" }}
              className="h-full"
            />
          </View>

          {/* Indicateur progression texte */}
          <View className="px-5 pt-3 pb-1 flex-row items-center justify-between">
            <Text className="text-muted text-xs">
              {answeredCount} / {totalQuestions} répondues
            </Text>
            <Text className="text-muted text-xs">
              {Math.round(progress * 100)} %
            </Text>
          </View>

          {/* Zone principale swipe */}
          {leftOption && rightOption ? (
            <SwipePairCard
              leftOption={leftOption}
              rightOption={rightOption}
              selectedSide={responses[question.id] as "left" | "right" | undefined}
              onChoose={(side) => selectAndAdvance(question.id, side)}
              pairIndex={currentIndex}
            />
          ) : (
            <View className="flex-1 items-center justify-center">
              <Text className="text-muted">Options indisponibles</Text>
            </View>
          )}

          {/* Bouton de soumission sur la dernière paire */}
          {isLastQuestion && (
            <View className="px-5 pb-8 pt-2">
              <TouchableOpacity
                onPress={handleSubmit}
                disabled={submitMutation.isPending}
                className="bg-brand-primary rounded-xl py-4 items-center"
              >
                {submitMutation.isPending ? (
                  <ActivityIndicator color="#07090F" />
                ) : (
                  <Text className="text-bg-primary font-semibold text-base">
                    Soumettre le test
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>
      </>
    );
  }

  // Mode classique (Likert ou autre)
  return (
    <>
      <Stack.Screen
        options={{
          title: `Question ${currentIndex + 1} / ${totalQuestions}`,
          headerBackTitle: "Tests",
        }}
      />

      <View className="flex-1 bg-bg-primary">
        {/* Progress bar */}
        <View className="h-1 bg-bg-border">
          <View
            style={{ width: `${progress * 100}%`, backgroundColor: "#4A90B8" }}
            className="h-full"
          />
        </View>

        <ScrollView
          className="flex-1"
          contentContainerStyle={{ padding: 20, paddingBottom: 120 }}
        >
          <Text className="text-muted text-sm mb-4">
            {answeredCount} / {totalQuestions} answered
          </Text>

          <Text className="text-text-primary text-xl font-medium leading-relaxed mb-8">
            {question?.text}
          </Text>

          <LikertQuestion
            question={question}
            selectedValue={responses[question?.id ?? 0]}
            onSelect={selectAnswer}
          />
        </ScrollView>

        {/* Bottom nav */}
        <View className="absolute bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-border px-5 py-4 flex-row gap-3">
          <TouchableOpacity
            onPress={goPrev}
            disabled={currentIndex === 0}
            className="border border-bg-border rounded-xl py-3 px-5"
            style={{ opacity: currentIndex === 0 ? 0.3 : 1 }}
          >
            <Text className="text-text-primary font-medium">← Back</Text>
          </TouchableOpacity>

          {isLastQuestion ? (
            <TouchableOpacity
              onPress={handleSubmit}
              disabled={submitMutation.isPending}
              className="flex-1 bg-brand-primary rounded-xl py-3 items-center"
            >
              {submitMutation.isPending ? (
                <ActivityIndicator color="#07090F" />
              ) : (
                <Text className="text-bg-primary font-semibold">Submit test</Text>
              )}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={goNext}
              className="flex-1 bg-brand-primary/90 rounded-xl py-3 items-center"
            >
              <Text className="text-bg-primary font-semibold">Next →</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>
    </>
  );
}
