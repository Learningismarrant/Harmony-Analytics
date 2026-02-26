import { View, Text } from "react-native";

interface ProgressHeaderProps {
  completed: number;
  total: number;
}

export function ProgressHeader({ completed, total }: ProgressHeaderProps) {
  const pct = (completed / Math.max(total, 1)) * 100;

  return (
    <View className="bg-bg-secondary border border-bg-border rounded-xl p-4 mb-5">
      <View className="flex-row justify-between items-center mb-2">
        <Text className="text-text-primary font-medium">Progress</Text>
        <Text className="text-brand-primary font-semibold">
          {completed} / {total}
        </Text>
      </View>
      <View className="h-2 bg-bg-border rounded-full overflow-hidden">
        <View
          style={{ width: `${pct}%`, backgroundColor: "#0EA5E9" }}
          className="h-full rounded-full"
        />
      </View>
      <Text className="text-muted text-xs mt-1.5">
        {completed === total
          ? "All tests completed — your profile is complete!"
          : `${total - completed} test(s) remaining to unlock full matching.`}
      </Text>
    </View>
  );
}
