/**
 * Mobile auth helpers — expo-secure-store
 *
 * Security model:
 *   - Refresh token: stored in SecureStore (encrypted on device)
 *   - Access token: stored in Zustand memory only
 *   - On app restart: load refresh token → hit /auth/refresh → restore session
 *
 * Calibrateurs :
 *   - Pas de refresh token — JWT stocké directement dans SecureStore
 *   - Sur restart : décode le JWT, vérifie exp, restaure l'access token si valide
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

// ── Calibrateur auth helpers ──────────────────────────────────────────────────

const CALIB_TOKEN_KEY = "harmony_calib_token";

export async function saveCalibToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(CALIB_TOKEN_KEY, token, {
    keychainAccessible: SecureStore.WHEN_UNLOCKED,
  });
}

export async function loadCalibToken(): Promise<string | null> {
  return SecureStore.getItemAsync(CALIB_TOKEN_KEY);
}

export async function clearCalibToken(): Promise<void> {
  await SecureStore.deleteItemAsync(CALIB_TOKEN_KEY);
}

/**
 * Tente de restaurer une session calibrateur depuis le JWT stocké.
 * Décode la payload base64, vérifie l'expiration, recharge le token en mémoire.
 * Retourne { ok: true, calibratorId, name } si restauré, { ok: false } sinon.
 */
export async function restoreCalibSession(): Promise<
  | { ok: true; calibratorId: number; name: string }
  | { ok: false }
> {
  try {
    const token = await loadCalibToken();
    if (!token) return { ok: false };

    // Décodage JWT payload (base64url → JSON) sans vérification de signature
    const parts = token.split(".");
    if (parts.length !== 3) return { ok: false };

    const payloadBase64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const payloadJson = atob(payloadBase64);
    const payload = JSON.parse(payloadJson) as {
      sub?: string;
      exp?: number;
      name?: string;
      calibrator_id?: number;
    };

    // Vérifier l'expiration
    const now = Math.floor(Date.now() / 1000);
    if (!payload.exp || payload.exp < now) {
      await clearCalibToken();
      return { ok: false };
    }

    const calibratorId = payload.calibrator_id ?? parseInt(payload.sub ?? "0", 10);
    const name = payload.name ?? "Calibrateur";

    setAccessToken(token);
    return { ok: true, calibratorId, name };
  } catch {
    clearAccessToken();
    await clearCalibToken();
    return { ok: false };
  }
}
