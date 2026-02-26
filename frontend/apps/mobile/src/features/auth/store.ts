import { create } from "zustand";
import { setAccessToken, clearAccessToken } from "@harmony/api";
import { saveRefreshToken, clearRefreshToken } from "./lib";
import type { UserRole } from "@harmony/types";

interface AuthState {
  isAuthenticated: boolean;
  isRestoringSession: boolean;
  role: UserRole | null;
  crewProfileId: number | null;
  name: string | null;

  login: (params: {
    accessToken: string;
    refreshToken?: string;
    role: UserRole;
    crewProfileId: number | null;
    name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  setRestoringSession: (v: boolean) => void;
  setAuthenticated: (v: boolean) => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  isAuthenticated: false,
  isRestoringSession: true, // true on first render — loading splash until session check
  role: null,
  crewProfileId: null,
  name: null,

  login: async ({ accessToken, refreshToken, role, crewProfileId, name }) => {
    setAccessToken(accessToken);
    if (refreshToken) {
      await saveRefreshToken(refreshToken);
    }
    set({ isAuthenticated: true, role, crewProfileId, name, isRestoringSession: false });
  },

  logout: async () => {
    clearAccessToken();
    await clearRefreshToken();
    set({
      isAuthenticated: false,
      role: null,
      crewProfileId: null,
      name: null,
      isRestoringSession: false,
    });
  },

  setRestoringSession: (v) => set({ isRestoringSession: v }),
  setAuthenticated: (v) => set({ isAuthenticated: v }),
}));
