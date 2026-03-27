import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { calibrationApi, calibrationQueryKeys } from "@harmony/api";
import type { CalibTraitScoreOut } from "@harmony/types";

const MMFS_TRAITS = new Set(["disponibilite", "geographie", "contraintes_perso", "administratif"]);

const TRAIT_META: Record<string, { label: string; description: string }> = {
  // HEXACO Personality
  H: { label: "Honnêteté-Humilité", description: "Sincérité, équité et désintéressement dans les relations." },
  E: { label: "Émotivité", description: "Sensibilité émotionnelle, anxiété et attachement aux proches." },
  X: { label: "Extraversion", description: "Aisance sociale, énergie et enthousiasme dans les interactions." },
  A: { label: "Agréabilité", description: "Patience, tolérance et coopération dans les situations de tension." },
  C: { label: "Conscienciosité", description: "Organisation, diligence et discipline dans le travail." },
  O: { label: "Ouverture", description: "Curiosité intellectuelle, créativité et sensibilité esthétique." },
  // Cognitive
  GCA_Gf: { label: "Intelligence fluide (GCA)", description: "Capacité de raisonnement face à des problèmes nouveaux et non verbaux." },
  matrix_reasoning: { label: "Raisonnement matriciel", description: "Identification de patterns visuels et règles abstraites." },
  analogy: { label: "Raisonnement analogique", description: "Détection de relations logiques entre concepts." },
  induction: { label: "Induction", description: "Généralisation à partir de séries et patterns observés." },
  icar_lnsr: { label: "Raisonnement lettre-chiffre", description: "Flexibilité mentale et mémoire de travail sur séquences mixtes." },
  icar_vr: { label: "Raisonnement verbal", description: "Compréhension de relations logiques exprimées en langage." },
  // Motivation (SDT & R-MAWS)
  intrinsic: { label: "Motivation intrinsèque", description: "Engagement par intérêt et plaisir inhérents à l'activité." },
  identified: { label: "Régulation identifiée", description: "Motivation par adhésion personnelle aux valeurs du travail." },
  integrated: { label: "Régulation intégrée", description: "Motivation pleinement assimilée à l'identité professionnelle." },
  introjected: { label: "Régulation introjectée", description: "Motivation par pression interne (culpabilité, fierté)." },
  extrinsic_material: { label: "Motivation extrinsèque (matérielle)", description: "Engagement principalement lié à la rémunération et avantages." },
  extrinsic_social: { label: "Motivation extrinsèque (sociale)", description: "Engagement pour la reconnaissance et l'approbation d'autrui." },
  external: { label: "Régulation externe", description: "Motivation par contraintes et récompenses extérieures." },
  amotivation: { label: "Amotivation", description: "Absence de motivation ou sentiment d'impuissance face à la tâche." },
  // Person-Team (LMX & Management)
  lmx_affect: { label: "LMX — Affect", description: "Appréciation mutuelle et lien positif avec la hiérarchie." },
  lmx_respect: { label: "LMX — Respect", description: "Reconnaissance professionnelle réciproque avec le manager." },
  lmx_mutual_understanding: { label: "LMX — Compréhension mutuelle", description: "Clarté des attentes et connaissance du rôle de chacun." },
  autonomy: { label: "Préférence d'autonomie", description: "Appétence pour l'indépendance et la prise de décision propre." },
  feedback: { label: "Besoin de feedback", description: "Importance accordée au retour régulier sur la performance." },
  structure: { label: "Besoin de structure", description: "Préférence pour des règles, procédures et cadres clairs." },
  // Person-Org (CES Values)
  achievement: { label: "Valeur d'accomplissement", description: "Importance accordée au dépassement de soi et à l'excellence." },
  fairness: { label: "Valeur d'équité", description: "Attachement à la justice et à l'égalité de traitement." },
  helping: { label: "Valeur d'aide", description: "Sens du service et importance du soutien aux autres." },
  honesty: { label: "Valeur d'honnêteté", description: "Importance de la transparence et de l'intégrité dans le travail." },
  // Physical — GSE
  gse: { label: "Auto-efficacité générale", description: "Confiance en sa capacité à faire face aux défis et obstacles." },
  // Physical — Tolérance ICE
  climat: { label: "Tolérance climatique", description: "Confort dans des environnements froids, chauds ou instables." },
  confinement: { label: "Tolérance au confinement", description: "Capacité à travailler dans des espaces restreints sur la durée." },
  houle: { label: "Tolérance à la houle", description: "Adaptation aux mouvements du navire et instabilité du plancher." },
  isolement: { label: "Tolérance à l'isolement", description: "Résistance psychologique aux périodes d'éloignement prolongé." },
  mal_de_mer: { label: "Résistance au mal de mer", description: "Sensibilité aux nausées et désorientation liées au mouvement marin." },
  sommeil: { label: "Qualité du sommeil en mer", description: "Capacité à récupérer dans un environnement de travail par quarts." },
};

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
            const isMmfs = MMFS_TRAITS.has(trait.name);
            const meta = TRAIT_META[trait.name];
            const displayLabel = meta?.label ?? trait.name;
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
