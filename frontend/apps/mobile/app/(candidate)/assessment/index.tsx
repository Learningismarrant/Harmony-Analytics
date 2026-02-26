import { View, Text, ScrollView, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { useAssessment } from "@/features/assessment/hooks/useAssessment";
import { TestCard } from "@/features/assessment/components/TestCard";
import { ProgressHeader } from "@/features/assessment/components/ProgressHeader";

export default function AssessmentListScreen() {
  const router = useRouter();
  const { catalogue, myResults, completedTestIds, isLoading } = useAssessment();

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
    >
      {catalogue && myResults && (
        <ProgressHeader completed={myResults.length} total={catalogue.length} />
      )}

      {isLoading ? (
        <View className="items-center py-10">
          <ActivityIndicator color="#0EA5E9" size="large" />
          <Text className="text-muted mt-3 text-sm">Loading tests…</Text>
        </View>
      ) : (
        <>
          {catalogue?.map((test) => (
            <TestCard
              key={test.id}
              test={test}
              isCompleted={completedTestIds.has(test.id)}
              onPress={() => router.push(`/(candidate)/assessment/${test.id}`)}
            />
          ))}
        </>
      )}
    </ScrollView>
  );
}
