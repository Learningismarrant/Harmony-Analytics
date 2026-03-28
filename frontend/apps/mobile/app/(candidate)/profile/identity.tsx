import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { IdentityCard } from "@/features/profile/components/IdentityCard";

export default function IdentityScreen() {
  const router = useRouter();

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header */}
      <View className="px-5 pt-4 pb-3 flex-row items-center gap-x-3">
        <TouchableOpacity onPress={() => router.back()} activeOpacity={0.7}>
          <Ionicons name="arrow-back" size={22} color="#94A3B8" />
        </TouchableOpacity>
        <View>
          <Text className="text-text-primary font-black" style={{ fontSize: 18, letterSpacing: 6 }}>
            MY IDENTITY
          </Text>
          <Text className="text-muted text-xs mt-0.5" style={{ letterSpacing: 2 }}>
            YOUR PUBLIC PROFILE
          </Text>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 48 }}
        showsVerticalScrollIndicator={false}
      >
        <IdentityCard />
      </ScrollView>
    </View>
  );
}
