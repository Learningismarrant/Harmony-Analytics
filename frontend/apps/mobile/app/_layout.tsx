import { useEffect } from "react";
import { Stack, useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { restoreSession } from "@/lib/auth";
import { useAuthStore } from "@/store/auth.store";

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

function AuthGuard() {
  const router = useRouter();
  const { isAuthenticated, isRestoringSession, setRestoringSession, setAuthenticated } =
    useAuthStore();

  useEffect(() => {
    restoreSession().then((ok) => {
      setAuthenticated(ok);
      setRestoringSession(false);
      if (!ok) {
        router.replace("/(auth)/login");
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="light" backgroundColor="#07090F" />
      <AuthGuard />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#07090F" },
          headerTintColor: "#E8EFF7",
          headerTitleStyle: { fontWeight: "600", fontSize: 16 },
          contentStyle: { backgroundColor: "#07090F" },
          animation: "slide_from_right",
        }}
      >
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(candidate)" options={{ headerShown: false }} />
      </Stack>
    </QueryClientProvider>
  );
}
