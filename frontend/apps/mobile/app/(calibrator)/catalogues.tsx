import { useState } from "react";
import { View, Text, ActivityIndicator, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import {
  ConstellationMap,
} from "@/features/calibration/components/ConstellationMap";
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
    if (startSessionMutation.isPending) return;
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
          Votre Radiant
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

      {/* Carte d'instruction */}
      <View style={{
        marginHorizontal: 16,
        backgroundColor: "#1A2C42",
        borderRadius: 16,
        borderWidth: 1,
        borderColor: "rgba(166,124,82,0.2)",
        padding: 16,
      }}>
        <Text style={{ color: "#F1F4F8", fontSize: 16, fontWeight: "800" }}>
          Votre rôle dans Radiant Analytics
        </Text>
        <Text style={{ color: "#94A3B8", fontSize: 12, lineHeight: 18, marginTop: 8 }}>
          Chaque test que vous passez contribue à construire les normes de nos instruments psychométriques. Vos réponses, combinées à celles de l'ensemble de la cohorte, permettent d'étalonner les outils utilisés lors des évaluations de candidats.
        </Text>
        <Text style={{ color: "#A67C52", fontSize: 11, marginTop: 10, fontWeight: "600" }}>
          Tapez une étoile pour découvrir les tests disponibles dans chaque domaine.
        </Text>
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
