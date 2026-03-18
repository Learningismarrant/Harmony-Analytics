import { View, Text, Animated } from "react-native";
import type { StyleProp, ViewStyle } from "react-native";

interface Props {
  questionText: string;
  questionNumber: number;
  totalQuestions: number;
  animatedStyle?: StyleProp<ViewStyle>;
}

export function QuestionCard({ questionText, questionNumber, totalQuestions, animatedStyle }: Props) {
  return (
    <Animated.View className="w-full px-5 mb-8" style={animatedStyle}>
      <View
        className="p-9 justify-center items-center bg-white rounded-3xl"
        style={{
          minHeight: 180,
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 10 },
          shadowOpacity: 0.1,
          shadowRadius: 15,
          elevation: 5,
        }}
      >
        {/* Badge */}
        <View className="absolute top-4 right-5">
          <Text className="text-silver text-xs font-extrabold tracking-[1px]">
            {questionNumber} / {totalQuestions}
          </Text>
        </View>

        <Text className="text-xl text-center font-bold text-navy leading-7">
          {questionText}
        </Text>

        {/* Décoration */}
        <View
          className="absolute bottom-0 w-16 rounded-t-sm"
          style={{ height: 3, backgroundColor: "#94A3B8" }}
        />
      </View>
    </Animated.View>
  );
}
