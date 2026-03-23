import { useState } from "react";
import { View, Text, ActivityIndicator, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import { ConstellationMap } from "@/features/calibration/components/ConstellationMap";
import { DomainSheet } from "@/features/calibration/components/DomainSheet";
import type { CalibCatalogueOut, CatalogueDomain } from "@harmony/types";

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
      {/* Header */}
      <View style={{ padding: 16, paddingBottom: 0 }}>
        <Text className="text-ice text-lg font-bold mb-1">
          Votre constellation
        </Text>
        <Text className="text-muted text-xs leading-5">
          Explorez les dimensions de votre profil. Chaque étoile révèle une facette de qui vous êtes.
        </Text>
      </View>

      {/* Constellation centrée */}
      <View style={{ alignItems: "center", paddingVertical: 24 }}>
        <ConstellationMap
          catalogues={catalogues ?? []}
          sessions={sessions ?? []}
          onDomainPress={(domain) => setSelectedDomain(domain)}
        />
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
