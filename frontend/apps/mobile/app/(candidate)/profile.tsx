import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/features/auth/store";
import { IdentityCard } from "@/features/profile/components/IdentityCard";
import { HarmonyScoreSection } from "@/features/profile/components/HarmonyScoreSection";
import { ExperienceSection } from "@/features/profile/components/ExperienceSection";
import { DocumentVaultSection } from "@/features/profile/components/DocumentVaultSection";

type ProfileTab = "id" | "score" | "experience" | "vault";

const TABS: {
  key: ProfileTab;
  icon: keyof typeof Ionicons.glyphMap;
  activeIcon: keyof typeof Ionicons.glyphMap;
  label: string;
  title: string;
  subtitle: string;
}[] = [
  {
    key: "id",
    icon: "person-outline",
    activeIcon: "person",
    label: "Profile",
    title: "MY IDENTITY",
    subtitle: "Your public profile",
  },
  {
    key: "score",
    icon: "analytics-outline",
    activeIcon: "analytics",
    label: "Skills",
    title: "SOFT SKILLS",
    subtitle: "Your behavioural signature",
  },
  {
    key: "experience",
    icon: "boat-outline",
    activeIcon: "boat",
    label: "History",
    title: "EXPERIENCE",
    subtitle: "Track record & references",
  },
  {
    key: "vault",
    icon: "shield-checkmark-outline",
    activeIcon: "shield-checkmark",
    label: "Docs",
    title: "DOCUMENTS",
    subtitle: "STCW compliance & certificates",
  },
];

export default function ProfileScreen() {
  const { logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<ProfileTab>("id");

  const currentTab = TABS.find((t) => t.key === activeTab)!;

  function confirmLogout() {
    Alert.alert("Sign out", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      { text: "Sign out", style: "destructive", onPress: logout },
    ]);
  }

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Page header */}
      <View className="px-5 pt-4 pb-4 flex-row items-start justify-between">
        <View>
          <Text
            className="text-text-primary font-black"
            style={{ fontSize: 18, letterSpacing: 6 }}
          >
            {currentTab.title}
          </Text>
          <Text className="text-muted text-xs mt-0.5" style={{ letterSpacing: 2 }}>
            {currentTab.subtitle.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Tab bar */}
      <View className="px-4 mb-2">
        <View className="bg-bg-elevated border border-bg-border rounded-2xl p-1.5 flex-row">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <TouchableOpacity
                key={tab.key}
                onPress={() => setActiveTab(tab.key)}
                className="flex-1 items-center py-2.5 rounded-xl"
                style={{ backgroundColor: isActive ? "#1A2C42" : "transparent" }}
              >
                <Ionicons
                  name={isActive ? tab.activeIcon : tab.icon}
                  size={18}
                  color={isActive ? "#A67C52" : "#718096"}
                />
                <Text
                  style={{
                    fontSize: 10,
                    fontWeight: "600",
                    letterSpacing: 0.5,
                    marginTop: 3,
                    // ice on active (12.7:1 on bg-secondary) · silver on inactive (4.7:1 on bg-elevated)
                    color: isActive ? "#F1F4F8" : "#94A3B8",
                  }}
                >
                  {tab.label.toUpperCase()}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Scrollable content */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 8, paddingBottom: 48 }}
        showsVerticalScrollIndicator={false}
      >
        {activeTab === "id" && <IdentityCard />}
        {activeTab === "score" && <HarmonyScoreSection />}
        {activeTab === "experience" && <ExperienceSection />}
        {activeTab === "vault" && <DocumentVaultSection />}

        {/* Footer watermark */}
        <View className="items-center mt-10 mb-2">
          <Text style={{ color: "#718096", fontSize: 8, letterSpacing: 4, fontWeight: "700", opacity: 0.4 }}>
            HARMONY · YACHTING ASSESSMENT CENTER
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}
