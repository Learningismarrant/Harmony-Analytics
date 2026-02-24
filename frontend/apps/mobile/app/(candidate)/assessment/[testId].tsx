import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useState, useRef, useEffect, use } from "react";
import { useRouter, useLocalSearchParams, Stack } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { assessmentApi, queryKeys } from "@harmony/api";
import type { ResponseIn } from "@harmony/types";

/**
 * Test-taking screen — renders questions one at a time (or in pages).
 * Tracks time-per-question (seconds_spent) for reliability engine.
 */
export default function TakeTestScreen() {
  const { testId } = useLocalSearchParams<{ testId: string }>();
  const id = parseInt(testId, 10);
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now());
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});

  const { data: questions, isLoading } = useQuery({
    queryKey: queryKeys.assessment.questions(id),
    queryFn: () => assessmentApi.getQuestions(id),
  });

  // Reset timer when question changes
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
      return assessmentApi.submit({ test_id: id, responses: responseList });
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
          {
            text: "Submit",
            onPress: () => submitMutation.mutate(),
          },
        ],
      );
    } else {
      submitMutation.mutate();
    }
  }

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

  // Likert scale labels
  const LIKERT_OPTIONS =
    question?.options ?? ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"];

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
          {/* Question counter */}
          <Text className="text-muted text-sm mb-4">
            {answeredCount} / {totalQuestions} answered
          </Text>

          {/* Question text */}
          <Text className="text-text-primary text-xl font-medium leading-relaxed mb-8">
            {question?.text}
          </Text>

          {/* Options */}
          <View className="space-y-3">
            {LIKERT_OPTIONS.map((option, idx) => {
              const value = String(idx + 1); // 1-indexed
              const isSelected = responses[question?.id ?? 0] === value;

              return (
                <TouchableOpacity
                  key={value}
                  onPress={() => selectAnswer(question!.id, value)}
                  className={`border rounded-xl px-4 py-4 ${
                    isSelected
                      ? "border-brand-primary bg-brand-primary/10"
                      : "border-bg-border bg-bg-elevated"
                  }`}
                  activeOpacity={0.75}
                >
                  <View className="flex-row items-center gap-3">
                    <View
                      className={`w-5 h-5 rounded-full border-2 items-center justify-center ${
                        isSelected
                          ? "border-brand-primary bg-brand-primary"
                          : "border-muted"
                      }`}
                    >
                      {isSelected && (
                        <View className="w-2 h-2 rounded-full bg-bg-primary" />
                      )}
                    </View>
                    <Text
                      className={`flex-1 text-base ${
                        isSelected ? "text-brand-primary font-medium" : "text-text-primary"
                      }`}
                    >
                      {option}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </ScrollView>

        {/* Bottom nav */}
        <View className="absolute bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-border
                          px-5 py-4 flex-row gap-3">
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
