import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import {
  TRAINING_AXES,
  MY_PATH,
  LEVEL_CONFIG,
  getAxeStats,
  type TrainingAxe,
} from "@/features/training/data";
import { PathBanner } from "@/features/training/components/PathBanner";
import { AxeCard } from "@/features/training/components/AxeCard";
import { ModuleCard } from "@/features/training/components/ModuleCard";

export default function TrainingScreen() {
  const router = useRouter();
  const [activeAxe, setActiveAxe] = useState<TrainingAxe | null>(null);

  const pathLevel = LEVEL_CONFIG[MY_PATH.level];

  function openModule(moduleId: string) {
    router.push(`/(candidate)/training/${moduleId}`);
  }

  // ── Axe detail view ───────────────────────────────────────────
  if (activeAxe) {
    const stats = getAxeStats(activeAxe);
    return (
      <View className="flex-1 bg-bg-primary">
        {/* Header */}
        <View className="px-5 pt-14 pb-4">
          <TouchableOpacity
            onPress={() => setActiveAxe(null)}
            className="flex-row items-center gap-x-1.5 mb-3"
          >
            <Ionicons name="chevron-back" size={16} color="#94A3B8" />
            <Text className="text-muted text-xs">All training</Text>
          </TouchableOpacity>
          <View className="flex-row items-center gap-x-3">
            <View
              className="w-10 h-10 rounded-xl items-center justify-center"
              style={{ backgroundColor: `${activeAxe.color}22` }}
            >
              <Text style={{ fontSize: 20 }}>{activeAxe.icon}</Text>
            </View>
            <View className="flex-1">
              <Text
                className="text-text-primary font-black"
                style={{ fontSize: 16, letterSpacing: 3 }}
              >
                {activeAxe.title.toUpperCase()}
              </Text>
              <Text className="text-muted text-xs mt-0.5">{activeAxe.subtitle}</Text>
            </View>
          </View>
        </View>

        {/* Axe progress */}
        <View className="px-5 mb-2">
          <View className="bg-bg-secondary border border-bg-border rounded-xl p-4">
            <View className="flex-row items-center justify-between mb-2">
              <Text className="text-muted text-xs">Progression de l'axe</Text>
              <Text style={{ color: activeAxe.color, fontSize: 12, fontWeight: "700" }}>
                {stats.completed}/{stats.total} · {stats.pct}%
              </Text>
            </View>
            <View className="h-2 rounded-full bg-bg-primary">
              <View
                className="h-2 rounded-full"
                style={{ width: `${stats.pct}%`, backgroundColor: activeAxe.color }}
              />
            </View>
            <Text className="text-muted text-xs mt-2 leading-4">
              {activeAxe.trigger_description}
            </Text>
          </View>
        </View>

        {/* Modules list */}
        <ScrollView
          className="flex-1"
          contentContainerStyle={{ paddingHorizontal: 20, paddingTop: 8, paddingBottom: 48 }}
          showsVerticalScrollIndicator={false}
        >
          {activeAxe.modules.map((mod, i) => (
            <View key={mod.id}>
              <ModuleCard
                module={mod}
                axeColor={activeAxe.color}
                onPress={() => openModule(mod.id)}
                isCurrentInPath={
                  MY_PATH.current_module_id === mod.id ||
                  MY_PATH.queued_module_ids.includes(mod.id)
                }
              />
              {i < activeAxe.modules.length - 1 && (
                <View className="ml-3.5 w-px bg-bg-border" style={{ height: 4 }} />
              )}
            </View>
          ))}

          <View className="flex-row items-start gap-x-2 px-1 mt-4">
            <Ionicons name="flash-outline" size={13} color="#A67C52" style={{ marginTop: 1 }} />
            <Text className="text-muted text-xs leading-4 flex-1">
              Les modules verrouillés se débloquent automatiquement à mesure que vous progressez ou lorsque vos résultats aux tests évoluent.
            </Text>
          </View>
        </ScrollView>
      </View>
    );
  }

  // ── Overview ─────────────────────────────────────────────────
  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header */}
      <View className="px-5 pt-14 pb-4 flex-row items-start justify-between">
        <View>
          <Text
            className="text-text-primary font-black"
            style={{ fontSize: 18, letterSpacing: 6 }}
          >
            TRAINING
          </Text>
          <Text className="text-muted text-xs mt-0.5" style={{ letterSpacing: 2 }}>
            PARCOURS PERSONNALISÉ
          </Text>
        </View>
        <View
          className="px-3 py-1.5 rounded-xl items-center"
          style={{ backgroundColor: `${pathLevel.color}22` }}
        >
          <Text style={{ color: pathLevel.color, fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
            {pathLevel.label.toUpperCase()}
          </Text>
          <Text style={{ color: pathLevel.color, fontSize: 8, opacity: 0.7 }}>
            {MY_PATH.level === "junior" ? "0–2 yrs" : MY_PATH.level === "mid" ? "2–6 yrs" : "6+ yrs"}
          </Text>
        </View>
      </View>

      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 4, paddingBottom: 48 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Personalized path banner */}
        <PathBanner onPressModule={openModule} />

        {/* Section: 4 axes */}
        <View className="flex-row items-center justify-between mb-3">
          <Text className="text-muted text-xs tracking-widest uppercase">
            Les 4 grands axes
          </Text>
          <Text className="text-muted text-xs">
            {TRAINING_AXES.reduce((acc, a) => acc + getAxeStats(a).completed, 0)}/
            {TRAINING_AXES.reduce((acc, a) => acc + getAxeStats(a).total, 0)} modules
          </Text>
        </View>

        {TRAINING_AXES.map((axe) => (
          <AxeCard key={axe.id} axe={axe} onPress={() => setActiveAxe(axe)} />
        ))}

        <View className="flex-row items-start gap-x-2 px-1 mt-2">
          <Ionicons
            name="information-circle-outline"
            size={13}
            color="#718096"
            style={{ marginTop: 1 }}
          />
          <Text className="text-muted text-xs leading-4 flex-1">
            Votre parcours est assemblé automatiquement à partir de vos résultats aux tests psychométriques. Complétez vos évaluations pour débloquer davantage de modules.
          </Text>
        </View>

        <View className="items-center mt-10 mb-2">
          <Text
            style={{ color: "#718096", fontSize: 8, letterSpacing: 4, fontWeight: "700", opacity: 0.4 }}
          >
            HARMONY · YACHTING TRAINING CENTER
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}
