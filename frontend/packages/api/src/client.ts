/**
 * Axios instance — Harmony API client
 *
 * Security model:
 *   - Access token: stored in memory only (never localStorage/cookie)
 *   - Refresh token: passed via refreshTokenProvider (web = sessionStorage, mobile = SecureStore)
 *   - On 401: attempt silent refresh via /auth/refresh with refresh_token in body, retry once
 */
import axios, {
  AxiosError,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";

// ── In-memory token store ─────────────────────────────────────────────────────
// Access token is intentionally NOT exported — only the client and auth helpers
// should touch it, preventing accidental exposure.

let _accessToken: string | null = null;
let _isRefreshing = false;
let _refreshQueue: Array<(token: string | null) => void> = [];

// ── Refresh token provider ─────────────────────────────────────────────────────
// Platform-specific: web sets () => sessionStorage.getItem("harmony_rt"),
//                    mobile sets () => SecureStore.getItemAsync("harmony_rt")

let _getRefreshToken: () => string | null | Promise<string | null> = () => null;

export function setRefreshTokenProvider(
  fn: () => string | null | Promise<string | null>,
): void {
  _getRefreshToken = fn;
}

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

export function clearAccessToken(): void {
  _accessToken = null;
}

// ── Axios instance ────────────────────────────────────────────────────────────

const BASE_URL = process.env["NEXT_PUBLIC_API_URL"] ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: false,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request interceptor — attach Bearer token ────────────────────────────────

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (_accessToken) {
      config.headers["Authorization"] = `Bearer ${_accessToken}`;
    }
    return config;
  },
  (error: unknown) => Promise.reject(error),
);

// ── Response interceptor — silent token refresh on 401 ──────────────────────

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean;
    };

    if (
      error.response?.status === 401 &&
      !originalRequest._retried &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      originalRequest._retried = true;

      if (_isRefreshing) {
        // Queue the request until refresh is done
        return new Promise((resolve, reject) => {
          _refreshQueue.push((token) => {
            if (!token) {
              reject(error);
              return;
            }
            originalRequest.headers["Authorization"] = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      _isRefreshing = true;

      try {
        const refreshToken = await _getRefreshToken();
        if (!refreshToken) throw new Error("No refresh token available");
        const { data } = await axios.post<{ access_token: string }>(
          `${BASE_URL}/auth/refresh`,
          { refresh_token: refreshToken },
        );
        const newToken = data.access_token;
        setAccessToken(newToken);

        // Drain the queue
        _refreshQueue.forEach((cb) => cb(newToken));
        _refreshQueue = [];

        originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch {
        // Refresh failed — clear token and signal logout
        clearAccessToken();
        _refreshQueue.forEach((cb) => cb(null));
        _refreshQueue = [];
        return Promise.reject(error);
      } finally {
        _isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// ── Typed request helpers ─────────────────────────────────────────────────────

export async function get<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await apiClient.get<T>(url, config);
  return data;
}

export async function post<T, D = unknown>(
  url: string,
  body?: D,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await apiClient.post<T>(url, body, config);
  return data;
}

export async function patch<T, D = unknown>(
  url: string,
  body?: D,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await apiClient.patch<T>(url, body, config);
  return data;
}

export async function del<T = void>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await apiClient.delete<T>(url, config);
  return data;
}
