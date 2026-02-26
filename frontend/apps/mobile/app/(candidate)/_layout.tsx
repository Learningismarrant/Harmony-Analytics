import { Tabs } from "expo-router";
import { Text } from "react-native";

function TabIcon({ label, focused }: { label: string; focused: boolean }) {
  return (
    <Text style={{ color: focused ? "#0EA5E9" : "#8FA3B8", fontSize: 20 }}>
      {label}
    </Text>
  );
}

export default function CandidateLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: "#07090F" },
        headerTintColor: "#E8EFF7",
        headerTitleStyle: { fontWeight: "600" },
        tabBarStyle: {
          backgroundColor: "#0D1117",
          borderTopColor: "#1E2733",
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: "#0EA5E9",
        tabBarInactiveTintColor: "#8FA3B8",
        tabBarLabelStyle: { fontSize: 11, fontWeight: "500" },
      }}
    >
      <Tabs.Screen
        name="profile"
        options={{
          title: "Profile",
          tabBarLabel: "Profile",
          tabBarIcon: ({ focused }) => <TabIcon label="◈" focused={focused} />,
          headerTitle: "My Profile",
        }}
      />
      <Tabs.Screen
        name="assessment/index"
        options={{
          title: "Tests",
          tabBarLabel: "Tests",
          tabBarIcon: ({ focused }) => <TabIcon label="⊞" focused={focused} />,
          headerTitle: "Psychometric Tests",
        }}
      />
      <Tabs.Screen
        name="survey/index"
        options={{
          title: "Survey",
          tabBarLabel: "Survey",
          tabBarIcon: ({ focused }) => <TabIcon label="◎" focused={focused} />,
          headerTitle: "Surveys & Pulse",
        }}
      />
      <Tabs.Screen
        name="assessment/[testId]"
        options={{ href: null, headerTitle: "Take Test" }}
      />
      <Tabs.Screen
        name="assessment/result"
        options={{ href: null, headerTitle: "Results" }}
      />
      <Tabs.Screen
        name="survey/[surveyId]"
        options={{ href: null, headerTitle: "Survey Response" }}
      />
    </Tabs>
  );
}
