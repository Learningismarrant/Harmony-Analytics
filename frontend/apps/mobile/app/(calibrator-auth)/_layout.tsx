import { Stack } from "expo-router";

export default function CalibratorAuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: "#07090F" },
        animation: "slide_from_right",
      }}
    />
  );
}
