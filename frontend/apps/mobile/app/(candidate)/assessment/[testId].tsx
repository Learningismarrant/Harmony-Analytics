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

export default function TakeTestScreen() {
  const { testId } = useLocalSearchParams<{ testId: string }>();
  const id = parseInt(testId, 10);

  const {
    questions,
    isLoading,
    currentIndex,
    responses,
    submitMutation,
    selectAnswer,
    goNext,
    goPrev,
    handleSubmit,
  } = useTakeTest(id);

  if (isLoading || !questions) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#0EA5E9" size="large" />
        <Text className="text-muted mt-3">Loading questions…</Text>
      </View>
    );
  }

  const question = questions[currentIndex];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(responses).length;
  const progress = (currentIndex + 1) / totalQuestions;
  const isLastQuestion = currentIndex === totalQuestions - 1;

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
            style={{ width: `${progress * 100}%`, backgroundColor: "#0EA5E9" }}
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
