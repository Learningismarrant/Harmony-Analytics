import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Alert,
} from "react-native";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { identityApi, queryKeys } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";

type Section = "info" | "experience" | "documents";

function SectionTab({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      className="flex-1 py-2.5 items-center"
      style={{
        borderBottomWidth: 2,
        borderBottomColor: active ? "#4A90B8" : "transparent",
      }}
    >
      <Text
        className="text-sm font-medium"
        style={{ color: active ? "#4A90B8" : "#8FA3B8" }}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <View className="flex-row justify-between py-3 border-b border-bg-border">
      <Text className="text-muted text-sm">{label}</Text>
      <Text className="text-text-primary text-sm font-medium flex-shrink ml-4 text-right">{value}</Text>
    </View>
  );
}

const AVAILABILITY_LABELS: Record<string, string> = {
  available: "Available",
  on_board: "On board",
  unavailable: "Unavailable",
  soon: "Available soon",
};

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  passport: "Passport",
  stcw: "STCW Certificate",
  medical: "Medical Certificate",
  cv: "CV",
  other: "Document",
};

export default function ProfileScreen() {
  const { crewProfileId, logout } = useAuthStore();
  const [section, setSection] = useState<Section>("info");

  const { data: profile, isLoading } = useQuery({
    queryKey: queryKeys.identity.fullProfile(crewProfileId ?? 0),
    queryFn: () => identityApi.getFullProfile(crewProfileId!),
    enabled: crewProfileId !== null,
  });

  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <Text className="text-muted">Loading profile...</Text>
      </View>
    );
  }

  const identity = profile?.identity;
  const crew = profile?.crew;
  const experiences = profile?.experiences ?? [];
  const documents = profile?.documents ?? [];

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ paddingBottom: 32 }}
    >
      {/* Avatar + name */}
      <View className="items-center pt-6 pb-5 px-4">
        <View className="w-20 h-20 rounded-full bg-brand-primary/20 border-2 border-brand-primary/40 items-center justify-center mb-3">
          <Text className="text-brand-primary text-3xl font-bold">
            {identity?.name?.charAt(0) ?? "?"}
          </Text>
        </View>
        <Text className="text-text-primary text-xl font-semibold">{identity?.name}</Text>
        <Text className="text-muted text-sm mt-0.5">{crew?.position_targeted}</Text>
        {identity?.is_harmony_verified && (
          <View className="mt-1.5">
            <Text className="text-brand-primary text-xs">&#10003; Harmony Verified</Text>
          </View>
        )}
      </View>

      {/* Section tabs */}
      <View
        className="flex-row mx-4 mb-4 bg-bg-secondary rounded-xl"
        style={{ borderWidth: 1, borderColor: "#2A3142" }}
      >
        <SectionTab label="Info" active={section === "info"} onPress={() => setSection("info")} />
        <SectionTab label="Experience" active={section === "experience"} onPress={() => setSection("experience")} />
        <SectionTab label="Documents" active={section === "documents"} onPress={() => setSection("documents")} />
      </View>

      <View className="px-4">
        {/* Info section */}
        {section === "info" && (
          <View className="bg-bg-secondary border border-bg-border rounded-xl px-4 mb-4">
            <InfoRow label="Email" value={identity?.email} />
            <InfoRow label="Phone" value={identity?.phone} />
            <InfoRow label="Location" value={identity?.location} />
            <InfoRow label="Position" value={crew?.position_targeted} />
            <InfoRow
              label="Experience"
              value={
                crew?.experience_years !== undefined
                  ? `${crew.experience_years} year${crew.experience_years !== 1 ? "s" : ""}`
                  : null
              }
            />
            <InfoRow
              label="Availability"
              value={
                crew?.availability_status
                  ? (AVAILABILITY_LABELS[crew.availability_status] ?? crew.availability_status)
                  : null
              }
            />
          </View>
        )}

        {/* Experience section */}
        {section === "experience" && (
          <View>
            {experiences.length === 0 ? (
              <View className="bg-bg-secondary border border-bg-border rounded-xl p-6 items-center">
                <Text className="text-muted text-sm">No experience added yet.</Text>
              </View>
            ) : (
              <View className="bg-bg-secondary border border-bg-border rounded-xl p-4">
                {experiences.map((exp, i) => (
                  <View
                    key={exp.id}
                    className="border-l-2 border-brand-primary/30 pl-3"
                    style={{ marginBottom: i < experiences.length - 1 ? 16 : 0 }}
                  >
                    <Text className="text-text-primary text-sm font-medium">
                      {exp.role} — {exp.yacht_name}
                    </Text>
                    <Text className="text-muted text-xs mt-0.5">
                      {new Date(exp.start_date).getFullYear()}
                      {exp.end_date
                        ? ` - ${new Date(exp.end_date).getFullYear()}`
                        : " - present"}
                    </Text>
                    {exp.candidate_comment ? (
                      <Text className="text-muted text-xs mt-1 italic">
                        {exp.candidate_comment}
                      </Text>
                    ) : null}
                    {exp.is_harmony_approved && (
                      <Text className="text-brand-primary text-xs mt-0.5">&#10003; Verified</Text>
                    )}
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Documents section */}
        {section === "documents" && (
          <View>
            {documents.length === 0 ? (
              <View className="bg-bg-secondary border border-bg-border rounded-xl p-6 items-center">
                <Text className="text-muted text-sm text-center">
                  No documents uploaded yet.
                </Text>
                <Text className="text-muted text-xs mt-1 text-center">Document management coming soon.</Text>
              </View>
            ) : (
              <View className="bg-bg-secondary border border-bg-border rounded-xl overflow-hidden">
                {documents.map((doc, i) => (
                  <View
                    key={doc.id}
                    className="flex-row items-center px-4 py-3"
                    style={{
                      borderBottomWidth: i < documents.length - 1 ? 1 : 0,
                      borderBottomColor: "#2A3142",
                    }}
                  >
                    <View className="w-9 h-9 rounded-lg bg-brand-primary/10 items-center justify-center mr-3">
                      <Text className="text-brand-primary text-base">&#128196;</Text>
                    </View>
                    <View className="flex-1">
                      <Text className="text-text-primary text-sm font-medium">{doc.title}</Text>
                      <Text className="text-muted text-xs mt-0.5">
                        {DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}
                        {" - "}
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            )}
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
          className="border border-bg-border rounded-xl py-3 items-center mt-4"
        >
          <Text className="text-muted text-sm">Sign out</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
