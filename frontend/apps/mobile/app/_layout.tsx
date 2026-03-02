import "../global.css";
import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { restoreSession } from "@/features/auth/lib";
import { useAuthStore } from "@/features/auth/store";

// Note: expo-router gère SplashScreen.preventAutoHideAsync() / hideAsync()
// automatiquement — ne pas l'appeler manuellement ici pour éviter les conflits.

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: (count, err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 401 || status === 403 || status === 404) return false;
        return count < 2;
      },
    },
  },
});

export default function RootLayout() {
  const { setAuthenticated, setRestoringSession } = useAuthStore();

  useEffect(() => {
    // Timeout de sécurité : si SecureStore ou le réseau hang,
    // on force la navigation vers login après 4s
    const fallback = setTimeout(() => {
      setAuthenticated(false);
      setRestoringSession(false);
    }, 4000);

    restoreSession()
      .then((ok) => {
        setAuthenticated(ok);
        setRestoringSession(false);
      })
      .catch(() => {
        setAuthenticated(false);
        setRestoringSession(false);
      })
      .finally(() => clearTimeout(fallback));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" backgroundColor="#07090F" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#07090F" },
          headerTintColor: "#E8EFF7",
          headerTitleStyle: { fontWeight: "600", fontSize: 16 },
          contentStyle: { backgroundColor: "#07090F" },
          animation: "slide_from_right",
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(candidate)" options={{ headerShown: false }} />
      </Stack>
    </QueryClientProvider>
  );
}
