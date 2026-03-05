import { View, Text } from "react-native";

export const AuthFooter = () => (
  <View className="mt-auto pb-8 items-center">
    <Text
      className="text-white text-[9px] font-bold tracking-[3px]"
      style={{ opacity: 0.3 }}
    >
      HARMONY GLOBAL MARITIME NETWORK
    </Text>
    <View className="flex-row gap-1.5 my-2.5">
      <View
        className="w-[3px] h-[3px] rounded-full bg-teak"
        style={{ opacity: 0.4 }}
      />
      <View
        className="w-[3px] h-[3px] rounded-full bg-teak"
        style={{ opacity: 0.4 }}
      />
      <View
        className="w-[3px] h-[3px] rounded-full bg-teak"
        style={{ opacity: 0.4 }}
      />
    </View>
    <Text
      className="text-silver text-[7px] tracking-[2px]"
      style={{ opacity: 0.5 }}
    >
      ENCRYPTED ACCESS GATEWAY v1.0
    </Text>
  </View>
);
