import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { identityApi, queryKeys } from "@harmony/api";
import { useAuthStore } from "@/store/auth.store";

function StatCard({ label, value, color = "#0EA5E9" }: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <View className="flex-1 bg-bg-elevated border border-bg-border rounded-xl p-3">
      <Text style={{ color }} className="text-xl font-bold">{value}</Text>
      <Text className="text-muted text-xs mt-0.5">{label}</Text>
    </View>
  );
}

function ScoreBar({ trait, score }: { trait: string; score: number }) {
  const pct = Math.round(score);
  const barColor =
    pct >= 75 ? "#22C55E" : pct >= 50 ? "#F59E0B" : "#EF4444";

  return (
    <View className="mb-3">
      <View className="flex-row justify-between mb-1">
        <Text className="text-text-primary text-sm capitalize">{trait.replace(/_/g, " ")}</Text>
        <Text className="text-muted text-sm">{pct}</Text>
      </View>
      <View className="h-1.5 bg-bg-border rounded-full overflow-hidden">
        <View
          style={{ width: `${pct}%`, backgroundColor: barColor }}
          className="h-full rounded-full"
        />
      </View>
    </View>
  );
}

export default function ProfileScreen() {
  const { crewProfileId, logout } = useAuthStore();

  const { data: profile, isLoading } = useQuery({
    queryKey: queryKeys.identity.fullProfile(crewProfileId ?? 0),
    queryFn: () => identityApi.getFullProfile(crewProfileId!),
    enabled: crewProfileId !== null,
  });

  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <Text className="text-muted">Loading profile…</Text>
      </View>
    );
  }

  const identity = profile?.identity;
  const crew = profile?.crew;
  const reports = profile?.reports ?? [];

  // Extract Big Five scores from most recent report
  const bigFiveReport = reports.find((r) =>
    r.test_name.includes("big_five"),
  );
  const bigFiveTraits = bigFiveReport
    ? (bigFiveReport.summary as Record<string, { score: number }>)
    : null;

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
    >
      {/* Avatar + name */}
      <View className="items-center mb-6">
        <View className="w-20 h-20 rounded-full bg-brand-primary/20 border-2 border-brand-primary/40
                          items-center justify-center mb-3">
          <Text className="text-brand-primary text-3xl font-bold">
            {identity?.name?.charAt(0) ?? "?"}
          </Text>
        </View>
        <Text className="text-text-primary text-xl font-semibold">{identity?.name}</Text>
        <Text className="text-muted text-sm mt-0.5">{crew?.position_targeted}</Text>
        {identity?.is_harmony_verified && (
          <View className="flex-row items-center gap-1 mt-1.5">
            <Text className="text-brand-primary text-xs">✓ Harmony Verified</Text>
          </View>
        )}
      </View>

      {/* Quick stats */}
      <View className="flex-row gap-3 mb-5">
        <StatCard
          label="Experience"
          value={`${crew?.experience_years ?? 0}yr`}
        />
        <StatCard
          label="Tests done"
          value={reports.length}
          color="#6366F1"
        />
        <StatCard
          label="Status"
          value={crew?.availability_status === "available" ? "✓" : "●"}
          color={crew?.availability_status === "available" ? "#22C55E" : "#F59E0B"}
        />
      </View>

      {/* Big Five if available */}
      {bigFiveTraits && (
        <View className="bg-bg-secondary border border-bg-border rounded-xl p-4 mb-4">
          <Text className="text-text-primary font-semibold mb-3">
            Personality profile
          </Text>
          {Object.entries(bigFiveTraits).map(([trait, data]) => (
            <ScoreBar key={trait} trait={trait} score={data.score} />
          ))}
        </View>
      )}

      {/* Experiences */}
      {(profile?.experiences ?? []).length > 0 && (
        <View className="bg-bg-secondary border border-bg-border rounded-xl p-4 mb-4">
          <Text className="text-text-primary font-semibold mb-3">Experience</Text>
          {profile!.experiences.map((exp) => (
            <View
              key={exp.id}
              className="border-l-2 border-brand-primary/30 pl-3 mb-3"
            >
              <Text className="text-text-primary text-sm font-medium">
                {exp.role} — {exp.yacht_name}
              </Text>
              <Text className="text-muted text-xs mt-0.5">
                {new Date(exp.start_date).getFullYear()}
                {exp.end_date
                  ? ` → ${new Date(exp.end_date).getFullYear()}`
                  : " → present"}
              </Text>
              {exp.is_harmony_approved && (
                <Text className="text-brand-primary text-xs">✓ Verified</Text>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Sign out */}
      <TouchableOpacity
        onPress={() =>
          Alert.alert("Sign out", "Are you sure?", [
            { text: "Cancel", style: "cancel" },
            { text: "Sign out", style: "destructive", onPress: logout },
          ])
        }
        className="border border-bg-border rounded-xl py-3 items-center mt-2"
      >
        <Text className="text-muted text-sm">Sign out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}
