import { View, Text, TouchableOpacity } from "react-native";
import type { TestInfoOut } from "@harmony/types";

const TEST_ICONS: Record<string, string> = {
  likert: "◈",
  cognitive: "⊞",
  free: "✎",
};

const TEST_DURATION: Record<string, string> = {
  likert: "~15 min",
  cognitive: "~20 min",
  free: "~10 min",
};

interface TestCardProps {
  test: TestInfoOut;
  isCompleted: boolean;
  onPress: () => void;
}

export function TestCard({ test, isCompleted, onPress }: TestCardProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isCompleted}
      className="bg-bg-secondary border border-bg-border rounded-xl p-4 mb-3"
      style={{ opacity: isCompleted ? 0.6 : 1 }}
      activeOpacity={0.75}
    >
      <View className="flex-row items-start gap-3">
        <View className="w-10 h-10 rounded-xl bg-brand-primary/15 border border-brand-primary/25 items-center justify-center">
          <Text className="text-brand-primary text-xl">
            {TEST_ICONS[test.test_type] ?? "●"}
          </Text>
        </View>

        <View className="flex-1">
          <View className="flex-row items-center justify-between mb-1">
            <Text className="text-text-primary font-semibold text-base flex-1 mr-2">
              {test.name}
            </Text>
            {isCompleted && (
              <View className="bg-green-500/15 border border-green-500/25 rounded-full px-2 py-0.5">
                <Text className="text-green-400 text-xs">Completed</Text>
              </View>
            )}
          </View>

          <Text className="text-muted text-sm leading-relaxed mb-2">
            {test.description}
          </Text>

          <View className="flex-row items-center gap-3">
            <Text className="text-xs text-muted">
              ⏱ {TEST_DURATION[test.test_type] ?? "~15 min"}
            </Text>
            <Text className="text-xs text-muted">
              {test.max_score_per_question} pts/question
            </Text>
          </View>
        </View>
      </View>

      {!isCompleted && (
        <View className="bg-brand-primary rounded-lg py-2.5 mt-3 items-center">
          <Text className="text-bg-primary font-semibold text-sm">Start test</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}
