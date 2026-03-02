import { View, Text } from "react-native";
import type { TirtDetail } from "@harmony/types";
import { colors } from "@harmony/ui";

interface TirtResultDetailProps {
  tirtDetail: TirtDetail;
}

const DOMAIN_LABELS: Record<string, string> = {
  O: "Openness",
  C: "Conscientiousness",
  E: "Extraversion",
  A: "Agreeableness",
  N: "Neuroticism",
};

const DOMAIN_ORDER = ["O", "C", "E", "A", "N"] as const;

function getBarColor(percentile: number): string {
  if (percentile >= 80) return colors.sociogram.excellent;
  if (percentile >= 65) return colors.sociogram.good;
  if (percentile >= 45) return colors.sociogram.moderate;
  return colors.sociogram.weak;
}

function formatZScore(z: number): string {
  return z >= 0 ? `z = +${z.toFixed(2)}` : `z = ${z.toFixed(2)}`;
}

export function TirtResultDetail({ tirtDetail }: TirtResultDetailProps) {
  const isReliable = tirtDetail.reliability_index >= 0.8;
  const reliableColor = isReliable ? colors.sociogram.excellent : colors.warning;
  const reliableBg = isReliable ? "rgba(46,138,92,0.15)" : "rgba(154,114,48,0.15)";
  const reliableBorder = isReliable ? "rgba(46,138,92,0.35)" : "rgba(154,114,48,0.35)";

  return (
    <View className="w-full">
      <Text className="text-text-primary font-semibold text-base mb-4">
        Personality Profile
      </Text>

      {DOMAIN_ORDER.map((domain) => {
        const detail = tirtDetail[domain];
        if (!detail) return null;

        const barColor = getBarColor(detail.percentile);

        return (
          <View key={domain} className="mb-4">
            <View className="flex-row justify-between items-center mb-1">
              <Text className="text-text-primary text-sm font-medium">
                {DOMAIN_LABELS[domain]}
              </Text>
              <Text className="text-muted text-xs">
                P{Math.round(detail.percentile)}
              </Text>
            </View>

            <View className="h-3 bg-bg-border rounded-full overflow-hidden mb-1">
              <View
                style={{
                  width: `${detail.percentile}%`,
                  backgroundColor: barColor,
                  height: "100%",
                  borderRadius: 9999,
                }}
              />
            </View>

            <Text className="text-muted text-xs">{formatZScore(detail.z_score)}</Text>
          </View>
        );
      })}

      <View className="mt-2 flex-row">
        <View
          className="rounded-full px-3 py-1"
          style={{
            backgroundColor: reliableBg,
            borderWidth: 1,
            borderColor: reliableBorder,
          }}
        >
          <Text
            className="text-xs font-medium"
            style={{ color: reliableColor }}
          >
            {isReliable ? "Reliable" : "Low reliability"}
          </Text>
        </View>
      </View>
    </View>
  );
}
