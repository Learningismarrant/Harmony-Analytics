import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface Props {
  name: string | null;
  catalogueName: string | null | undefined;
  testType: string | null | undefined;
  disclaimer: string;
}

function getContextualMessage(catalogueName: string | null | undefined, testType: string | null | undefined): string {
  const name = (catalogueName ?? "").toLowerCase();
  const type = (testType ?? "").toLowerCase();
  if (name.includes("hexaco") || name.includes("big five") || name.includes("hbf")) {
    return "Ton profil de personnalité contribue à calibrer notre détection de l'intégrité en milieu maritime.";
  }
  if (type.includes("qcm") || type.includes("raven") || name.includes("gca") || name.includes("hmr") || name.includes("icar")) {
    return "Tes réponses aident à étalonner notre mesure de l'aptitude cognitive.";
  }
  return "Ta participation contribue à rendre la sélection maritime plus équitable et scientifiquement rigoureuse.";
}

export function CalibThankYou({ name, catalogueName, testType, disclaimer }: Props) {
  const contextualMessage = getContextualMessage(catalogueName, testType);

  return (
    <View
      style={{
        backgroundColor: "#1A2C42",
        borderRadius: 16,
        borderWidth: 1,
        borderColor: "#1E3050",
        padding: 24,
        alignItems: "center",
        marginBottom: 20,
      }}
    >
      {/* Icône */}
      <View
        style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          backgroundColor: "#2E8A5C22",
          borderWidth: 2,
          borderColor: "#2E8A5C44",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 16,
        }}
      >
        <Ionicons name="checkmark-circle" size={36} color="#2E8A5C" />
      </View>

      {/* Titre */}
      <Text
        style={{
          color: "#F1F4F8",
          fontSize: 20,
          fontWeight: "900",
          letterSpacing: 0.5,
          marginBottom: 8,
          textAlign: "center",
        }}
      >
        Merci {name ? name.split(" ")[0] : ""} !
      </Text>

      {/* Message contextuel */}
      <Text
        style={{
          color: "#94A3B8",
          fontSize: 13,
          lineHeight: 20,
          textAlign: "center",
          marginBottom: 16,
        }}
      >
        {contextualMessage}
      </Text>

      {/* Disclaimer */}
      <Text
        style={{
          color: "#64748B",
          fontSize: 10,
          lineHeight: 15,
          textAlign: "center",
          fontStyle: "italic",
        }}
      >
        {disclaimer}
      </Text>
    </View>
  );
}
