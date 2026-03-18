import { View, Text, FlatList, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { useAssessment } from "@/features/assessment/hooks/useAssessment";
import { useAuthStore } from "@/features/auth/store";
import { TestCard } from "@/features/assessment/components/catalogue/TestCard";
import { ProgressHeader } from "@/features/assessment/components/catalogue/ProgressHeader";

export default function AssessmentListScreen() {
  const router = useRouter();
  const name = useAuthStore((s) => s.name);
  const { catalogue, myResults, completedTestIds, isLoading } = useAssessment();

  const completed = myResults?.length ?? 0;
  const total = catalogue?.length ?? 0;

  return (
    <View style={{ flex: 1, backgroundColor: "#0D1B2A" }}>
           

      {/* ── Card list — overlaps header by 20px ───────────────────── */}
      {isLoading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator color="#A67C52" size="large" />
          <Text style={{ color: "#64748B", marginTop: 12, fontSize: 13 }}>
            Loading Assessments...
          </Text>
        </View>
      ) : (
        <FlatList
          data={catalogue}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TestCard
              test={item}
              isCompleted={completedTestIds.has(item.id)}
              onPress={() => router.push(`/(candidate)/assessment/${item.id}`)}
            />
          )}
          contentContainerStyle={{
            paddingHorizontal: 16,
            paddingTop: 20,
            paddingBottom: 48,
            marginTop: -20,
          }}
          showsVerticalScrollIndicator={false}
          ListHeaderComponent={
            catalogue && myResults ? (
              <ProgressHeader completed={completed} total={total} />
            ) : null
          }
        />
      )}
    </View>
  );
}
