import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { TrainingAxe } from "../data";
import { getAxeStats } from "../data";

interface AxeCardProps {
  axe: TrainingAxe;
  onPress: () => void;
}

export function AxeCard({ axe, onPress }: AxeCardProps) {
  const stats = getAxeStats(axe);

  return (
    <TouchableOpacity
      onPress={onPress}
      className="bg-bg-secondary border border-bg-border rounded-2xl p-4 mb-3"
      activeOpacity={0.75}
    >
      <View className="flex-row items-start">
        {/* Icon */}
        <View
          className="w-11 h-11 rounded-xl items-center justify-center mr-3"
          style={{ backgroundColor: `${axe.color}22` }}
        >
          <Text style={{ fontSize: 20 }}>{axe.icon}</Text>
        </View>

        {/* Info */}
        <View className="flex-1">
          <View className="flex-row items-center justify-between">
            <Text className="text-text-primary font-semibold text-sm flex-1 mr-2">
              {axe.title}
            </Text>
            <View className="flex-row items-center gap-x-1">
              <Text style={{ color: axe.color, fontSize: 13, fontWeight: "700" }}>
                {stats.pct}%
              </Text>
              <Ionicons name="chevron-forward" size={14} color="#718096" />
            </View>
          </View>

          <Text className="text-muted text-xs mt-0.5 mb-2">{axe.subtitle}</Text>

          {/* Progress bar */}
          <View className="h-1.5 rounded-full bg-bg-primary mb-2">
            <View
              className="h-1.5 rounded-full"
              style={{ width: `${stats.pct}%`, backgroundColor: axe.color }}
            />
          </View>

          {/* Stats row */}
          <View className="flex-row items-center gap-x-3">
            <View className="flex-row items-center gap-x-1">
              <Ionicons name="checkmark-circle-outline" size={12} color="#5A8279" />
              <Text className="text-muted text-xs">{stats.completed} done</Text>
            </View>
            {stats.in_progress > 0 && (
              <View className="flex-row items-center gap-x-1">
                <Ionicons name="play-circle-outline" size={12} color="#A67C52" />
                <Text className="text-muted text-xs">{stats.in_progress} in progress</Text>
              </View>
            )}
            <View className="flex-row items-center gap-x-1">
              <Ionicons name="layers-outline" size={12} color="#718096" />
              <Text className="text-muted text-xs">{stats.total} modules</Text>
            </View>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}
