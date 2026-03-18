import { View, Text, TouchableOpacity, ActivityIndicator } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { identityApi, queryKeys } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import {
  RadarChart,
  type RadarDataPoint,
} from "@/features/assessment/components/result/RadarChart";
import type { DimensionScoresOut, KeySignalOut } from "@harmony/types";

// ── Dimension label map ───────────────────────────────────────────────────────

const DIMENSION_LABELS: Record<string, string> = {
  agreeableness: "Agreeableness",
  conscientiousness: "Conscientiousness",
  openness: "Openness",
  extraversion: "Extraversion",
  emotional_stability: "Emotional Stability",
  gca: "Fluid Intelligence",
  resilience: "Resilience",
};

// ── Score colour tokens (aligned with @harmony/ui sociogram) ─────────────────

const scoreColor = (v: number): string =>
  v >= 80 ? "#2E8A5C"
  : v >= 65 ? "#5A8A30"
  : v >= 45 ? "#9A7030"
  : "#883838";

// ── ScoreBar (fallback when < 3 dimensions available) ────────────────────────

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = scoreColor(value);
  return (
    <View className="mb-4">
      <View className="flex-row justify-between mb-1.5">
        <Text className="text-muted text-xs">{label}</Text>
        <Text className="text-xs font-semibold" style={{ color }}>{Math.round(value)}</Text>
      </View>
      <View className="h-2 rounded-full bg-bg-primary">
        <View
          className="h-2 rounded-full"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </View>
    </View>
  );
}

// ── CTA to navigate to assessments ───────────────────────────────────────────

function AssessmentCTA({ label }: { label: string }) {
  const router = useRouter();
  return (
    <TouchableOpacity
      className="mt-4 flex-row items-center justify-center gap-x-2 py-3 rounded-xl"
      style={{ backgroundColor: "#A67C5233", borderWidth: 1, borderColor: "#A67C5255" }}
      onPress={() => router.push("/(candidate)/assessment")}
    >
      <Ionicons name="flask-outline" size={16} color="#A67C52" />
      <Text style={{ color: "#A67C52", fontSize: 13, fontWeight: "600" }}>{label}</Text>
    </TouchableOpacity>
  );
}

// ── KeySignals ────────────────────────────────────────────────────────────────

