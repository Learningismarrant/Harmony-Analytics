import { View, Text } from "react-native";

function getLevel(score: number): { label: string; color: string } {
  if (score >= 75) return { label: "Excellent", color: "#22C55E" };
  if (score >= 55) return { label: "Good", color: "#F59E0B" };
  return { label: "In progress", color: "#EF4444" };
}

interface ResultRingProps {
  score: number;
}

export function ResultRing({ score }: ResultRingProps) {
  const { label, color } = getLevel(score);

  return (
    <View className="items-center">
      <View
        className="w-32 h-32 rounded-full border-4 items-center justify-center mb-4"
        style={{ borderColor: color }}
      >
        <Text style={{ color }} className="text-4xl font-bold">
          {score}
        </Text>
        <Text className="text-muted text-xs">/ 100</Text>
      </View>
      <Text className="text-text-primary text-2xl font-semibold mb-1">{label}</Text>
      <Text className="text-muted text-sm text-center mb-8">
        Your score has been recorded and your psychometric profile has been updated.
      </Text>
    </View>
  );
}
