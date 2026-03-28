import { View, Text, TouchableOpacity, Alert } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/features/auth/store";
import { ProfileMacroMap } from "@/features/profile/components/ProfileMacroMap";

function deriveInitials(name: string | null): string {
  if (!name) return "YC";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

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
          <Text className="text-muted text-xs mt-0.5" style={{ letterSpacing: 2 }}>
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

      {/* Macro constellation — fills the available space */}
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ProfileMacroMap
          initials={initials}
          onStarPress={(key) => router.push(`/(candidate)/profile/${key}`)}
          onCenterPress={() => router.push("/(candidate)/profile/identity")}
        />

        <Text
          style={{
            color: "#718096",
            fontSize: 8,
            letterSpacing: 4,
            fontWeight: "700",
            opacity: 0.4,
            marginTop: 8,
          }}
        >
          RADIANT ANALYTICS · YACHTING ASSESSMENT CENTER
        </Text>
      </View>
    </View>
  );
}
