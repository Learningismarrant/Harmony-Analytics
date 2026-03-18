import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {
  MY_PATH,
  getModuleById,
  LEVEL_CONFIG,
  MODULE_TYPE_CONFIG,
} from "../data";

interface PathBannerProps {
  onPressModule: (moduleId: string) => void;
}

export function PathBanner({ onPressModule }: PathBannerProps) {
  const path = MY_PATH;
  const currentModule = getModuleById(path.current_module_id);
  const levelConfig = LEVEL_CONFIG[path.level];

  if (!currentModule) return null;
  const typeConfig = MODULE_TYPE_CONFIG[currentModule.type];

  return (
    <View className="bg-bg-secondary border border-bg-border rounded-2xl overflow-hidden mb-4">
      {/* Level badge + path name */}
      <View className="px-5 pt-4 pb-3 flex-row items-center justify-between">
        <View>
          <Text
            className="text-text-primary font-bold"
            style={{ fontSize: 13, letterSpacing: 1 }}
          >
            {path.path_name.toUpperCase()}
          </Text>
          <Text className="text-muted text-xs mt-0.5">{path.trigger_summary}</Text>
        </View>
        <View
          className="px-2.5 py-1 rounded-full"
          style={{ backgroundColor: `${levelConfig.color}22` }}
        >
          <Text style={{ color: levelConfig.color, fontSize: 10, fontWeight: "700" }}>
            {levelConfig.label.toUpperCase()}
          </Text>
        </View>
      </View>

      {/* Global progress bar */}
      <View className="px-5 mb-4">
        <View className="flex-row items-center justify-between mb-1.5">
          <Text className="text-muted text-xs">Progression globale</Text>
          <Text style={{ color: "#A67C52", fontSize: 11, fontWeight: "700" }}>
            {path.global_completion_pct}%
          </Text>
        </View>
        <View className="h-1.5 rounded-full bg-bg-primary">
          <View
            className="h-1.5 rounded-full"
            style={{
              width: `${path.global_completion_pct}%`,
              backgroundColor: "#A67C52",
            }}
          />
        </View>
      </View>

      {/* Current module card */}
      <TouchableOpacity
        onPress={() => onPressModule(currentModule.id)}
        className="mx-4 mb-4 rounded-xl overflow-hidden"
        style={{ backgroundColor: "#0D1B2A", borderWidth: 1, borderColor: "#243347" }}
        activeOpacity={0.8}
      >
        <View className="px-4 py-3.5">
          <View className="flex-row items-center justify-between mb-2">
            <View className="flex-row items-center gap-x-2">
              <View
                className="px-2 py-0.5 rounded-full"
                style={{ backgroundColor: `${typeConfig.color}33` }}
              >
                <Text style={{ color: typeConfig.color, fontSize: 9, fontWeight: "700", letterSpacing: 0.5 }}>
                  {typeConfig.label.toUpperCase()} · {currentModule.duration_min} MIN
                </Text>
              </View>
              <View className="px-2 py-0.5 rounded-full" style={{ backgroundColor: "#A67C5233" }}>
                <Text style={{ color: "#A67C52", fontSize: 9, fontWeight: "700" }}>
                  EN COURS
                </Text>
              </View>
            </View>
            <Text style={{ color: "#A67C52", fontSize: 10 }}>+{currentModule.points} pts</Text>
          </View>

          <Text className="text-text-primary font-semibold text-sm">{currentModule.title}</Text>
          <Text className="text-muted text-xs mt-0.5">{currentModule.subtitle}</Text>

          {currentModule.trigger_description && (
            <View className="flex-row items-center mt-2 gap-x-1.5">
              <Ionicons name="flash-outline" size={11} color="#A67C52" />
              <Text style={{ color: "#A67C52", fontSize: 10 }}>
                {currentModule.trigger_description}
              </Text>
            </View>
          )}
        </View>

        <View
          className="flex-row items-center justify-center py-2.5 gap-x-2"
          style={{ backgroundColor: "#A67C5233", borderTopWidth: 1, borderTopColor: "#243347" }}
        >
          <Ionicons name="play-circle-outline" size={16} color="#A67C52" />
          <Text style={{ color: "#A67C52", fontSize: 12, fontWeight: "700" }}>
            Continuer ce module
          </Text>
        </View>
      </TouchableOpacity>

      {/* Queue — next 2 modules */}
      <View className="px-5 pb-4">
        <Text className="text-muted text-xs tracking-widest uppercase mb-2">
          Prochains dans votre parcours
        </Text>
        {path.queued_module_ids.slice(0, 2).map((id, i) => {
          const m = getModuleById(id);
          if (!m) return null;
          const tc = MODULE_TYPE_CONFIG[m.type];
          return (
            <TouchableOpacity
              key={id}
              onPress={() => onPressModule(id)}
              className="flex-row items-center py-2.5"
              style={{
                borderTopWidth: i > 0 ? 1 : 0,
                borderTopColor: "#1E3050",
              }}
            >
              <View
                className="w-7 h-7 rounded-lg items-center justify-center mr-3"
                style={{ backgroundColor: `${tc.color}22` }}
              >
                <Text style={{ fontSize: 14 }}>{tc.icon}</Text>
              </View>
              <View className="flex-1">
                <Text className="text-text-secondary text-xs font-medium">{m.title}</Text>
                <Text className="text-muted text-xs">{m.duration_min} min · {tc.label}</Text>
              </View>
              <Ionicons name="chevron-forward" size={14} color="#718096" />
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}
