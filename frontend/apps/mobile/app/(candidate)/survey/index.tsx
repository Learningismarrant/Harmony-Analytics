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
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { crewApi } from "@harmony/api";
import { useSurvey } from "@/features/survey/hooks/useSurvey";
import type { SurveyTriggerType } from "@harmony/types";

const TRIGGER_LABELS: Record<SurveyTriggerType, string> = {
  monthly_pulse: "Monthly Pulse",
  post_charter: "Post Charter",
  post_season: "Post Season",
  conflict_event: "Conflict Review",
  exit_interview: "Exit Interview",
};

function PulseButton({
  score,
  selected,
  onPress,
}: {
  score: number;
  selected: boolean;
  onPress: () => void;
}) {
  const colors = ["#EF4444", "#F97316", "#F59E0B", "#84CC16", "#22C55E"];
  const color = colors[score - 1];
  return (
    <TouchableOpacity
      onPress={onPress}
      className="w-12 h-12 rounded-full items-center justify-center"
      style={{
        backgroundColor: selected ? color : "#1A1F2B",
        borderWidth: 2,
        borderColor: selected ? color : "#2A3142",
      }}
    >
      <Text
        className="text-base font-bold"
        style={{ color: selected ? "#07090F" : "#8FA3B8" }}
      >
        {score}
      </Text>
    </TouchableOpacity>
  );
}

export default function SurveyScreen() {
  const router = useRouter();
  const { pendingSurveys, isLoading } = useSurvey();

  // Daily pulse state
  const [pulseScore, setPulseScore] = useState<number | null>(null);
  const [pulseComment, setPulseComment] = useState("");
  const [pulseSubmitted, setPulseSubmitted] = useState(false);

  // Complaint state
  const [complaintText, setComplaintText] = useState("");
  const [complaintSubmitted, setComplaintSubmitted] = useState(false);

  const pulseMutation = useMutation({
    mutationFn: () => crewApi.submitPulse({ score: pulseScore!, comment: pulseComment || undefined }),
    onSuccess: () => setPulseSubmitted(true),
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) {
        Alert.alert("Already submitted", "You have already submitted your pulse today.");
      } else if (status === 403) {
        Alert.alert("Not on board", "You must be assigned to a yacht to submit a pulse.");
      } else {
        Alert.alert("Error", "Could not submit pulse. Please try again.");
      }
    },
  });

  // Management surveys = non-monthly_pulse pending surveys
  const managementSurveys = pendingSurveys.filter(
    (s) => s.trigger_type !== "monthly_pulse",
  );

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
    >
      {/* ── Daily Pulse ── */}
      <View className="bg-bg-secondary border border-bg-border rounded-xl p-4 mb-4">
        <Text className="text-text-primary font-semibold text-base mb-1">Daily Pulse</Text>
        <Text className="text-muted text-xs mb-4">
          How are you feeling today? Rate your mood from 1 (very bad) to 5 (excellent).
        </Text>

        {pulseSubmitted ? (
          <View className="items-center py-3">
            <Text className="text-green-400 font-medium">Pulse submitted — thanks!</Text>
          </View>
        ) : (
          <>
            <View className="flex-row justify-between mb-4">
              {[1, 2, 3, 4, 5].map((s) => (
                <PulseButton
                  key={s}
                  score={s}
                  selected={pulseScore === s}
                  onPress={() => setPulseScore(s)}
                />
              ))}
            </View>

            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-3 py-2.5 text-text-primary text-sm mb-3"
              placeholder="Add a comment (optional)"
              placeholderTextColor="#8FA3B8"
              value={pulseComment}
              onChangeText={setPulseComment}
              multiline
              numberOfLines={2}
            />

            <TouchableOpacity
              onPress={() => {
                if (!pulseScore) {
                  Alert.alert("Select a score", "Please select a score from 1 to 5.");
                  return;
                }
                pulseMutation.mutate();
              }}
              disabled={pulseMutation.isPending}
              className="bg-brand-primary rounded-xl py-3 items-center"
              style={{ opacity: pulseMutation.isPending ? 0.6 : 1 }}
            >
              {pulseMutation.isPending ? (
                <ActivityIndicator color="#07090F" />
              ) : (
                <Text className="text-bg-primary font-semibold text-sm">Submit pulse</Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* ── Management Surveys ── */}
      <View className="mb-4">
        <Text className="text-text-primary font-semibold text-base mb-3">
          Management Surveys
        </Text>

        {isLoading ? (
          <View className="bg-bg-secondary border border-bg-border rounded-xl p-4 items-center">
            <ActivityIndicator color="#4A90B8" />
          </View>
        ) : managementSurveys.length === 0 ? (
          <View className="bg-bg-secondary border border-bg-border rounded-xl p-6 items-center">
            <Text className="text-muted text-sm">No pending surveys.</Text>
          </View>
        ) : (
          managementSurveys.map((survey) => (
            <TouchableOpacity
              key={survey.id}
              onPress={() => router.push(`/(candidate)/survey/${survey.id}`)}
              className="bg-bg-secondary border border-bg-border rounded-xl px-4 py-3 mb-2 flex-row items-center justify-between"
            >
              <View>
                <Text className="text-text-primary text-sm font-medium">
                  {TRIGGER_LABELS[survey.trigger_type] ?? survey.trigger_type}
                </Text>
                <Text className="text-muted text-xs mt-0.5">
                  {new Date(survey.created_at).toLocaleDateString()}
                </Text>
              </View>
              <Text className="text-brand-primary text-sm">Respond ›</Text>
            </TouchableOpacity>
          ))
        )}
      </View>

      {/* ── Complaint ── */}
      <View className="bg-bg-secondary border border-bg-border rounded-xl p-4">
        <Text className="text-text-primary font-semibold text-base mb-1">Send a complaint</Text>
        <Text className="text-muted text-xs mb-3">
          Report an issue or share feedback confidentially with the Harmony team.
        </Text>

        {complaintSubmitted ? (
          <View className="items-center py-3">
            <Text className="text-green-400 font-medium">Message sent — thank you.</Text>
          </View>
        ) : (
          <>
            <TextInput
              className="bg-bg-elevated border border-bg-border rounded-xl px-3 py-2.5 text-text-primary text-sm mb-3"
              placeholder="Describe your concern..."
              placeholderTextColor="#8FA3B8"
              value={complaintText}
              onChangeText={setComplaintText}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
            <TouchableOpacity
              onPress={() => {
                if (!complaintText.trim()) {
                  Alert.alert("Empty message", "Please write your complaint before sending.");
                  return;
                }
                // TODO: backend endpoint /crew/complaint
                setComplaintSubmitted(true);
                setComplaintText("");
              }}
              className="bg-bg-elevated border border-bg-border rounded-xl py-3 items-center"
            >
              <Text className="text-muted text-sm">Send complaint</Text>
            </TouchableOpacity>
          </>
        )}
      </View>
    </ScrollView>
  );
}
