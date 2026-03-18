import { View, Text, ScrollView, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { TestType } from "@harmony/types";

interface Props {
  data: {
    name?: string;
    instructions?: string | null;
    test_type?: TestType;
  };
  onStart: () => void;
}

const DURATION_BY_TYPE: Record<string, number> = {
  tirt: 25,
  cognitive: 20,
  likert: 15,
  free: 10,
};

export function InstructionsView({ data, onStart }: Props) {
  const isCognitive = data.test_type === "cognitive";
  const accentColor = isCognitive ? "#94A3B8" : "#A67C52";
  const duration = DURATION_BY_TYPE[data.test_type ?? "likert"] ?? 15;

  const instructions = [
    data.instructions ?? "Répondez avec franchise et spontanéité pour obtenir l'analyse la plus fidèle à votre profil.",
    "Assurez-vous d'être dans un environnement calme et sans distractions.",
    "Une fois lancé, le test ne peut pas être mis en pause.",
  ];

  return (
    <View className="flex-1 bg-bg-primary p-6 justify-center">
      {/* Header */}
      <View className="items-center mb-8">
        <View
          className="w-20 h-20 rounded-full border-2 items-center justify-center mb-5 bg-bg-secondary"
          style={{ borderColor: accentColor, borderStyle: "dashed" }}
        >
          <Ionicons
            name={isCognitive ? "school" : "compass-outline"}
            size={40}
            color={accentColor}
          />
        </View>

        <Text className="text-ice text-xl font-black text-center tracking-[1.5px] mb-4">
          {data.name?.toUpperCase() ?? "BRIEFING DE MISSION"}
        </Text>

        <View className="flex-row gap-2.5">
          <View className="flex-row items-center bg-white/5 px-3 py-1.5 rounded-full gap-1.5">
            <Ionicons name="time-outline" size={14} color="#94A3B8" />
            <Text className="text-silver text-[10px] font-extrabold tracking-[0.5px]">
              {duration} MINUTES
            </Text>
          </View>
          <View className="flex-row items-center bg-white/5 px-3 py-1.5 rounded-full gap-1.5">
            <Ionicons name="flash-outline" size={14} color="#94A3B8" />
            <Text className="text-silver text-[10px] font-extrabold tracking-[0.5px]">
              FOCUS REQUIS
            </Text>
          </View>
        </View>
      </View>

      {/* Card instructions */}
      <View
        className="bg-bg-secondary rounded-3xl p-6 border border-bg-border"
        style={{ maxHeight: "65%" }}
      >
        <Text className="text-silver text-[11px] font-black tracking-[2px] text-center mb-5">
          CONSIGNES DE NAVIGATION
        </Text>

        <ScrollView showsVerticalScrollIndicator={false} style={{ maxHeight: 200 }} className="mb-5">
          {instructions.map((text, i) => (
            <View key={i} className="flex-row mb-4 items-start">
              <View
                className="w-1.5 h-1.5 rounded-full mt-[7px] mr-3 flex-shrink-0"
                style={{ backgroundColor: accentColor }}
              />
              <Text className="flex-1 text-sm text-text-secondary leading-[22px]">{text}</Text>
            </View>
          ))}
        </ScrollView>

        {/* Privacy */}
        <View className="flex-row items-center bg-bg-elevated p-3 rounded-xl gap-2.5 mb-5">
          <Ionicons name="shield-checkmark-outline" size={16} color="#94A3B8" />
          <Text className="flex-1 text-[10px] text-slate leading-[14px] font-medium">
            Données traitées pour le recrutement et le management de bord
          </Text>
        </View>

        <TouchableOpacity
          onPress={onStart}
          className="w-full h-14 rounded-[18px] items-center justify-center"
          style={{ backgroundColor: accentColor }}
          activeOpacity={0.85}
        >
          <Text className="text-white font-black tracking-wider text-sm">
            LANCER L&apos;ANALYSE
          </Text>
        </TouchableOpacity>
      </View>

      <Text className="text-center text-[10px] text-silver font-bold mt-6 tracking-[1px]">
        VOTRE RÉSULTAT SERA TRANSMIS AUTOMATIQUEMENT
      </Text>
    </View>
  );
}
