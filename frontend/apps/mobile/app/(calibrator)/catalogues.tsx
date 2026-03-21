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
    queryFn: () => calibrationApi.getMySessions(),
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
    if (session?.status === "completed") {
      router.push(`/(calibrator)/session/result/${session.id}`);
      return;
    }
    if (session?.status === "in_progress") {
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
