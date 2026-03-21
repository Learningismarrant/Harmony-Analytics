import { View, Text } from "react-native";
import type { CalibTraitScoreOut } from "@harmony/types";

interface Props {
  trait: CalibTraitScoreOut;
}

function getRingColor(score: number): string {
  if (score >= 70) return "#2E8A5C";
  if (score >= 40) return "#9A7030";
  return "#883838";
}

export function CalibScoreRing({ trait }: Props) {
  const color = getRingColor(trait.score);

  return (
    <View style={{ alignItems: "center", margin: 8 }}>
      {/* Cercle */}
      <View
        style={{
          width: 120,
          height: 120,
          borderRadius: 60,
          borderWidth: 4,
          borderColor: color,
          backgroundColor: `${color}11`,
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 8,
        }}
      >
        <Text
          style={{
            color: "#F1F4F8",
            fontSize: 28,
            fontWeight: "900",
          }}
        >
          {Math.round(trait.score)}
        </Text>
      </View>
      {/* Label */}
      <Text
        style={{
          color: "#94A3B8",
          fontSize: 11,
          fontWeight: "700",
          textAlign: "center",
          maxWidth: 100,
        }}
        numberOfLines={2}
      >
        {trait.label}
      </Text>
    </View>
  );
}
