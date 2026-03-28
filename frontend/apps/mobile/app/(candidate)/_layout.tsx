import { Tabs, useRouter } from "expo-router";
import { TouchableOpacity, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/features/auth/store";

// ── React Navigation style props can't use className, so we reference
//    tailwind token values here as a single source of truth.
const NAV = {
  bgPrimary:   "#0D1B2A",  // bg-bg-primary
  bgSecondary: "#1A2C42",  // bg-bg-secondary
  bgBorder:    "#1E3050",  // bg-bg-border
  teak:        "#A67C52",  // teak
  silver:      "#94A3B8",  // silver / muted
} as const;

// ── Header components — use NativeWind className ──────────────────────────────

function HeaderTitle({ title }: { title: string }) {
  return (
    <View className="flex-row items-center">
      <Text className="text-teak text-xs font-black tracking-widest">
        HARMONY
      </Text>
      <Text className="text-slate text-xs font-light mx-1.5">·</Text>
      <Text className="text-ice text-xs font-bold tracking-widest">
        {title.toUpperCase()}
      </Text>
    </View>
  );
}

function LogoutButton() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);

  async function handleLogout() {
    await logout();
    router.replace("/(auth)/login");
  }

  return (
    <TouchableOpacity
      onPress={handleLogout}
      className="mr-4 flex-row items-center px-2.5 py-1.5 rounded-lg bg-teak/10 border border-teak/20"
    >
      <Ionicons name="log-out-outline" size={14} color={NAV.teak} />
    </TouchableOpacity>
  );
}

// ── Shared screen options ─────────────────────────────────────────────────────

const SCREEN_TITLES: Record<string, string> = {
  profile:              "My Profile",
  "assessment/index":   "Assessment",
  "survey/index":       "Survey",
  "training/index":     "Training",
  "applications/index": "Applications",
};

const sharedOptions = (name: string) => ({
  headerTitle: () => <HeaderTitle title={SCREEN_TITLES[name] ?? name} />,
  headerTitleAlign: "left" as const,
  headerRight: () => <LogoutButton />,
  headerStyle: { backgroundColor: NAV.bgPrimary },
  headerShadowVisible: false,
});

// ── Layout ────────────────────────────────────────────────────────────────────

export default function CandidateLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: NAV.bgPrimary,
          borderTopColor: NAV.bgBorder,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: NAV.teak,
        tabBarInactiveTintColor: NAV.silver,
        tabBarLabelStyle: { fontSize: 10, fontWeight: "600", letterSpacing: 0.5 },
      }}
    >
      <Tabs.Screen
        name="profile"
        options={{
          ...sharedOptions("profile"),
          tabBarLabel: "Profile",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="analytics-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="assessment/index"
        options={{
          ...sharedOptions("assessment/index"),
          tabBarLabel: "Tests",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="layers-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="survey/index"
        options={{
          ...sharedOptions("survey/index"),
          tabBarLabel: "Survey",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="compass-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="training/index"
        options={{
          ...sharedOptions("training/index"),
          tabBarLabel: "Training",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="medal-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="applications/index"
        options={{
          ...sharedOptions("applications/index"),
          tabBarLabel: "Applications",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="briefcase-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen name="assessment/[testId]" options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="assessment/result"   options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="survey/[surveyId]"   options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="training/[moduleId]" options={{ href: null, headerShown: false }} />
      {/* Profile sub-screens (managed by profile/_layout Stack) */}
      <Tabs.Screen name="profile/identity"   options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="profile/tests"      options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="profile/experience" options={{ href: null, headerShown: false }} />
      <Tabs.Screen name="profile/documents"  options={{ href: null, headerShown: false }} />
    </Tabs>
  );
}
