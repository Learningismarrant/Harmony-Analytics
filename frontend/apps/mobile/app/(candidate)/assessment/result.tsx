import { View, Text, TouchableOpacity } from "react-native";
import { useRouter, useLocalSearchParams, Stack } from "expo-router";

export default function TestResultScreen() {
  const router = useRouter();
  const { score } = useLocalSearchParams<{ score: string }>();
  const scoreNum = parseInt(score ?? "0", 10);

  const levelLabel =
    scoreNum >= 75 ? "Excellent" : scoreNum >= 55 ? "Good" : "In progress";
  const levelColor =
    scoreNum >= 75 ? "#22C55E" : scoreNum >= 55 ? "#F59E0B" : "#EF4444";

  return (
    <>
      <Stack.Screen options={{ title: "Result", headerBackVisible: false }} />
      <View className="flex-1 bg-bg-primary items-center justify-center px-6">
        {/* Score ring */}
        <View
          className="w-32 h-32 rounded-full border-4 items-center justify-center mb-4"
          style={{ borderColor: levelColor }}
        >
          <Text style={{ color: levelColor }} className="text-4xl font-bold">
            {scoreNum}
          </Text>
          <Text className="text-muted text-xs">/ 100</Text>
        </View>

        <Text className="text-text-primary text-2xl font-semibold mb-1">{levelLabel}</Text>
        <Text className="text-muted text-sm text-center mb-8">
          Your score has been recorded and your psychometric profile has been updated.
        </Text>

        <View className="w-full space-y-3">
          <TouchableOpacity
            onPress={() => router.replace("/(candidate)/assessment")}
            className="bg-brand-primary rounded-xl py-4 items-center"
          >
            <Text className="text-bg-primary font-semibold">Back to tests</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => router.replace("/(candidate)/profile")}
            className="border border-bg-border rounded-xl py-4 items-center"
          >
            <Text className="text-text-primary">View my profile</Text>
          </TouchableOpacity>
        </View>
      </View>
    </>
  );
}
