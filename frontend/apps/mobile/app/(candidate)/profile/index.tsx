import { View, Text, TouchableOpacity, ScrollView, Alert } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/features/auth/store";
import { IdentityCard } from "@/features/profile/components/IdentityCard";
import { ProfileMacroMap } from "@/features/profile/components/ProfileMacroMap";

// ── Derive initials from a full name string ────────────────────────────────────
function deriveInitials(name: string | null): string {
  if (!name) return "YC";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// ── Hardcoded investor-demo progress values ────────────────────────────────────
const STAR_PROGRESS = {
  tests:       0.33,
  experience:  1.0,
  documents:   0.67,
} as const;

const GLOBAL_PROGRESS = 0.67;

export default function ProfileIndexScreen() {
  const router = useRouter();
  const { logout, name } = useAuthStore();

  const initials = deriveInitials(name);

  function confirmLogout() {
    Alert.alert("Sign out", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      { text: "Sign out", style: "destructive", onPress: logout },
    ]);
  }

  function handleStarPress(key: "tests" | "experience" | "documents") {
    router.push(`/(candidate)/profile/${key}`);
  }

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Page header */}
      <View className="px-5 pt-4 pb-3 flex-row items-start justify-between">
        <View>
          <Text
            className="text-text-primary font-black"
            style={{ fontSize: 18, letterSpacing: 6 }}
          >
            MY PROFILE
          </Text>
          <Text
            className="text-muted text-xs mt-0.5"
            style={{ letterSpacing: 2 }}
          >
            YOUR RADIANT IDENTITY
          </Text>
        </View>

        <TouchableOpacity
          onPress={confirmLogout}
          className="flex-row items-center px-2.5 py-1.5 rounded-lg"
          style={{
            backgroundColor: "rgba(166,124,82,0.1)",
            borderWidth: 1,
            borderColor: "rgba(166,124,82,0.2)",
          }}
        >
          <Ionicons name="log-out-outline" size={16} color="#A67C52" />
        </TouchableOpacity>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{
          paddingHorizontal: 16,
          paddingBottom: 48,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* Macro constellation map */}
        <View style={{ alignItems: "center", paddingVertical: 16 }}>
          <ProfileMacroMap
            initials={initials}
            globalProgress={GLOBAL_PROGRESS}
            starProgress={STAR_PROGRESS}
            onStarPress={handleStarPress}
          />
        </View>

        {/* Identity card */}
        <IdentityCard />

        {/* Footer watermark */}
        <View className="items-center mt-10 mb-2">
          <Text
            style={{
              color: "#718096",
              fontSize: 8,
              letterSpacing: 4,
              fontWeight: "700",
              opacity: 0.4,
            }}
          >
            RADIANT ANALYTICS · YACHTING ASSESSMENT CENTER
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}
