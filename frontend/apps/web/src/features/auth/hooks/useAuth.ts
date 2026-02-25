import { useAuthStore } from "../store";

/** Convenience hook — exposes auth state and actions from the Zustand store. */
export function useAuth() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const role            = useAuthStore((s) => s.role);
  const userId          = useAuthStore((s) => s.userId);
  const profileId       = useAuthStore((s) => s.profileId);
  const name            = useAuthStore((s) => s.name);
  const login           = useAuthStore((s) => s.login);
  const logout          = useAuthStore((s) => s.logout);

  return { isAuthenticated, role, userId, profileId, name, login, logout };
}
