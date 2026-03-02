import { useEffect } from "react";
import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { useRouter, useLocalSearchParams, Stack } from "expo-router";
import { ResultRing } from "@/features/assessment/components/ResultRing";
import { TirtResultDetail } from "@/features/assessment/components/TirtResultDetail";
import { useLastResultStore } from "@/features/assessment/store/useLastResultStore";

export default function TestResultScreen() {
  const router = useRouter();
  const { score } = useLocalSearchParams<{ score: string }>();
  const scoreNum = parseInt(score ?? "0", 10);

  const { lastResult, clearLastResult } = useLastResultStore();
  const tirtDetail = lastResult?.scores?.tirt_detail;

  useEffect(() => {
    return () => {
      clearLastResult();
    };
  }, [clearLastResult]);

  return (
    <>
      <Stack.Screen options={{ title: "Result", headerBackVisible: false }} />
      <ScrollView
        className="flex-1 bg-bg-primary"
        contentContainerStyle={{ padding: 24, paddingBottom: 40 }}
      >
        <View className="items-center mb-8">
          {tirtDetail && scoreNum === 0 ? (
            <Text className="text-text-primary text-2xl font-semibold text-center">
              Your Big Five profile
            </Text>
          ) : (
            <ResultRing score={scoreNum} />
          )}
        </View>

        {tirtDetail && (
          <View className="mb-8">
            <TirtResultDetail tirtDetail={tirtDetail} />
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
