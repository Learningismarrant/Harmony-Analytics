import { View, Text } from "react-native";
import type { CalibTraitScoreOut } from "@harmony/types";

interface Props {
  traits: CalibTraitScoreOut[];
}

function getBarColor(score: number): string {
  if (score >= 70) return "#2E8A5C";
  if (score >= 40) return "#9A7030";
  return "#883838";
}

export function CalibTraitBars({ traits }: Props) {
  if (traits.length === 0) {
    return (
      <Text style={{ color: "#64748B", fontSize: 12, textAlign: "center", padding: 16 }}>
        Aucun trait disponible.
      </Text>
    );
  }

  return (
    <View style={{ gap: 14 }}>
      {traits.map((trait) => {
        const color = getBarColor(trait.score);
        return (
          <View key={trait.trait} testID={`trait-bar-${trait.trait}`}>
            {/* Label + score */}
            <View
              style={{
                flexDirection: "row",
                justifyContent: "space-between",
                marginBottom: 6,
                alignItems: "center",
              }}
            >
              <Text style={{ color: "#CBD5E1", fontSize: 12, fontWeight: "700", flex: 1 }}>
                {trait.label}
              </Text>
              <Text style={{ color, fontSize: 12, fontWeight: "800" }}>
                {Math.round(trait.score)}
              </Text>
            </View>

            {/* Barre de fond */}
            <View
              style={{
                height: 8,
                backgroundColor: "#0D1B2A",
                borderRadius: 4,
                overflow: "hidden",
              }}
            >
              {/* Barre de progression */}
              <View
                style={{
                  height: "100%",
                  width: `${Math.min(100, Math.max(0, trait.score))}%`,
                  backgroundColor: color,
                  borderRadius: 4,
                }}
              />
            </View>
          </View>
        );
      })}
    </View>
  );
}
