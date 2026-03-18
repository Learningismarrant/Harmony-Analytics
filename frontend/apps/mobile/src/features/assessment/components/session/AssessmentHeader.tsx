import { View } from "react-native";

interface Props {
  current: number; // 0-based index
  total: number;
}

export function AssessmentHeader({ current, total }: Props) {
  const progress = (current + 1) / total;

  return (
    <View className="w-full px-10 pt-4 mb-2">
      <View
        className="rounded-sm overflow-hidden"
        style={{ height: 2, backgroundColor: "rgba(255,255,255,0.08)" }}
      >
        <View
          style={{
            width: `${progress * 100}%`,
            height: "100%",
            backgroundColor: "#94A3B8",
            shadowColor: "#94A3B8",
            shadowOffset: { width: 0, height: 0 },
            shadowOpacity: 0.5,
            shadowRadius: 4,
          }}
        />
      </View>
    </View>
  );
}
