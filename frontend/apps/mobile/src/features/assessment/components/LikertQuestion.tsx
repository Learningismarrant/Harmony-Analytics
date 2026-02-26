import { View, Text, TouchableOpacity } from "react-native";
import type { QuestionOut } from "@harmony/types";

interface LikertQuestionProps {
  question: QuestionOut;
  selectedValue: string | undefined;
  onSelect: (questionId: number, value: string) => void;
}

const DEFAULT_OPTIONS = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"];

export function LikertQuestion({ question, selectedValue, onSelect }: LikertQuestionProps) {
  const options = question.options ?? DEFAULT_OPTIONS;

  return (
    <View className="space-y-3">
      {options.map((option, idx) => {
        const value = String(idx + 1);
        const isSelected = selectedValue === value;

        return (
          <TouchableOpacity
            key={value}
            onPress={() => onSelect(question.id, value)}
            className={`border rounded-xl px-4 py-4 ${
              isSelected
                ? "border-brand-primary bg-brand-primary/10"
                : "border-bg-border bg-bg-elevated"
            }`}
            activeOpacity={0.75}
          >
            <View className="flex-row items-center gap-3">
              <View
                className={`w-5 h-5 rounded-full border-2 items-center justify-center ${
                  isSelected ? "border-brand-primary bg-brand-primary" : "border-muted"
                }`}
              >
                {isSelected && (
                  <View className="w-2 h-2 rounded-full bg-bg-primary" />
                )}
              </View>
              <Text
                className={`flex-1 text-base ${
                  isSelected ? "text-brand-primary font-medium" : "text-text-primary"
                }`}
              >
                {option}
              </Text>
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}
