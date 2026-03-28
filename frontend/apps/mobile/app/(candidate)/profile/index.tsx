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
  const { name } = useAuthStore();

  const initials = deriveInitials(name);


  return (
    <View className="flex-1 bg-bg-primary">

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
