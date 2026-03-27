import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibTraitScoreOut } from "@harmony/types";
import { TRAIT_META, MMFS_TRAITS } from "@harmony/types";

export default function CalibResultScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();

  const { data: score, isLoading } = useQuery({
    queryKey: calibrationQueryKeys.sessionScore(Number(sessionId)),
    queryFn: () => calibrationApi.getSessionScore(Number(sessionId)),
  });

  if (isLoading) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center">
        <ActivityIndicator color="#94A3B8" size="large" />
        <Text className="text-muted text-sm mt-4">Chargement des résultats...</Text>
      </View>
    );
  }

  if (!score) {
    return (
      <View className="flex-1 bg-bg-primary items-center justify-center p-6">
        <Text className="text-muted text-sm text-center">
          Résultats non disponibles. La session est peut-être encore en cours de traitement.
        </Text>
        <TouchableOpacity
          onPress={() => router.replace("/(calibrator)/catalogues" as never)}
          style={{ marginTop: 20, paddingHorizontal: 20, paddingVertical: 12 }}
        >
          <Text style={{ color: "#A67C52", fontSize: 13, fontWeight: "700" }}>
            Retour aux catalogues
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  const traits = score.traits ?? [];

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 20, paddingBottom: 40 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Zone 1 : Confirmation header */}
      <View
        style={{
          backgroundColor: "#1A2C42",
          borderRadius: 12,
          borderWidth: 1,
          borderColor: "#1E3050",
          padding: 24,
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <Ionicons name="checkmark-circle" size={48} color="#2E8A5C" />
        <Text
          style={{
            color: "#F1F4F8",
            fontSize: 20,
            fontWeight: "800",
            textAlign: "center",
            marginTop: 12,
          }}
        >
          Contribution enregistrée !
        </Text>
        <Text
          style={{
            color: "#94A3B8",
            fontSize: 14,
            textAlign: "center",
            marginTop: 6,
          }}
        >
          {score.catalogue_name}
        </Text>
        <Text
          style={{
            color: "#64748B",
            fontSize: 12,
            fontStyle: "italic",
            textAlign: "center",
            marginTop: 8,
          }}
        >
          Vos réponses contribuent à l'étalonnage de cet instrument. Ces données ne constituent
          pas une évaluation personnelle.
        </Text>
      </View>

      {/* Zone 2 : Raw trait scores (neutral presentation) */}
      {traits.length > 0 && (
        <View
          style={{
            backgroundColor: "#1A2C42",
            borderRadius: 12,
            borderWidth: 1,
            borderColor: "#1E3050",
            padding: 20,
            marginBottom: 20,
          }}
        >
          <Text
            style={{
              color: "#64748B",
              fontSize: 10,
              fontWeight: "800",
              letterSpacing: 1,
              marginBottom: 16,
            }}
          >
            RÉPONSES ENREGISTRÉES
          </Text>
          {traits.map((trait: CalibTraitScoreOut, index: number) => {
            const isMmfs = MMFS_TRAITS.has(trait.trait);
            const meta = TRAIT_META[trait.trait];
            const displayLabel = meta?.label ?? trait.trait;
            return (
              <View
                key={trait.trait}
                style={{
                  flexDirection: "row",
                  justifyContent: "space-between",
                  alignItems: "center",
                  paddingVertical: 10,
                  borderTopWidth: index === 0 ? 0 : 1,
                  borderTopColor: "#1E3050",
                }}
              >
                {isMmfs ? (
                  <Text style={{ color: "#CBD5E1", fontSize: 13, fontWeight: "600", flex: 1, marginRight: 8 }}>
                    {displayLabel}
                  </Text>
                ) : (
                  <View style={{ flex: 1, marginRight: 8 }}>
                    <Text style={{ color: "#CBD5E1", fontSize: 13, fontWeight: "600" }}>
                      {displayLabel}
                    </Text>
                    {meta?.description ? (
                      <Text style={{ color: "#64748B", fontSize: 11, lineHeight: 16, marginTop: 2 }}>
                        {meta.description}
                      </Text>
                    ) : null}
                  </View>
                )}
                <Text style={{ color: "#94A3B8", fontSize: 13 }}>
                  {isMmfs ? "—" : trait.score.toFixed(1)}
                </Text>
              </View>
            );
          })}
          {traits.some((t: CalibTraitScoreOut) => MMFS_TRAITS.has(t.name)) && (
            <Text
              style={{
                color: "#64748B",
                fontSize: 11,
                fontStyle: "italic",
                marginTop: 12,
              }}
            >
              Les scores de mobilité sont utilisés uniquement pour les calculs du modèle.
            </Text>
          )}
        </View>
      )}

      {/* Zone 3 : CTA retour */}
      <TouchableOpacity
        onPress={() => router.replace("/(calibrator)/catalogues" as never)}
        style={{
          borderWidth: 1,
          borderColor: "#A67C5244",
          borderRadius: 12,
          paddingVertical: 16,
          alignItems: "center",
          backgroundColor: "#A67C5211",
        }}
        activeOpacity={0.75}
      >
        <Text style={{ color: "#A67C52", fontSize: 13, fontWeight: "800", letterSpacing: 0.5 }}>
          VOIR LES AUTRES CATALOGUES
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}
