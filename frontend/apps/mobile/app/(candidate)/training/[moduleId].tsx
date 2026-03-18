import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import {
  getModuleById,
  getAxeById,
  MODULE_TYPE_CONFIG,
  type ChecklistCategory,
  type ExerciseStep,
  type LessonSection,
  type SelfAssessmentQuestion,
} from "@/features/training/data";

// ── Sub-components ────────────────────────────────────────────────

function LessonView({ sections }: { sections: LessonSection[] }) {
  if (sections.length === 0) {
    return (
      <View className="items-center py-8">
        <Text className="text-muted text-sm">Contenu en cours de rédaction</Text>
        <Text className="text-slate text-xs mt-1">Coming soon</Text>
      </View>
    );
  }
  return (
    <View className="gap-y-5">
      {sections.map((section, i) => (
        <View key={i}>
          <Text className="text-text-primary font-semibold text-sm mb-2">
            {section.title}
          </Text>
          <Text className="text-muted text-sm leading-6">{section.body}</Text>
        </View>
      ))}
    </View>
  );
}

function ExerciseView({
  objective,
  steps,
  debrief,
}: {
  objective: string;
  steps: ExerciseStep[];
  debrief: string;
}) {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  function toggleStep(n: number) {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      next.has(n) ? next.delete(n) : next.add(n);
      return next;
    });
  }

  return (
    <View className="gap-y-5">
      {/* Objective */}
      <View
        className="rounded-xl p-4"
        style={{ backgroundColor: "#A67C5215", borderWidth: 1, borderColor: "#A67C5233" }}
      >
        <View className="flex-row items-center gap-x-2 mb-2">
          <Ionicons name="flag-outline" size={14} color="#A67C52" />
          <Text style={{ color: "#A67C52", fontSize: 11, fontWeight: "700", letterSpacing: 1 }}>
            OBJECTIF
          </Text>
        </View>
        <Text className="text-muted text-sm leading-5">{objective}</Text>
      </View>

      {/* Steps */}
      <View className="gap-y-3">
        {steps.map((step) => {
          const done = completedSteps.has(step.number);
          return (
            <TouchableOpacity
              key={step.number}
              onPress={() => toggleStep(step.number)}
              className="rounded-xl p-4"
              style={{
                backgroundColor: done ? "#1A2C42" : "#0D1B2A",
                borderWidth: 1,
                borderColor: done ? "#5A827944" : "#1E3050",
              }}
              activeOpacity={0.8}
            >
              <View className="flex-row items-start gap-x-3">
                <View
                  className="w-6 h-6 rounded-full items-center justify-center mt-0.5"
                  style={{
                    backgroundColor: done ? "#5A827922" : "#1E3050",
                    borderWidth: 1.5,
                    borderColor: done ? "#5A8279" : "#1E3050",
                  }}
                >
                  {done ? (
                    <Ionicons name="checkmark" size={12} color="#5A8279" />
                  ) : (
                    <Text style={{ color: "#94A3B8", fontSize: 10, fontWeight: "700" }}>
                      {step.number}
                    </Text>
                  )}
                </View>
                <View className="flex-1">
                  <View className="flex-row items-center justify-between">
                    <Text
                      className="font-semibold text-sm"
                      style={{ color: done ? "#94A3B8" : "#F1F4F8" }}
                    >
                      {step.title}
                    </Text>
                    <Text className="text-slate text-xs">{step.estimated_min} min</Text>
                  </View>
                  <Text
                    className="text-xs mt-1 leading-4"
                    style={{ color: done ? "#718096" : "#94A3B8" }}
                  >
                    {step.description}
                  </Text>
                </View>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Debrief */}
      {debrief && (
        <View
          className="rounded-xl p-4"
          style={{ backgroundColor: "#1A2C42", borderWidth: 1, borderColor: "#243347" }}
        >
          <View className="flex-row items-center gap-x-2 mb-2">
            <Ionicons name="bulb-outline" size={14} color="#A68D6A" />
            <Text style={{ color: "#A68D6A", fontSize: 11, fontWeight: "700", letterSpacing: 1 }}>
              DÉBRIEF
            </Text>
          </View>
          <Text className="text-muted text-sm leading-5">{debrief}</Text>
        </View>
      )}
    </View>
  );
}

function ChecklistView({
  intro,
  categories,
  downloadable,
}: {
  intro: string;
  categories: ChecklistCategory[];
  downloadable: boolean;
}) {
  const [checked, setChecked] = useState<Set<string>>(new Set());

  function toggle(key: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  const totalItems = categories.reduce((acc, c) => acc + c.items.length, 0);
  const checkedCount = checked.size;

  return (
    <View className="gap-y-4">
      {/* Intro */}
      <Text className="text-muted text-sm leading-5">{intro}</Text>

      {/* Progress */}
      <View className="bg-bg-secondary border border-bg-border rounded-xl p-3">
        <View className="flex-row justify-between mb-1.5">
          <Text className="text-muted text-xs">Checklist complétée</Text>
          <Text style={{ color: "#5A8279", fontSize: 11, fontWeight: "700" }}>
            {checkedCount}/{totalItems}
          </Text>
        </View>
        <View className="h-1.5 rounded-full bg-bg-primary">
          <View
            className="h-1.5 rounded-full"
            style={{
              width: totalItems ? `${(checkedCount / totalItems) * 100}%` : "0%",
              backgroundColor: "#5A8279",
            }}
          />
        </View>
      </View>

      {/* Categories */}
      {categories.map((cat) => (
        <View key={cat.category} className="bg-bg-secondary border border-bg-border rounded-2xl overflow-hidden">
          <View className="px-4 py-3 border-b border-bg-border">
            <Text className="text-text-primary text-sm font-semibold">{cat.category}</Text>
          </View>
          {cat.items.map((item, i) => {
            const key = `${cat.category}-${i}`;
            const done = checked.has(key);
            return (
              <TouchableOpacity
                key={key}
                onPress={() => toggle(key)}
                className="flex-row items-start px-4 py-3"
                style={{
                  borderBottomWidth: i < cat.items.length - 1 ? 1 : 0,
                  borderBottomColor: "#1E3050",
                }}
                activeOpacity={0.7}
              >
                <View
                  className="w-5 h-5 rounded-md items-center justify-center mr-3 mt-0.5"
                  style={{
                    backgroundColor: done ? "#5A827922" : "#0D1B2A",
                    borderWidth: 1.5,
                    borderColor: done ? "#5A8279" : "#1E3050",
                  }}
                >
                  {done && <Ionicons name="checkmark" size={11} color="#5A8279" />}
                </View>
                <Text
                  className="flex-1 text-sm leading-5"
                  style={{ color: done ? "#718096" : "#F1F4F8" }}
                >
                  {item}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      ))}

      {/* Download CTA */}
      {downloadable && (
        <TouchableOpacity
          className="flex-row items-center justify-center gap-x-2 py-3 rounded-xl"
          style={{ backgroundColor: "#5A827933", borderWidth: 1, borderColor: "#5A827955" }}
          onPress={() => {}} // TODO: implement PDF download
        >
          <Ionicons name="download-outline" size={16} color="#5A8279" />
          <Text style={{ color: "#5A8279", fontSize: 13, fontWeight: "600" }}>
            Télécharger en PDF
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

function SelfAssessmentView({
  intro,
  questions,
}: {
  intro: string;
  questions: SelfAssessmentQuestion[];
}) {
  const [answers, setAnswers] = useState<Record<string, number>>({});

  function setAnswer(id: string, value: number) {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  }

  const answered = Object.keys(answers).length;

  return (
    <View className="gap-y-4">
      <Text className="text-muted text-sm leading-5">{intro}</Text>

      {questions.map((q) => {
        const val = answers[q.id];
        return (
          <View
            key={q.id}
            className="bg-bg-secondary border border-bg-border rounded-2xl p-4"
          >
            <Text className="text-text-primary text-sm font-medium mb-4 leading-5">
              {q.text}
            </Text>

            {/* 5-point scale */}
            <View className="gap-y-2">
              {[1, 2, 3, 4, 5].map((v) => (
                <TouchableOpacity
                  key={v}
                  onPress={() => setAnswer(q.id, v)}
                  className="flex-row items-center py-2.5 px-3 rounded-xl"
                  style={{
                    backgroundColor: val === v ? "#A67C5222" : "#0D1B2A",
                    borderWidth: 1,
                    borderColor: val === v ? "#A67C5255" : "#1E3050",
                  }}
                >
                  <View
                    className="w-5 h-5 rounded-full items-center justify-center mr-3"
                    style={{
                      backgroundColor: val === v ? "#A67C5233" : "#1E3050",
                      borderWidth: 1.5,
                      borderColor: val === v ? "#A67C52" : "#1E3050",
                    }}
                  >
                    {val === v && (
                      <View className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#A67C52" }} />
                    )}
                  </View>
                  <Text className="text-muted text-xs flex-1">
                    {v === 1
                      ? q.scale_low
                      : v === 5
                      ? q.scale_high
                      : v === 3
                      ? "Neutre"
                      : v === 2
                      ? "Plutôt non"
                      : "Plutôt oui"}
                  </Text>
                  <Text className="text-slate text-xs">{v}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        );
      })}

      {answered === questions.length && (
        <View
          className="rounded-xl p-4 items-center"
          style={{ backgroundColor: "#5A827922", borderWidth: 1, borderColor: "#5A827933" }}
        >
          <Ionicons name="checkmark-circle" size={24} color="#5A8279" />
          <Text style={{ color: "#5A8279", fontSize: 13, fontWeight: "700", marginTop: 8 }}>
            Auto-évaluation complète
          </Text>
          <Text className="text-muted text-xs mt-1 text-center">
            Vos réponses calibrent les modules suivants de votre parcours.
          </Text>
        </View>
      )}
    </View>
  );
}

// ── Main screen ───────────────────────────────────────────────────

export default function ModuleScreen() {
  const { moduleId } = useLocalSearchParams<{ moduleId: string }>();
  const router = useRouter();

  const mod = getModuleById(moduleId ?? "");
  const axe = mod ? getAxeById(mod.axe_id) : undefined;

  if (!mod || !axe) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center px-6">
        <Ionicons name="alert-circle-outline" size={32} color="#9C6B6B" />
        <Text className="text-text-primary font-semibold mt-3">Module introuvable</Text>
        <Text className="text-muted text-sm mt-1 text-center">
          Ce module n'existe pas ou a été déplacé.
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="mt-4 px-4 py-2 rounded-xl border border-bg-border"
        >
          <Text className="text-muted text-sm">Retour</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const typeConfig = MODULE_TYPE_CONFIG[mod.type];

  return (
    <View className="flex-1 bg-bg-primary">
      {/* Header */}
      <View className="px-5 pt-14 pb-4">
        <TouchableOpacity
          onPress={() => router.back()}
          className="flex-row items-center gap-x-1.5 mb-4"
        >
          <Ionicons name="chevron-back" size={16} color="#94A3B8" />
          <Text className="text-muted text-xs">{axe.title}</Text>
        </TouchableOpacity>

        {/* Module meta */}
        <View className="flex-row items-center gap-x-2 mb-3">
          <View
            className="px-2.5 py-1 rounded-full"
            style={{ backgroundColor: `${typeConfig.color}33` }}
          >
            <Text style={{ color: typeConfig.color, fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
              {typeConfig.icon} {typeConfig.label.toUpperCase()}
            </Text>
          </View>
          <View className="flex-row items-center gap-x-1">
            <Ionicons name="time-outline" size={12} color="#718096" />
            <Text className="text-slate text-xs">{mod.duration_min} min</Text>
          </View>
          <Text style={{ color: axe.color, fontSize: 11, fontWeight: "600" }}>
            +{mod.points} pts
          </Text>
        </View>

        <Text
          className="text-text-primary font-black"
          style={{ fontSize: 17, letterSpacing: 1 }}
        >
          {mod.title}
        </Text>
        <Text className="text-muted text-sm mt-1">{mod.subtitle}</Text>
      </View>

      {/* Axe tag */}
      <View className="px-5 mb-2">
        <View
          className="flex-row items-center gap-x-2 px-3 py-2 rounded-xl self-start"
          style={{ backgroundColor: `${axe.color}15` }}
        >
          <Text style={{ fontSize: 14 }}>{axe.icon}</Text>
          <Text style={{ color: axe.color, fontSize: 11, fontWeight: "600" }}>{axe.title}</Text>
        </View>
      </View>

      {/* Separator */}
      <View className="mx-5 h-px bg-bg-border mb-4" />

      {/* Content */}
      <ScrollView
        className="flex-1"
        contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 120 }}
        showsVerticalScrollIndicator={false}
      >
        {mod.content.type === "lesson" && (
          <LessonView sections={mod.content.data.sections} />
        )}
        {mod.content.type === "exercise" && (
          <ExerciseView
            objective={mod.content.data.objective}
            steps={mod.content.data.steps}
            debrief={mod.content.data.debrief}
          />
        )}
        {mod.content.type === "checklist" && (
          <ChecklistView
            intro={mod.content.data.intro}
            categories={mod.content.data.categories}
            downloadable={mod.content.data.downloadable}
          />
        )}
        {mod.content.type === "self_assessment" && (
          <SelfAssessmentView
            intro={mod.content.data.intro}
            questions={mod.content.data.questions}
          />
        )}
      </ScrollView>

      {/* CTA — Mark complete */}
      {mod.status !== "completed" && (
        <View
          className="absolute bottom-0 left-0 right-0 px-5 pb-8 pt-4"
          style={{ backgroundColor: "#0D1B2A", borderTopWidth: 1, borderTopColor: "#1E3050" }}
        >
          <TouchableOpacity
            className="flex-row items-center justify-center gap-x-2 py-4 rounded-xl"
            style={{ backgroundColor: axe.color }}
            onPress={() => {}} // TODO: mark as completed + update path
            activeOpacity={0.85}
          >
            <Ionicons name="checkmark-circle-outline" size={18} color="#0D1B2A" />
            <Text style={{ color: "#0D1B2A", fontSize: 14, fontWeight: "800" }}>
              Marquer comme terminé
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {mod.status === "completed" && (
        <View
          className="absolute bottom-0 left-0 right-0 px-5 pb-8 pt-4 flex-row items-center justify-center gap-x-2"
          style={{ backgroundColor: "#0D1B2A", borderTopWidth: 1, borderTopColor: "#1E3050" }}
        >
          <Ionicons name="checkmark-circle" size={18} color="#5A8279" />
          <Text style={{ color: "#5A8279", fontSize: 13, fontWeight: "700" }}>
            Module complété
          </Text>
        </View>
      )}
    </View>
  );
}
