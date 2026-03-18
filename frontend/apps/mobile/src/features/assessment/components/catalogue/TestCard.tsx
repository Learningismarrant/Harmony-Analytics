import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { TestInfoOut } from "@harmony/types";

// ── Theming per test type ─────────────────────────────────────────────────────

const TYPE_CONFIG: Record<
  string,
  {
    color: string;
    label: string;
    focus: string;
    icon: keyof typeof Ionicons.glyphMap;
    duration: string;
  }
> = {
  cognitive: {
    color: "#5B8DB8",
    label: "CAPACITÉS COGNITIVES",
    focus: "LOGIQUE & RÉFLEXION",
    icon: "layers-outline",
    duration: "~20 min",
  },
  likert: {
    color: "#A67C52",
    label: "ANALYSE DE PROFIL",
    focus: "SOFT SKILLS",
    icon: "shield-checkmark-outline",
    duration: "~15 min",
  },
  free: {
    color: "#94A3B8",
    label: "ÉVALUATION LIBRE",
    focus: "TEXTE LIBRE",
    icon: "create-outline",
    duration: "~10 min",
  },
};

const DEFAULT_CONFIG = TYPE_CONFIG.likert;

// ── Component ─────────────────────────────────────────────────────────────────

interface TestCardProps {
  test: TestInfoOut;
  isCompleted: boolean;
  onPress: () => void;
}

export function TestCard({ test, isCompleted, onPress }: TestCardProps) {
  const cfg = TYPE_CONFIG[test.test_type] ?? DEFAULT_CONFIG;

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.85}
      style={{ opacity: isCompleted ? 0.7 : 1, marginBottom: 14 }}
    >
      <View
        style={{
          backgroundColor: "#1A2C42",
          borderRadius: 14,
          borderLeftWidth: 3,
          borderLeftColor: cfg.color,
          borderTopWidth: 1,
          borderTopColor: "#1E3050",
          borderRightWidth: 1,
          borderRightColor: "#1E3050",
          borderBottomWidth: 1,
          borderBottomColor: "#1E3050",
          padding: 18,
          shadowColor: "#000",
          shadowOpacity: 0.15,
          shadowRadius: 8,
          elevation: 3,
        }}
      >
        {/* Header row */}
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
          <View style={{ flex: 1 }}>
            <Text
              style={{ color: "#F1F4F8", fontSize: 14, fontWeight: "800", letterSpacing: 0.5 }}
              numberOfLines={1}
            >
              {test.name.toUpperCase()}
            </Text>

            {/* Type badge */}
            <View
              style={{
                alignSelf: "flex-start",
                marginTop: 6,
                paddingHorizontal: 8,
                paddingVertical: 3,
                borderRadius: 6,
                backgroundColor: `${cfg.color}22`,
              }}
            >
              <Text style={{ color: cfg.color, fontSize: 9, fontWeight: "800", letterSpacing: 0.5 }}>
                {cfg.label}
              </Text>
            </View>
          </View>

          {/* Icon circle */}
          <View
            style={{
              width: 36,
              height: 36,
              borderRadius: 18,
              backgroundColor: `${cfg.color}18`,
              borderWidth: 1,
              borderColor: `${cfg.color}33`,
              alignItems: "center",
              justifyContent: "center",
              marginLeft: 12,
            }}
          >
            {isCompleted ? (
              <Ionicons name="checkmark" size={18} color="#2E8A5C" />
            ) : (
              <Ionicons name={cfg.icon} size={17} color={cfg.color} />
            )}
          </View>
        </View>

        {/* Description */}
        <Text
          style={{ color: "#94A3B8", fontSize: 12, lineHeight: 18, marginBottom: 14 }}
          numberOfLines={2}
        >
          {test.description}
        </Text>

        {/* Footer */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            borderTopWidth: 1,
            borderTopColor: "#1E3050",
            paddingTop: 11,
          }}
        >
          {/* Duration */}
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginRight: 14 }}>
            <Ionicons name="time-outline" size={11} color="#64748B" />
            <Text style={{ color: "#64748B", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
              {cfg.duration.toUpperCase()}
            </Text>
          </View>

          {/* Focus */}
          <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
            <Ionicons name="options-outline" size={11} color="#64748B" />
            <Text style={{ color: "#64748B", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
              {cfg.focus}
            </Text>
          </View>

          {/* CTA */}
          <View style={{ flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "flex-end", gap: 3 }}>
            {isCompleted ? (
              <>
                <Text style={{ color: "#2E8A5C", fontSize: 10, fontWeight: "800", letterSpacing: 0.5 }}>
                  COMPLÉTÉ
                </Text>
                <Ionicons name="checkmark-circle" size={13} color="#2E8A5C" />
              </>
            ) : (
              <>
                <Text style={{ color: cfg.color, fontSize: 10, fontWeight: "900", letterSpacing: 0.5 }}>
                  DÉMARRER
                </Text>
                <Ionicons name="chevron-forward" size={13} color={cfg.color} />
              </>
            )}
          </View>
        </View>

        {/* Privacy note */}
        <View style={{ flexDirection: "row", alignItems: "center", marginTop: 10, gap: 5, opacity: 0.5 }}>
          <Ionicons name="shield-outline" size={10} color="#94A3B8" />
          <Text style={{ color: "#94A3B8", fontSize: 9, fontStyle: "italic" }}>
            Analyses réservées au recrutement & management de bord
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}
