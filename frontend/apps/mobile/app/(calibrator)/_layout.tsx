import { Tabs, useRouter } from "expo-router";
import { TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/features/auth/store";
import { clearCalibToken } from "@/features/auth/lib";

const NAV = {
  bgPrimary: "#0D1B2A",
  bgBorder: "#1E3050",
  teak: "#A67C52",
  silver: "#94A3B8",
} as const;

function LogoutButton() {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);

  async function handleLogout() {
    await logout();
    await clearCalibToken();
    router.replace("/(calibrator-auth)/login");
  }

  return (
    <TouchableOpacity
      onPress={handleLogout}
      style={{
        marginRight: 16,
        padding: 8,
        borderRadius: 8,
        backgroundColor: "rgba(166,124,82,0.1)",
        borderWidth: 1,
        borderColor: "rgba(166,124,82,0.2)",
      }}
    >
      <Ionicons name="log-out-outline" size={16} color={NAV.teak} />
    </TouchableOpacity>
  );
}

export default function CalibratorLayout() {
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
        headerStyle: { backgroundColor: NAV.bgPrimary },
        headerTintColor: "#E8EFF7",
        headerShadowVisible: false,
        headerRight: () => <LogoutButton />,
      }}
    >
      <Tabs.Screen
        name="catalogues"
        options={{
          title: "Tests",
          tabBarLabel: "Tests",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="layers-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="sessions"
        options={{
          title: "Historique",
          tabBarLabel: "Historique",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="time-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profil",
          tabBarLabel: "Profil",
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-outline" size={size} color={color} />
          ),
        }}
      />
      {/* Screens cachés de la tab bar */}
      <Tabs.Screen
        name="session/[sessionId]"
        options={{ href: null, headerShown: false }}
      />
      <Tabs.Screen
        name="session/result/[sessionId]"
        options={{ href: null, headerShown: false }}
      />
    </Tabs>
  );
}
