import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { TrainingModule } from "../data";
import { MODULE_TYPE_CONFIG } from "../data";

interface ModuleCardProps {
  module: TrainingModule;
  axeColor: string;
  onPress: () => void;
  isCurrentInPath?: boolean;
}

const STATUS_CONFIG = {
  completed: { icon: "checkmark-circle" as const, color: "#5A8279", label: "Completed" },
  in_progress: { icon: "play-circle" as const, color: "#A67C52", label: "In progress" },
  available: { icon: "radio-button-off" as const, color: "#94A3B8", label: "Available" },
  locked: { icon: "lock-closed" as const, color: "#1E3050", label: "Locked" },
};

export function ModuleCard({ module: mod, axeColor, onPress, isCurrentInPath }: ModuleCardProps) {
  const statusConfig = STATUS_CONFIG[mod.status];
  const typeConfig = MODULE_TYPE_CONFIG[mod.type];
  const isLocked = mod.status === "locked";

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isLocked}
      className="flex-row items-start py-4"
      style={{ opacity: isLocked ? 0.5 : 1 }}
      activeOpacity={0.7}
    >
      {/* Status icon + vertical connector managed by parent */}
      <View className="items-center mr-4" style={{ width: 28 }}>
        <View
          className="w-7 h-7 rounded-full items-center justify-center"
          style={{
            backgroundColor: isLocked ? "#0D1B2A" : `${statusConfig.color}22`,
            borderWidth: 1.5,
            borderColor: isLocked ? "#1E3050" : statusConfig.color,
          }}
        >
          <Ionicons
            name={statusConfig.icon}
            size={14}
            color={isLocked ? "#1E3050" : statusConfig.color}
          />
        </View>
      </View>

      {/* Content */}
      <View
        className="flex-1 rounded-xl p-3.5"
        style={{
          backgroundColor: mod.status === "in_progress" ? "#1A2C42" : "#0D1B2A",
          borderWidth: 1,
          borderColor:
            mod.status === "in_progress"
              ? `${axeColor}44`
              : mod.status === "completed"
              ? "#1E3050"
              : "#1E3050",
        }}
      >
        {/* Header row */}
        <View className="flex-row items-center justify-between mb-1.5">
          <View className="flex-row items-center gap-x-1.5">
            <View
              className="px-2 py-0.5 rounded-full"
              style={{ backgroundColor: `${typeConfig.color}33` }}
            >
              <Text style={{ color: typeConfig.color, fontSize: 9, fontWeight: "700", letterSpacing: 0.5 }}>
                {typeConfig.label.toUpperCase()}
              </Text>
            </View>
            {isCurrentInPath && (
              <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: `${axeColor}33` }}>
                <Text style={{ color: axeColor, fontSize: 9, fontWeight: "700" }}>
                  PARCOURS
                </Text>
              </View>
            )}
          </View>
          <Text className="text-slate text-xs">{mod.duration_min} min</Text>
        </View>

        <Text className="text-text-primary text-sm font-semibold">{mod.title}</Text>
        <Text className="text-muted text-xs mt-0.5">{mod.subtitle}</Text>

        {mod.trigger_description && !isLocked && (
          <View className="flex-row items-center mt-1.5 gap-x-1">
            <Ionicons name="flash-outline" size={10} color={axeColor} />
            <Text style={{ color: axeColor, fontSize: 10 }}>{mod.trigger_description}</Text>
          </View>
        )}

        {isLocked && mod.trigger_description && (
          <View className="flex-row items-center mt-1.5 gap-x-1">
            <Ionicons name="lock-closed-outline" size={10} color="#718096" />
            <Text className="text-muted text-xs">{mod.trigger_description}</Text>
          </View>
        )}

        {/* Points */}
        <View className="flex-row items-center justify-between mt-2">
          <View className="flex-row items-center gap-x-3">
            {mod.levels.map((lvl) => (
              <Text key={lvl} className="text-slate" style={{ fontSize: 9 }}>
                {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
              </Text>
            ))}
          </View>
          <Text style={{ color: axeColor, fontSize: 10, fontWeight: "600" }}>
            +{mod.points} pts
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}
