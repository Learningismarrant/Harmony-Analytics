import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

// TODO: Replace with real data from useQuery(queryKeys.identity.fullProfile(crewProfileId))
const MOCK_IDENTITY = {
  name: "James Whitfield",
  position: "First Mate",
  nationality: "British",
  location: "Monaco, France",
  experience_years: 8,
  email: "j.whitfield@harmony.crew",
  phone: "+44 7700 900461",
  availability: "available" as const,
  bio: "Experienced deck officer with 8 years aboard superyachts in the Med and Caribbean. STCW certified, strong leadership track record.",
  is_harmony_verified: true,
};

const AVAILABILITY_CONFIG = {
  available: { label: "Available", color: "#5A8279" },
  soon: { label: "Available soon", color: "#A68D6A" },
  on_board: { label: "On board", color: "#A67C52" },
  unavailable: { label: "Unavailable", color: "#9C6B6B" },
};

function InfoRow({
  icon,
  label,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
}) {
  return (
    <View className="flex-row items-center py-3 border-b border-bg-border">
      <View className="w-8 h-8 rounded-lg bg-bg-primary items-center justify-center mr-3">
        <Ionicons name={icon} size={16} color="#94A3B8" />
      </View>
      <View className="flex-1">
        <Text className="text-muted text-xs mb-0.5">{label}</Text>
        <Text className="text-text-primary text-sm font-medium">{value}</Text>
      </View>
    </View>
  );
}

export function IdentityCard() {
  // TODO: const { data: profile } = useQuery(...)
  const identity = MOCK_IDENTITY;
  const avail = AVAILABILITY_CONFIG[identity.availability];

  return (
    <View className="gap-y-4">
      {/* Avatar + name */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
        {/* Avatar */}
        <View
          className="w-20 h-20 rounded-full items-center justify-center mb-3"
          style={{ borderWidth: 2, borderColor: "#A67C52", backgroundColor: "#1A2C42" }}
        >
          <Text style={{ fontSize: 32, color: "#A67C52", fontWeight: "700" }}>
            {identity.name.charAt(0)}
          </Text>
        </View>

        {/* Name + verified badge */}
        <View className="flex-row items-center gap-x-2">
          <Text className="text-text-primary text-lg font-bold">{identity.name}</Text>
          {identity.is_harmony_verified && (
            <Ionicons name="checkmark-circle" size={18} color="#5A8279" />
          )}
        </View>

        {/* Position */}
        <View className="mt-1 px-3 py-1 rounded-full" style={{ backgroundColor: "#1E3050" }}>
          <Text className="text-muted text-xs tracking-widest uppercase">
            {identity.position}
          </Text>
        </View>

        {/* Availability */}
        <View
          className="mt-2 px-3 py-1 rounded-full flex-row items-center gap-x-1.5"
          style={{ backgroundColor: `${avail.color}22` }}
        >
          <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: avail.color }} />
          <Text style={{ color: avail.color, fontSize: 11, fontWeight: "600" }}>
            {avail.label}
          </Text>
        </View>

        {/* Bio */}
        {identity.bio && (
          <Text className="text-muted text-xs text-center mt-3 leading-5">{identity.bio}</Text>
        )}

        {/* Edit button — TODO: wire up */}
        <TouchableOpacity
          className="mt-4 flex-row items-center gap-x-1.5 px-4 py-2 rounded-xl"
          style={{ backgroundColor: "#A67C5233", borderWidth: 1, borderColor: "#A67C5255" }}
          onPress={() => {}} // TODO: open edit modal
        >
          <Ionicons name="pencil-outline" size={13} color="#A67C52" />
          <Text style={{ color: "#A67C52", fontSize: 12, fontWeight: "600" }}>Edit profile</Text>
        </TouchableOpacity>
      </View>

      {/* Info rows */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl px-4 py-1">
        <InfoRow icon="mail-outline" label="Email" value={identity.email} />
        <InfoRow icon="call-outline" label="Phone" value={identity.phone} />
        <InfoRow icon="location-outline" label="Location" value={identity.location} />
        <InfoRow icon="flag-outline" label="Nationality" value={identity.nationality} />
      </View>
    </View>
  );
}
