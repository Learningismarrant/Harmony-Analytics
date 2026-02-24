/**
 * Mobile auth helpers — expo-secure-store
 *
 * Security model:
 *   - Refresh token: stored in SecureStore (encrypted on device)
 *   - Access token: stored in Zustand memory only
 *   - On app restart: load refresh token → hit /auth/refresh → restore session
 */
import * as SecureStore from "expo-secure-store";
import {
  setAccessToken,
  clearAccessToken,
  setRefreshTokenProvider,
  authApi,
} from "@harmony/api";

const REFRESH_TOKEN_KEY = "harmony_refresh_token";

export async function saveRefreshToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, token, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED,
  });
}

/**
 * Register SecureStore as the refresh-token provider for the API client.
 * Call once at app startup (before any authenticated requests).
 */
export function initRefreshTokenProvider(): void {
  setRefreshTokenProvider(() => SecureStore.getItemAsync(REFRESH_TOKEN_KEY));
}

export async function loadRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearRefreshToken(): Promise<void> {
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
}

/**
 * On app start: attempt to restore session from saved refresh token.
 * Returns true if session was restored, false if login is required.
 */
export async function restoreSession(): Promise<boolean> {
  try {
    const stored = await loadRefreshToken();
    if (!stored) return false;

    const { access_token } = await authApi.refresh(stored);
    setAccessToken(access_token);
    return true;
  } catch {
    clearAccessToken();
    await clearRefreshToken();
    return false;
  }
}

export async function signOut(): Promise<void> {
  try {
    await authApi.logout();
  } catch {
    // Best-effort
  }
  clearAccessToken();
  await clearRefreshToken();
}
