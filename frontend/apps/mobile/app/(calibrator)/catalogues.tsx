import { View, Text, FlatList, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import { CatalogueCard } from "@/features/calibration/components/CatalogueCard";
import type { CalibCatalogueOut } from "@harmony/types";

export default function CataloguesScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

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

  const completedCount = (sessions ?? []).filter((s) => s.completed_at !== null).length;
  const totalCount = (catalogues ?? []).length;
  const progressPct = totalCount > 0 ? completedCount / totalCount : 0;

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
    <View className="flex-1 bg-bg-primary">
      <FlatList
        data={catalogues ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        ListHeaderComponent={() => (
          <View className="mb-6">
            <Text className="text-ice text-lg font-bold mb-1">
              Catalogue de tests
            </Text>
            <Text className="text-muted text-xs leading-5">
              Participez aux études d'étalonnage en complétant les tests ci-dessous.
            </Text>

            {/* Barre de progression globale */}
            {totalCount > 0 && (
              <View style={{ marginTop: 16 }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 6 }}>
                  <Text style={{ color: "#64748B", fontSize: 10, fontWeight: "700", letterSpacing: 0.5 }}>
                    PROGRESSION
                  </Text>
                  <Text style={{ color: "#94A3B8", fontSize: 10, fontWeight: "700" }}>
                    {completedCount} / {totalCount}
                  </Text>
                </View>
                <View style={{ height: 5, backgroundColor: "#1A2C42", borderRadius: 3, overflow: "hidden" }}>
                  <View
                    style={{
                      height: 5,
                      borderRadius: 3,
                      backgroundColor: completedCount === totalCount ? "#2E8A5C" : "#A67C52",
                      width: `${progressPct * 100}%`,
                    }}
                  />
                </View>
              </View>
            )}
          </View>
        )}
        ListEmptyComponent={() => (
          <View className="items-center py-12">
            <Text className="text-muted text-sm">Aucun test disponible</Text>
          </View>
        )}
        renderItem={({ item }) => (
          <CatalogueCard
            catalogue={item}
            session={getSession(item.id)}
            onPress={() => handlePress(item)}
          />
        )}
      />
    </View>
  );
}
