import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSurvey } from "@/features/survey/hooks/useSurvey";
import type { DepartureReason } from "@harmony/types";

const DEPARTURE_REASONS: { value: DepartureReason; label: string }[] = [
  { value: "performance", label: "Performance issues" },
  { value: "team_conflict", label: "Team conflict" },
  { value: "environment", label: "Environment / conditions" },
  { value: "leadership", label: "Leadership" },
  { value: "external", label: "External (health, family...)" },
  { value: "unknown", label: "Unknown" },
];

function ScaleSelector({
  label,
  description,
  value,
  onChange,
}: {
  label: string;
  description?: string;
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <View className="mb-5">
      <Text className="text-text-primary text-sm font-medium mb-0.5">{label}</Text>
      {description ? (
        <Text className="text-muted text-xs mb-2">{description}</Text>
      ) : null}
      <View className="flex-row justify-between">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
          <TouchableOpacity
            key={n}
            onPress={() => onChange(n)}
            className="w-8 h-8 rounded-lg items-center justify-center"
            style={{
              backgroundColor: value === n ? "#4A90B8" : "#1A1F2B",
              borderWidth: 1,
              borderColor: value === n ? "#4A90B8" : "#2A3142",
            }}
          >
            <Text
              className="text-xs font-medium"
              style={{ color: value === n ? "#07090F" : "#8FA3B8" }}
            >
              {n}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <View className="flex-row justify-between mt-1">
        <Text className="text-muted text-xs">Low</Text>
        <Text className="text-muted text-xs">High</Text>
      </View>
    </View>
  );
}

export default function SurveyResponseScreen() {
  const { surveyId } = useLocalSearchParams<{ surveyId: string }>();
  const router = useRouter();
  const { pendingSurveys, respond, isSubmitting } = useSurvey();

  const survey = pendingSurveys.find((s) => s.id === Number(surveyId));
  const isExitInterview = survey?.trigger_type === "exit_interview";

  const [teamCohesion, setTeamCohesion] = useState<number | null>(null);
  const [workloadFelt, setWorkloadFelt] = useState<number | null>(null);
  const [leadershipFit, setLeadershipFit] = useState<number | null>(null);
  const [selfPerformance, setSelfPerformance] = useState<number | null>(null);
  const [intentToStay, setIntentToStay] = useState<number | null>(null);
  const [freeText, setFreeText] = useState("");
  const [departureReason, setDepartureReason] = useState<DepartureReason | null>(null);

  async function handleSubmit() {
    if (!intentToStay) {
      Alert.alert("Required", "Please rate your intent to stay (1-10).");
      return;
    }

    try {
      await respond({
        surveyId: Number(surveyId),
        body: {
          team_cohesion: teamCohesion ?? undefined,
          workload_felt: workloadFelt ?? undefined,
          leadership_fit: leadershipFit ?? undefined,
          self_performance: selfPerformance ?? undefined,
          intent_to_stay: intentToStay,
          free_text: freeText.trim() || undefined,
          departure_reason: departureReason ?? undefined,
        },
      });
      Alert.alert("Thank you", "Your response has been recorded.", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        Alert.alert("Already responded", "You have already responded to this survey.");
        router.back();
      } else {
        Alert.alert("Error", "Could not submit response. Please try again.");
      }
    }
  }

  if (!survey) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center px-6">
        <Text className="text-muted text-center">
          Survey not found or already completed.
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          className="mt-4 border border-bg-border rounded-xl px-6 py-2"
        >
          <Text className="text-muted text-sm">Go back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
    >
      <Text className="text-muted text-xs mb-5">
        {new Date(survey.created_at).toLocaleDateString()} — Rate each dimension from 1 to 10.
      </Text>

      <ScaleSelector
        label="Team cohesion"
        description="How well does the crew work together?"
        value={teamCohesion}
        onChange={setTeamCohesion}
      />

      <ScaleSelector
        label="Workload"
        description="How manageable is your current workload?"
        value={workloadFelt}
        onChange={setWorkloadFelt}
      />

      <ScaleSelector
        label="Leadership"
        description="How well does management support you?"
        value={leadershipFit}
        onChange={setLeadershipFit}
      />

      <ScaleSelector
        label="Self performance"
        description="How would you rate your own performance?"
        value={selfPerformance}
        onChange={setSelfPerformance}
      />

      <ScaleSelector
        label="Intent to stay *"
        description="How likely are you to stay on board? (1 = leaving soon, 10 = staying)"
        value={intentToStay}
        onChange={setIntentToStay}
      />

      {/* Exit interview extras */}
      {isExitInterview && (
        <View className="mb-5">
          <Text className="text-text-primary text-sm font-medium mb-2">
            Reason for leaving
          </Text>
          {DEPARTURE_REASONS.map(({ value, label }) => (
            <TouchableOpacity
              key={value}
              onPress={() => setDepartureReason(value)}
              className="flex-row items-center mb-2"
            >
              <View
                className="w-5 h-5 rounded-full mr-3 items-center justify-center"
                style={{
                  borderWidth: 2,
                  borderColor: departureReason === value ? "#4A90B8" : "#2A3142",
                  backgroundColor: departureReason === value ? "#4A90B8" : "transparent",
                }}
              >
                {departureReason === value && (
                  <View className="w-2 h-2 rounded-full bg-bg-primary" />
                )}
              </View>
              <Text className="text-text-primary text-sm">{label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Free text */}
      <View className="mb-6">
        <Text className="text-text-primary text-sm font-medium mb-1">
          Additional comments <Text className="text-muted">(optional)</Text>
        </Text>
        <TextInput
          className="bg-bg-elevated border border-bg-border rounded-xl px-3 py-2.5 text-text-primary text-sm"
          placeholder="Any additional feedback..."
          placeholderTextColor="#8FA3B8"
          value={freeText}
          onChangeText={setFreeText}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />
      </View>

      <TouchableOpacity
        onPress={handleSubmit}
        disabled={isSubmitting}
        className="bg-brand-primary rounded-xl py-4 items-center"
        style={{ opacity: isSubmitting ? 0.6 : 1 }}
      >
        {isSubmitting ? (
          <ActivityIndicator color="#07090F" />
        ) : (
          <Text className="text-bg-primary font-semibold text-base">Submit response</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        onPress={() => router.back()}
        className="py-3 items-center mt-2"
      >
        <Text className="text-muted text-sm">Cancel</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}
