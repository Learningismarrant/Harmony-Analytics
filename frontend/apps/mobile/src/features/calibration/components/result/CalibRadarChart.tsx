import { View, Text } from "react-native";
import { RadarChart } from "@/components/RadarChart";
import type { CalibTraitScoreOut, RadarPoint } from "@harmony/types";

interface Props {
  traits: CalibTraitScoreOut[];
}

function toRadarPoints(traits: CalibTraitScoreOut[]): RadarPoint[] {
  return traits.map((t) => ({
    trait: t.trait,
    label: t.label,
    A: t.score,
    B: t.score,
    fullMark: 100,
  }));
}

export function CalibRadarChart({ traits }: Props) {
  if (traits.length === 0) {
    return (
      <View style={{ padding: 24, alignItems: "center" }}>
        <Text style={{ color: "#64748B", fontSize: 12 }}>
          Aucun trait à afficher.
        </Text>
      </View>
    );
  }

  const data = toRadarPoints(traits);
  return (
    <View style={{ alignItems: "center", marginVertical: 8 }}>
      <RadarChart data={data} />
    </View>
  );
}
