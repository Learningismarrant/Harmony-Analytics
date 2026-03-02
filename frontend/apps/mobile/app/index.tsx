import { View, ActivityIndicator } from "react-native";
import { Redirect } from "expo-router";
import { useAuthStore } from "@/features/auth/store";

/**
 * Route racine `/` — décide où rediriger selon l'état de session.
 * Affiche un spinner pendant la restauration (expo-router masque
 * le splash automatiquement dès que ce composant est rendu).
 */
export default function Index() {
  const { isAuthenticated, isRestoringSession } = useAuthStore();

  if (isRestoringSession) {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: "#07090F",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <ActivityIndicator size="large" color="#4A90B8" />
      </View>
    );
  }

  if (isAuthenticated) return <Redirect href="/(candidate)/profile" />;

  return <Redirect href="/(auth)/login" />;
}
