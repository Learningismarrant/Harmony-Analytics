import { useState } from "react";
import { View, Text, ActivityIndicator, ScrollView, TouchableOpacity } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import {
  ConstellationMap,
  DOMAIN_SHORT_LABELS,
  DOMAIN_COLORS,
  DOMAIN_ICONS,
} from "@/features/calibration/components/ConstellationMap";
import { DomainSheet } from "@/features/calibration/components/DomainSheet";
import type { CalibCatalogueOut, CatalogueDomain } from "@harmony/types";

const DOMAINS_ORDERED: CatalogueDomain[] = [
  "cognitive", "personality", "motivation", "person_team",
  "physical", "person_org", "person_job",
];

export default function CataloguesScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [selectedDomain, setSelectedDomain] = useState<CatalogueDomain | null>(null);

  const { data: catalogues, isLoading: isLoadingCatalogues } = useQuery({
    queryKey: calibrationQueryKeys.catalogues(),
    queryFn: () => calibrationApi.getCatalogues(),
  });

  const { data: sessions, isLoading: isLoadingSessions } = useQuery({
    queryKey: calibrationQueryKeys.sessions(),
    queryFn: () => calibrationApi.getSessions(),
    refetchOnWindowFocus: true,
    staleTime: 0,
  });

  const startSessionMutation = useMutation({
    mutationFn: (catalogueId: number) => calibrationApi.startSession(catalogueId),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: calibrationQueryKeys.sessions() });
      router.push(
        `/(calibrator)/session/${session.id}?catalogueId=${session.catalogue_id}`,
      );
    },
  });

  const isLoading = isLoadingCatalogues || isLoadingSessions;

  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#94A3B8" size="large" />
      </View>
    );
  }

  function getSession(catalogueId: number) {
    return sessions?.find((s) => s.catalogue_id === catalogueId) ?? null;
  }

  function handlePress(catalogue: CalibCatalogueOut) {
    const session = getSession(catalogue.id);
    if (session !== null && session.completed_at !== null) {
      router.push(`/(calibrator)/session/result/${session.id}`);
      return;
    }
    if (session !== null && session.completed_at === null) {
      router.push(
        `/(calibrator)/session/${session.id}?catalogueId=${catalogue.id}`,
      );
      return;
    }
    startSessionMutation.mutate(catalogue.id);
  }

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ paddingBottom: 32 }}
    >
      {/* Header card */}
      <View style={{
        margin: 16,
        marginBottom: 0,
        backgroundColor: "#1A2C42",
        borderRadius: 16,
        borderWidth: 1,
        borderColor: "rgba(166,124,82,0.2)",
        padding: 16,
      }}>
        <Text style={{ color: "#F1F4F8", fontSize: 17, fontWeight: "800", marginBottom: 4 }}>
          Votre constellation
        </Text>
        <Text style={{ color: "#64748B", fontSize: 12, lineHeight: 18 }}>
          Explorez les dimensions de votre profil. Tapez une étoile pour découvrir les tests du domaine.
        </Text>
      </View>

      {/* Constellation centrée */}
      <View style={{ alignItems: "center", paddingVertical: 20 }}>
        <ConstellationMap
          catalogues={catalogues ?? []}
          sessions={sessions ?? []}
          onDomainPress={(domain) => setSelectedDomain(domain)}
        />
      </View>

      {/* Légende — 2 colonnes */}
      <View style={{ paddingHorizontal: 16, gap: 8 }}>
        {Array.from({ length: Math.ceil(DOMAINS_ORDERED.length / 2) }).map((_, rowIdx) => {
          const left = DOMAINS_ORDERED[rowIdx * 2];
          const right = DOMAINS_ORDERED[rowIdx * 2 + 1];
          return (
            <View key={rowIdx} style={{ flexDirection: "row", gap: 8 }}>
              {[left, right].map((domain) =>
                domain ? (
                  <TouchableOpacity
                    key={domain}
                    onPress={() => setSelectedDomain(domain)}
                    activeOpacity={0.7}
                    style={{
                      flex: 1,
                      flexDirection: "row",
                      alignItems: "center",
                      backgroundColor: "#1A2C42",
                      borderRadius: 10,
                      borderWidth: 1,
                      borderColor: "rgba(255,255,255,0.06)",
                      paddingVertical: 8,
                      paddingHorizontal: 10,
                      gap: 8,
                    }}
                  >
                    <View style={{
                      width: 28,
                      height: 28,
                      borderRadius: 14,
                      backgroundColor: `${DOMAIN_COLORS[domain]}22`,
                      borderWidth: 1,
                      borderColor: `${DOMAIN_COLORS[domain]}55`,
                      alignItems: "center",
                      justifyContent: "center",
                    }}>
                      <Ionicons name={DOMAIN_ICONS[domain]} size={13} color={DOMAIN_COLORS[domain]} />
                    </View>
                    <Text style={{ color: "#94A3B8", fontSize: 11, flex: 1, lineHeight: 15 }}>
                      {DOMAIN_SHORT_LABELS[domain]}
                    </Text>
                  </TouchableOpacity>
                ) : (
                  <View key="empty" style={{ flex: 1 }} />
                )
              )}
            </View>
          );
        })}
      </View>

      {/* Domain Sheet */}
      <DomainSheet
        domain={selectedDomain}
        catalogues={catalogues ?? []}
        sessions={sessions ?? []}
        onClose={() => setSelectedDomain(null)}
        onCataloguePress={handlePress}
      />
    </ScrollView>
  );
}
