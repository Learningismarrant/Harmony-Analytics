import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { HarmonyScoreSection } from "@/features/profile/components/HarmonyScoreSection";

export default function ProfileTestsScreen() {
  const router = useRouter();

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header */}
      <View className="px-5 pt-4 pb-3 flex-row items-start justify-between">
        <View className="flex-row items-center gap-x-3">
          <TouchableOpacity
            onPress={() => router.back()}
            className="w-8 h-8 rounded-lg items-center justify-center"
            style={{ backgroundColor: "rgba(166,124,82,0.1)", borderWidth: 1, borderColor: "rgba(166,124,82,0.2)" }}
          >
            <Ionicons name="chevron-back" size={16} color="#A67C52" />
          </TouchableOpacity>
          <View>
            <Text
              className="text-text-primary font-black"
              style={{ fontSize: 16, letterSpacing: 5 }}
            >
              PSYCHOMETRIC PROFILE
            </Text>
            <Text
              className="text-muted text-xs mt-0.5"
              style={{ letterSpacing: 2 }}
            >
              YOUR BEHAVIOURAL SIGNATURE
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 48 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Locked normative database banner */}
        <View
          style={{
            backgroundColor: "rgba(166,124,82,0.06)",
            borderWidth: 1,
            borderColor: "rgba(166,124,82,0.3)",
            borderRadius: 16,
            padding: 16,
            flexDirection: "row",
            alignItems: "flex-start",
            gap: 12,
            marginBottom: 20,
          }}
        >
          <Ionicons name="lock-closed-outline" size={18} color="#A67C52" style={{ marginTop: 1 }} />
          <Text
            className="flex-1 text-muted text-xs leading-5"
            style={{ flex: 1 }}
          >
            Scores available once the Radiant Analytics normative database is validated.
          </Text>
        </View>

        {/* Existing HarmonyScoreSection */}
        <HarmonyScoreSection />
      </ScrollView>
    </View>
  );
}
