import { View, Text, TouchableOpacity } from "react-native";
import type { QuestionOut, ForcedChoiceOption } from "@harmony/types";

interface ForcedChoiceQuestionProps {
  question: QuestionOut;
  selectedValue: string | undefined;
  onSelect: (questionId: number, value: string) => void;
}

export function ForcedChoiceQuestion({
  question,
  selectedValue,
  onSelect,
}: ForcedChoiceQuestionProps) {
  const options = question.options as ForcedChoiceOption[] | null;

  if (!options || options.length < 2) {
    return (
      <View className="items-center py-8">
        <Text className="text-muted text-sm">Options unavailable</Text>
      </View>
    );
  }

  const leftOption = options.find((o) => o.side === "left");
  const rightOption = options.find((o) => o.side === "right");

  if (!leftOption || !rightOption) {
    return (
      <View className="items-center py-8">
        <Text className="text-muted text-sm">Options unavailable</Text>
      </View>
    );
  }

  return (
    <View className="gap-4">
      {[leftOption, rightOption].map((option) => {
        const isSelected = selectedValue === option.side;
        return (
          <TouchableOpacity
            key={option.side}
            onPress={() => onSelect(question.id, option.side)}
            style={{ minHeight: 72 }}
            className={`border rounded-xl px-4 py-5 justify-center ${
              isSelected
                ? "border-brand-primary bg-brand-primary/10"
                : "border-bg-border bg-bg-elevated"
            }`}
            activeOpacity={0.75}
          >
            <Text
              className={`text-base leading-relaxed ${
                isSelected ? "text-brand-primary font-medium" : "text-text-primary"
              }`}
            >
              {option.text.fr}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}
