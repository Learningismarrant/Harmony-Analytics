import { View, Text, FlatList, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import { SessionCard } from "@/features/calibration/components/SessionCard";

export default function SessionsScreen() {
  const router = useRouter();

  const { data: sessions, isLoading: isLoadingSessions } = useQuery({
    queryKey: calibrationQueryKeys.sessions(),
    queryFn: () => calibrationApi.getMySessions(),
  });

  const { data: catalogues, isLoading: isLoadingCatalogues } = useQuery({
    queryKey: calibrationQueryKeys.catalogues(),
    queryFn: () => calibrationApi.getCatalogues(),
  });

  const isLoading = isLoadingSessions || isLoadingCatalogues;

  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#94A3B8" size="large" />
      </View>
    );
  }

  function getCatalogueName(catalogueId: number): string {
    return catalogues?.find((c) => c.id === catalogueId)?.name ?? `Catalogue #${catalogueId}`;
  }

  return (
    <View className="flex-1 bg-bg-primary">
      <FlatList
        data={sessions ?? []}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        ListHeaderComponent={() => (
          <View className="mb-6">
            <Text className="text-ice text-lg font-bold mb-1">Historique</Text>
            <Text className="text-muted text-xs leading-5">
              Vos sessions de tests complétées et en cours.
            </Text>
          </View>
        )}
        ListEmptyComponent={() => (
          <View className="items-center py-12">
            <Text className="text-muted text-sm">Aucune session pour l'instant</Text>
            <Text className="text-muted text-xs mt-2">
              Démarrez un test depuis l'onglet Tests.
            </Text>
          </View>
        )}
        renderItem={({ item }) => (
          <SessionCard
            session={item}
            catalogueName={getCatalogueName(item.catalogue_id)}
            onViewResult={() =>
              router.push(`/(calibrator)/session/result/${item.id}`)
            }
          />
        )}
      />
    </View>
  );
}
