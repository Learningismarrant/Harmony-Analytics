"use client";

import { ReactNode, useEffect, useState } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { setRefreshTokenProvider, setAccessToken, authApi } from "@harmony/api";
import { makeQueryClient } from "./query-client";

const REFRESH_KEY = "harmony_rt";
const SESSION_COOKIE = "harmony_session";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  // useState ensures the client is stable across renders (no recreation on HMR)
  const [queryClient] = useState(() => makeQueryClient());
  // Only used to gate devtools (client-only component — never affects SSR)
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    // 1. Register the refresh token provider synchronously so the 401 interceptor
    //    can use it for any requests that fire before restoration completes.
    setRefreshTokenProvider(() => sessionStorage.getItem(REFRESH_KEY));

    // 2. Proactively restore the access token. Without this, on page reload
    //    every query fires with no access token, each 401s, and the interceptor
    //    has to refresh them sequentially — creating a blank flash before data loads.
    const rt = sessionStorage.getItem(REFRESH_KEY);
    if (rt) {
      authApi
        .refresh(rt)
        .then(({ access_token }) => {
          setAccessToken(access_token);
        })
        .catch(() => {
          // Refresh token expired — clear session so middleware redirects on next nav.
          try {
            sessionStorage.removeItem(REFRESH_KEY);
            document.cookie = `${SESSION_COOKIE}=; path=/; SameSite=Strict; max-age=0`;
          } catch {}
        });
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {/*
       * Always render children — gating on client state here blocks SSR and
       * produces an empty HTML shell, causing a white screen on first load.
       * Session restoration happens asynchronously in the background; the 401
       * interceptor handles any queries that fire before it completes.
       */}
      {children}
      {/*
       * ReactQueryDevtools is lazy-loaded (never in SSR HTML).
       * It renders browser-only portals; including it in SSR output produces
       * markup the client cannot reconcile → React hydration error → blank screen.
       */}
      {mounted && process.env.NODE_ENV === "development" && <DevtoolsLazy />}
    </QueryClientProvider>
  );
}

// Lazy devtools component — dynamic import keeps it out of the initial bundle.
function DevtoolsLazy() {
  const [Devtools, setDevtools] =
    useState<React.ComponentType<{ initialIsOpen: boolean }> | null>(null);

  useEffect(() => {
    import("@tanstack/react-query-devtools").then((m) => {
      setDevtools(() => m.ReactQueryDevtools as React.ComponentType<{ initialIsOpen: boolean }>);
    });
  }, []);

  if (!Devtools) return null;
  return <Devtools initialIsOpen={false} />;
}
