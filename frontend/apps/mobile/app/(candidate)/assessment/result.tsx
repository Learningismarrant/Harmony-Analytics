import { View, Text, TouchableOpacity } from "react-native";
import { useRouter, useLocalSearchParams, Stack } from "expo-router";
import { ResultRing } from "@/features/assessment/components/ResultRing";

export default function TestResultScreen() {
  const router = useRouter();
  const { score } = useLocalSearchParams<{ score: string }>();
  const scoreNum = parseInt(score ?? "0", 10);

  return (
    <>
      <Stack.Screen options={{ title: "Result", headerBackVisible: false }} />
      <View className="flex-1 bg-bg-primary items-center justify-center px-6">
        <ResultRing score={scoreNum} />

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
