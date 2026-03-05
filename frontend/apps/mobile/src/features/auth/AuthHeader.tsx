import { View, Text } from "react-native";

interface AuthHeaderProps {
  title: string;
  subtitle: string;
}

export const AuthHeader = ({ title, subtitle }: AuthHeaderProps) => (
  <View className="items-center mb-12 w-full">
    <Text
      className="text-white font-black text-center mb-2.5"
      style={{
        fontSize: 32,
        letterSpacing: 12,
        textShadowColor: "#1A2C42",
        textShadowOffset: { width: 0, height: 2 },
        textShadowRadius: 4,
      }}
    >
      {title}
    </Text>

    {/* Horizon line */}
    <View className="flex-row items-center justify-center h-5" style={{ width: "60%" }}>
      <View className="w-[3px] h-[3px] rounded-full bg-teak" style={{ opacity: 0.8 }} />
      <View className="flex-1 mx-2.5 bg-teak" style={{ height: 0.5, opacity: 0.4 }} />
      <View className="w-[3px] h-[3px] rounded-full bg-teak" style={{ opacity: 0.8 }} />
    </View>

    <Text
      className="text-white text-center font-normal mt-1.5"
      style={{ fontSize: 9, letterSpacing: 4, opacity: 0.5 }}
    >
      {subtitle.toUpperCase()}
    </Text>
  </View>
);
