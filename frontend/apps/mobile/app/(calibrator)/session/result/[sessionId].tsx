import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { CalibThankYou } from "@/features/calibration/components/result/CalibThankYou";
import { CalibTraitBars } from "@/features/calibration/components/result/CalibTraitBars";
import { CalibRadarChart } from "@/features/calibration/components/result/CalibRadarChart";
import { CalibScoreRing } from "@/features/calibration/components/result/CalibScoreRing";

const DISCLAIMER =
  "Ces résultats sont indicatifs et servent uniquement à l'étalonnage de nos instruments psychométriques. Ils ne constituent pas un diagnostic psychologique.";

export default function CalibResultScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();
  const name = useAuthStore((s) => s.name);

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

  // Choisir la visualisation selon le nombre de traits
  function renderVisualization() {
    if (traits.length === 0) return null;

    if (traits.length === 1) {
      return (
        <View style={{ alignItems: "center", marginBottom: 20 }}>
          <CalibScoreRing trait={traits[0]} />
        </View>
      );
    }

    if (traits.length >= 3) {
      return (
        <View style={{ marginBottom: 20 }}>
          <Text
            style={{
              color: "#64748B",
              fontSize: 10,
              fontWeight: "800",
              letterSpacing: 1,
              textAlign: "center",
              marginBottom: 12,
            }}
          >
            PROFIL PAR TRAIT
          </Text>
          <CalibRadarChart traits={traits} />
        </View>
      );
    }

    // 2 traits : barres
    return (
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
          SCORES PAR TRAIT
        </Text>
        <CalibTraitBars traits={traits} />
      </View>
    );
  }

  return (
    <ScrollView
      className="flex-1 bg-bg-primary"
      contentContainerStyle={{ padding: 20, paddingBottom: 40 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Zone 1 : Remerciements */}
      <CalibThankYou
        name={name}
        catalogueName={score.catalogue_name}
        testType={score.test_type}
        disclaimer={DISCLAIMER}
      />

      {/* Zone 2 : Visualisation des scores */}
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
            VOS RÉSULTATS
          </Text>
          {renderVisualization()}

          {/* Toujours afficher les barres si >= 3 traits */}
          {traits.length >= 3 && (
            <View style={{ marginTop: 8 }}>
              <CalibTraitBars traits={traits} />
            </View>
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