function KeySignalsSection({ signals }: { signals: KeySignalOut[] }) {
  const strengths = signals.filter((s) => s.type === "strength");
  const risks = signals.filter((s) => s.type === "risk");

  return (
    <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5">
      <View className="flex-row items-center mb-4 gap-x-2">
        <Ionicons name="pulse-outline" size={16} color="#A67C52" />
        <Text className="text-text-primary text-sm font-semibold">Key Signals</Text>
      </View>

      {strengths.length > 0 && (
        <View className="mb-3">
          <Text className="text-muted text-xs font-semibold mb-2 uppercase tracking-wider">
            Strengths
          </Text>
          {strengths.map((s, idx) => (
            <View key={idx} className="flex-row items-center py-1.5 gap-x-2">
              <View
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: "#2E8A5C" }}
              />
              <Text className="text-text-primary text-xs flex-1">{s.label}</Text>
            </View>
          ))}
        </View>
      )}

      {risks.length > 0 && (
        <View>
          <Text className="text-muted text-xs font-semibold mb-2 uppercase tracking-wider">
            Watch points
          </Text>
          {risks.map((r, idx) => (
            <View key={idx} className="flex-row items-center py-1.5 gap-x-2">
              <View
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: "#883838" }}
              />
              <Text className="text-text-primary text-xs flex-1">{r.label}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

// ── Coming next (always shown) ────────────────────────────────────────────────

function ComingNextSection() {
  return (
    <View
      className="bg-bg-primary rounded-2xl p-5"
      style={{ borderWidth: 1, borderColor: "#1E3050", borderStyle: "dashed" }}
    >
      <View className="flex-row items-center mb-3 gap-x-2">
        <Ionicons name="hourglass-outline" size={16} color="#94A3B8" />
        <Text className="text-muted text-sm font-medium">Coming next</Text>
      </View>
      {["DNRE — Need for Exploration", "MLPSM — Leadership Style"].map((label) => (
        <View
          key={label}
          className="flex-row items-center py-3 border-b border-bg-border"
        >
          <View
            className="w-8 h-8 rounded-lg items-center justify-center mr-3"
            style={{ backgroundColor: "#1E3050" }}
          >
            <Ionicons name="lock-closed-outline" size={14} color="#718096" />
          </View>
          <Text className="text-muted text-xs">{label}</Text>
          <View className="ml-auto px-2 py-0.5 rounded-full bg-bg-border">
            <Text style={{ color: "#718096", fontSize: 10 }}>Not done</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Build radar data points from DimensionScoresOut ──────────────────────────

function buildRadarData(dimensions: DimensionScoresOut): RadarDataPoint[] {
  return Object.entries(dimensions)
    .filter(([, v]) => v != null)
    .map(([key, v]) => ({
      label: DIMENSION_LABELS[key] ?? key,
      score: v as number,
    }));
}

// ── Main component ────────────────────────────────────────────────────────────

export function HarmonyScoreSection() {
  const crewProfileId = useAuthStore((s) => s.crewProfileId);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.identity.reports(crewProfileId!),
    queryFn: () => identityApi.getReports(crewProfileId!),
    enabled: !!crewProfileId,
  });

  const radarData: RadarDataPoint[] =
    data?.has_data && data.dimensions ? buildRadarData(data.dimensions) : [];

  return (
    <View className="gap-y-4">
      {/* Loading */}
      {isLoading && (
        <View className="py-12 items-center">
          <ActivityIndicator size="large" color="#A67C52" testID="loading-indicator" />
        </View>
      )}

      {/* No crew profile ID */}
      {!crewProfileId && !isLoading && (
        <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
          <Ionicons name="person-outline" size={32} color="#718096" />
          <Text className="text-muted text-sm text-center mt-3">
            No candidate profile found.
          </Text>
        </View>
      )}

      {/* Error */}
      {isError && (
        <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
          <Ionicons name="alert-circle-outline" size={32} color="#883838" />
          <Text className="text-muted text-sm text-center mt-3">
            Unable to load your psychometric report.
          </Text>
        </View>
      )}

      {/* has_data === false */}
      {data && !data.has_data && (
        <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
          <Ionicons name="flask-outline" size={40} color="#A67C52" />
          <Text className="text-text-primary font-semibold text-base mt-4 text-center">
            No psychometric data yet
          </Text>
          {data.message ? (
            <Text className="text-muted text-xs text-center mt-2" style={{ maxWidth: 240 }}>
              {data.message}
            </Text>
          ) : (
            <Text className="text-muted text-xs text-center mt-2" style={{ maxWidth: 240 }}>
              Complete assessments to unlock your Harmony profile.
            </Text>
          )}
          <AssessmentCTA label="Start assessments" />
        </View>
      )}

      {/* has_data === true */}
      {data?.has_data && (
        <>
          {/* Radar chart (≥ 3 dimensions) */}
          {radarData.length >= 3 && (
            <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5">
              <View className="flex-row items-center mb-4 gap-x-2">
                <Ionicons name="analytics-outline" size={16} color="#A67C52" />
                <Text className="text-text-primary text-sm font-semibold">
                  Your Psychometric Profile
                </Text>
              </View>
              <RadarChart data={radarData} />
            </View>
          )}

          {/* Score bars (< 3 dimensions but > 0) */}
          {radarData.length > 0 && radarData.length < 3 && (
            <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5">
              <View className="flex-row items-center mb-4 gap-x-2">
                <Ionicons name="analytics-outline" size={16} color="#A67C52" />
                <Text className="text-text-primary text-sm font-semibold">
                  Your Psychometric Profile
                </Text>
              </View>
              {radarData.map((pt) => (
                <ScoreBar key={pt.label} label={pt.label} value={pt.score} />
              ))}
            </View>
          )}

          {/* Key signals */}
          {data.key_signals && data.key_signals.length > 0 && (
            <KeySignalsSection signals={data.key_signals} />
          )}
        </>
      )}

      {/* Coming next (always shown) */}
      <ComingNextSection />
    </View>
  );
}
