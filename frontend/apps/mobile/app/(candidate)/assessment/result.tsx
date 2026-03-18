import { useEffect } from "react";
import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { useRouter, useLocalSearchParams, Stack } from "expo-router";
import { ResultRing } from "@/features/assessment/components/result/ResultRing";
import { RadarChart, type RadarDataPoint } from "@/features/assessment/components/result/RadarChart";
import { useLastResultStore } from "@/features/assessment/store/useLastResultStore";

export default function TestResultScreen() {
  const router = useRouter();
  const { score } = useLocalSearchParams<{ score: string }>();
  const scoreNum = parseInt(score ?? "0", 10);

  const { lastResult, clearLastResult } = useLastResultStore();

  useEffect(() => {
    return () => {
      clearLastResult();
    };
  }, [clearLastResult]);

  const radarData: RadarDataPoint[] = lastResult?.scores?.traits
    ? Object.entries(lastResult.scores.traits).map(([label, t]) => ({
        label,
        score: t.score,
        niveau: t.niveau,
      }))
    : [];

  return (
    <>
      <Stack.Screen options={{ title: "Result", headerBackVisible: false }} />
      <ScrollView
        className="flex-1 bg-bg-primary"
        contentContainerStyle={{ padding: 24, paddingBottom: 40 }}
      >
        <View className="items-center mb-6">
          <ResultRing score={scoreNum} />
        </View>

        {radarData.length >= 3 && (
          <View className="mb-8">
            <RadarChart data={radarData} />
          </View>
        )}

        <View className="gap-3">
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
      </ScrollView>
    </>
  );
}
