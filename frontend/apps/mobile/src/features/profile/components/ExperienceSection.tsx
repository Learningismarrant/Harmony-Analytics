import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

// TODO: Replace with real experience data from API
// Shape: ExperienceOut[] from backend GET /identity/full-profile
const MOCK_EXPERIENCES = [
  {
    id: 1,
    role: "First Mate",
    yacht_name: "M/Y Aurora",
    yacht_length: 52,
    start_date: "2022-04-01",
    end_date: null,
    location: "Mediterranean",
    candidate_comment: "Managing deck operations and leading a crew of 6 across the summer season.",
    is_harmony_approved: true,
  },
  {
    id: 2,
    role: "Bosun",
    yacht_name: "S/Y Pelerin",
    yacht_length: 38,
    start_date: "2019-06-01",
    end_date: "2022-03-15",
    location: "Caribbean",
    candidate_comment: "Full maintenance responsibility, water sports program management.",
    is_harmony_approved: true,
  },
  {
    id: 3,
    role: "Deckhand",
    yacht_name: "M/Y Solstice",
    yacht_length: 30,
    start_date: "2017-05-01",
    end_date: "2019-05-30",
    location: "Mediterranean",
    candidate_comment: null,
    is_harmony_approved: false,
  },
];

function formatPeriod(start: string, end: string | null): string {
  const startYear = new Date(start).getFullYear();
  const endLabel = end ? new Date(end).getFullYear().toString() : "Present";
  return `${startYear} — ${endLabel}`;
}

function ExperienceCard({
  exp,
  isLast,
}: {
  exp: (typeof MOCK_EXPERIENCES)[number];
  isLast: boolean;
}) {
  return (
    <View className="flex-row">
      {/* Timeline column */}
      <View className="items-center mr-4" style={{ width: 24 }}>
        <View
          className="w-5 h-5 rounded-full items-center justify-center"
          style={{ backgroundColor: exp.is_harmony_approved ? "#5A827922" : "#1E3050", borderWidth: 1.5, borderColor: exp.is_harmony_approved ? "#5A8279" : "#1E3050" }}
        >
          {exp.is_harmony_approved && (
            <Ionicons name="checkmark" size={11} color="#5A8279" />
          )}
        </View>
        {!isLast && (
          <View className="flex-1 w-px bg-bg-border" style={{ marginTop: 4, minHeight: 24 }} />
        )}
      </View>

      {/* Content */}
      <View className="flex-1 pb-5">
        <View className="flex-row items-start justify-between">
          <View className="flex-1">
            <Text className="text-text-primary text-sm font-semibold">{exp.role}</Text>
            <Text className="text-muted text-xs mt-0.5">
              {exp.yacht_name} · {exp.yacht_length}m
            </Text>
          </View>
          {exp.is_harmony_approved && (
            <View
              className="px-2 py-0.5 rounded-full ml-2"
              style={{ backgroundColor: "#5A827933" }}
            >
              <Text style={{ color: "#5A8279", fontSize: 10, fontWeight: "700", letterSpacing: 1 }}>
                VERIFIED
              </Text>
            </View>
          )}
        </View>

        <View className="flex-row items-center mt-1.5 gap-x-3">
          <View className="flex-row items-center gap-x-1">
            <Ionicons name="calendar-outline" size={11} color="#94A3B8" />
            <Text className="text-muted text-xs">{formatPeriod(exp.start_date, exp.end_date)}</Text>
          </View>
          <View className="flex-row items-center gap-x-1">
            <Ionicons name="location-outline" size={11} color="#94A3B8" />
            <Text className="text-muted text-xs">{exp.location}</Text>
          </View>
        </View>

        {exp.candidate_comment && (
          <Text className="text-muted text-xs mt-2 leading-4 italic">
            "{exp.candidate_comment}"
          </Text>
        )}
      </View>
    </View>
  );
}

export function ExperienceSection() {
  // TODO: const { data: profile } = useQuery(queryKeys.identity.fullProfile(crewProfileId))
  // TODO: const experiences = profile?.experiences ?? []
  const experiences = MOCK_EXPERIENCES;

  return (
    <View className="gap-y-4">
      {/* Header */}
      <View className="flex-row items-center justify-between">
        <Text className="text-muted text-xs tracking-widest uppercase">
          {experiences.length} position{experiences.length !== 1 ? "s" : ""}
        </Text>
        <TouchableOpacity
          className="flex-row items-center gap-x-1.5 px-3 py-1.5 rounded-lg"
          style={{ backgroundColor: "#A67C5233", borderWidth: 1, borderColor: "#A67C5255" }}
          onPress={() => {}} // TODO: open ExperienceFormModal
        >
          <Ionicons name="add" size={14} color="#A67C52" />
          <Text style={{ color: "#A67C52", fontSize: 12, fontWeight: "600" }}>Add</Text>
        </TouchableOpacity>
      </View>

      {/* Timeline */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5">
        {experiences.length === 0 ? (
          <View className="items-center py-6">
            <Ionicons name="boat-outline" size={32} color="#718096" />
            <Text className="text-muted text-sm mt-3">No experience added yet.</Text>
            <Text className="text-slate text-xs mt-1">Add your first yachting position.</Text>
          </View>
        ) : (
          experiences.map((exp, i) => (
            <ExperienceCard key={exp.id} exp={exp} isLast={i === experiences.length - 1} />
          ))
        )}
      </View>

      {/* Info note */}
      <View className="flex-row items-start gap-x-2 px-1">
        <Ionicons name="information-circle-outline" size={14} color="#718096" style={{ marginTop: 1 }} />
        <Text className="text-muted text-xs leading-4 flex-1">
          Experiences are verified by Harmony from employer references. Unverified entries are shown grayed.
        </Text>
      </View>
    </View>
  );
}
