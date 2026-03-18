import { View, Text } from "react-native";

export function AssessmentFooter() {
  return (
    <View className="items-center pb-8 gap-2">
      <View
        className="w-5 mb-1"
        style={{ height: 1, backgroundColor: "rgba(255,255,255,0.2)" }}
      />
      <Text className="text-white/40 text-[9px] font-extrabold tracking-[3px] text-center">
        HARMONY ASSESSMENT SYSTEM
      </Text>
      <Text
        className="text-silver text-[7px] font-semibold tracking-[1.5px] text-center"
        style={{ opacity: 0.6 }}
      >
        SECURE ENGINE v1.0
      </Text>
    </View>
  );
}
