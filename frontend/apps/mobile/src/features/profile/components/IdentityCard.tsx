import { View, Text, ActivityIndicator } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { identityApi, queryKeys } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import type { AvailabilityStatus } from "@harmony/types";

const AVAILABILITY_CONFIG: Record<AvailabilityStatus, { label: string; color: string }> = {
  available:   { label: "Available",       color: "#5A8279" },
  soon:        { label: "Available soon",  color: "#A68D6A" },
  on_board:    { label: "On board",        color: "#A67C52" },
  unavailable: { label: "Unavailable",     color: "#9C6B6B" },
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
  const crewProfileId = useAuthStore((s) => s.crewProfileId);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.identity.fullProfile(crewProfileId!),
    queryFn: () => identityApi.getFullProfile(crewProfileId!),
    enabled: !!crewProfileId,
  });

  if (isLoading) {
    return (
      <View className="py-16 items-center">
        <ActivityIndicator size="large" color="#A67C52" />
      </View>
    );
  }

  if (isError || !data) {
    return (
      <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
        <Ionicons name="alert-circle-outline" size={32} color="#883838" />
        <Text className="text-muted text-sm text-center mt-3">
          Unable to load your profile.
        </Text>
      </View>
    );
  }

  const { identity } = data;
  const initials = identity.name.trim().split(/\s+/).map((p) => p[0]).join("").substring(0, 2).toUpperCase();
  const avail = (identity.availability_status && AVAILABILITY_CONFIG[identity.availability_status as AvailabilityStatus]) ?? AVAILABILITY_CONFIG.unavailable;

  return (
    <View className="gap-y-4">
      {/* Avatar + name */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl p-5 items-center">
        <View
          className="w-20 h-20 rounded-full items-center justify-center mb-3"
          style={{ borderWidth: 2, borderColor: "#A67C52", backgroundColor: "#1A2C42" }}
        >
          <Text style={{ fontSize: 32, color: "#A67C52", fontWeight: "700" }}>
            {initials}
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
            {identity.position_targeted}
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
      </View>

      {/* Info rows */}
      <View className="bg-bg-secondary border border-bg-border rounded-2xl px-4 py-1">
        <InfoRow icon="mail-outline"     label="Email"    value={identity.email} />
        {identity.phone    && <InfoRow icon="call-outline"     label="Phone"    value={identity.phone} />}
        {identity.location && <InfoRow icon="location-outline" label="Location" value={identity.location} />}
        <InfoRow
          icon="time-outline"
          label="Experience"
          value={`${identity.experience_years} year${identity.experience_years !== 1 ? "s" : ""} at sea`}
        />
      </View>
    </View>
  );
}
