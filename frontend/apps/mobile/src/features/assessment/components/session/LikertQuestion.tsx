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
  const firstLabel = String(options[0]);
  const lastLabel = String(options[options.length - 1]);

  return (
    <View className="gap-4">
      {/* Labels extrêmes */}
      <View className="flex-row justify-between px-1">
        <Text className="text-muted text-xs leading-4" style={{ maxWidth: "38%" }}>
          {firstLabel}
        </Text>
        <Text className="text-muted text-xs leading-4 text-right" style={{ maxWidth: "38%" }}>
          {lastLabel}
        </Text>
      </View>

      {/* Cercles de sélection */}
      <View className="flex-row justify-between px-1">
        {options.map((_, idx) => {
          const value = String(idx + 1);
          const isSelected = selectedValue === value;

          return (
            <TouchableOpacity
              key={value}
              testID={`likert-option-${value}`}
              onPress={() => onSelect(question.id, value)}
              activeOpacity={0.7}
              className="items-center"
              style={{ flex: 1 }}
            >
              <View
                className={`w-12 h-12 rounded-full border-2 items-center justify-center ${
                  isSelected
                    ? "border-brand-primary bg-brand-primary"
                    : "border-bg-border bg-bg-elevated"
                }`}
              >
                <Text
                  className={`text-sm font-bold ${isSelected ? "text-white" : "text-muted"}`}
                >
                  {idx + 1}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}
