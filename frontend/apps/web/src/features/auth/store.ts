/**
 * Auth store — Zustand
 *
 * Access token: mémoire uniquement (jamais persisté).
 * Refresh token: sessionStorage (web) — perdu à la fermeture du navigateur.
 *   → Pas de HttpOnly cookie côté backend, le refresh_token est retourné dans le body JSON.
 */
import { create } from "zustand";
import { setAccessToken, clearAccessToken } from "@harmony/api";
import type { UserRole } from "@harmony/types";

const REFRESH_KEY = "harmony_rt";
const SESSION_COOKIE = "harmony_session";

function saveRefreshToken(token: string) {
  try { sessionStorage.setItem(REFRESH_KEY, token); } catch {}
}
function loadRefreshToken(): string | null {
  try { return sessionStorage.getItem(REFRESH_KEY); } catch { return null; }
}
function clearRefreshTokenStorage() {
  try { sessionStorage.removeItem(REFRESH_KEY); } catch {}
}

// Lightweight session flag readable by Next.js middleware (not HttpOnly).
function saveSessionCookie() {
  try {
    document.cookie = `${SESSION_COOKIE}=1; path=/; SameSite=Strict; max-age=86400`;
  } catch {}
}
function clearSessionCookie() {
  try {
    document.cookie = `${SESSION_COOKIE}=; path=/; SameSite=Strict; max-age=0`;
  } catch {}
}

export { loadRefreshToken };

interface AuthState {
  isAuthenticated: boolean;
  role: UserRole | null;
  userId: number | null;
  profileId: number | null;   // crew_profile.id ou employer_profile.id
  name: string | null;

  login: (params: {
    accessToken: string;
    refreshToken: string;
    role: UserRole;
    userId: number;
    profileId: number;
    name: string;
  }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  isAuthenticated: false,
  role: null,
  userId: null,
  profileId: null,
  name: null,

  login: ({ accessToken, refreshToken, role, userId, profileId, name }) => {
    setAccessToken(accessToken);
    saveRefreshToken(refreshToken);
    saveSessionCookie();
    set({ isAuthenticated: true, role, userId, profileId, name });
  },

  logout: () => {
    clearAccessToken();
    clearRefreshTokenStorage();
    clearSessionCookie();
    set({ isAuthenticated: false, role: null, userId: null, profileId: null, name: null });
  },
}));
