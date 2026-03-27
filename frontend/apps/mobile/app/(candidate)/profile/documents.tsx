import { View, Text, TouchableOpacity, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { DocumentVaultSection } from "@/features/profile/components/DocumentVaultSection";

export default function ProfileDocumentsScreen() {
  const router = useRouter();

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header */}
      <View className="px-5 pt-4 pb-3 flex-row items-start">
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
              DOCUMENTS
            </Text>
            <Text
              className="text-muted text-xs mt-0.5"
              style={{ letterSpacing: 2 }}
            >
              STCW COMPLIANCE &amp; CERTIFICATES
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 48 }}
        showsVerticalScrollIndicator={false}
      >
        <DocumentVaultSection />
      </ScrollView>
    </View>
  );
}
