/**
 * API client — unit tests
 *
 * Tests the in-memory token management and the 401 silent-refresh interceptor.
 * We use axios-mock-adapter so that no real HTTP requests are made.
 */

import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import {
  apiClient,
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  setRefreshTokenProvider,
} from "@harmony/api";

// ── setup / teardown ──────────────────────────────────────────────────────────

let mock: MockAdapter;

beforeEach(() => {
  mock = new MockAdapter(apiClient);
  // Also mock the global axios for refresh calls (which use axios.post directly)
  clearAccessToken();
  setRefreshTokenProvider(() => null);
});

afterEach(() => {
  mock.restore();
});

// ── token helpers ─────────────────────────────────────────────────────────────

describe("token management", () => {
  it("setAccessToken / getAccessToken round-trips", () => {
    setAccessToken("my-token");
    expect(getAccessToken()).toBe("my-token");
  });

  it("clearAccessToken nulls the stored token", () => {
    setAccessToken("tok");
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it("attaches Bearer header when access token is set", async () => {
    setAccessToken("abc");
    mock.onGet("/ping").reply((config) => {
      const auth = config.headers?.["Authorization"];
      return [200, { header: auth }];
    });

    const { data } = await apiClient.get("/ping");
    expect(data.header).toBe("Bearer abc");
  });

  it("omits Authorization header when no token", async () => {
    clearAccessToken();
    mock.onGet("/ping").reply((config) => {
      return [200, { header: config.headers?.["Authorization"] ?? null }];
    });

    const { data } = await apiClient.get("/ping");
    expect(data.header).toBeNull();
  });
});

// ── 401 silent refresh interceptor ───────────────────────────────────────────

describe("401 interceptor", () => {
  it("retries request with new token after successful refresh", async () => {
    setRefreshTokenProvider(() => "valid-rt");

    // First call returns 401, second call returns 200
    let callCount = 0;
    mock.onGet("/protected").reply(() => {
      callCount++;
      if (callCount === 1) return [401, {}];
      return [200, { ok: true }];
    });

    // Mock the refresh endpoint on the global axios instance
    const globalMock = new MockAdapter(axios);
    globalMock
      .onPost("http://localhost:8000/auth/refresh")
      .reply(200, { access_token: "new-token" });

    try {
      const { data } = await apiClient.get("/protected");
      expect(data.ok).toBe(true);
      expect(getAccessToken()).toBe("new-token");
    } finally {
      globalMock.restore();
    }
  });

  it("rejects without retry when no refresh token is available", async () => {
    setRefreshTokenProvider(() => null);
    mock.onGet("/protected").reply(401, {});

    await expect(apiClient.get("/protected")).rejects.toMatchObject({
      response: { status: 401 },
    });
  });

  it("does not retry refresh endpoint on 401 (prevents infinite loop)", async () => {
    setRefreshTokenProvider(() => "rt");
    mock.onPost("/auth/refresh").reply(401, {});

    await expect(apiClient.post("/auth/refresh")).rejects.toMatchObject({
      response: { status: 401 },
    });
  });

  it("does not retry a request that already had _retried=true", async () => {
    setRefreshTokenProvider(() => "rt");
    let callCount = 0;
    mock.onGet("/double-retry").reply(() => {
      callCount++;
      return [401, {}];
    });

    const globalMock = new MockAdapter(axios);
    globalMock
      .onPost("http://localhost:8000/auth/refresh")
      .reply(200, { access_token: "tok" });

    try {
      await apiClient.get("/double-retry").catch(() => {});
      // The interceptor sets _retried=true — should only call the endpoint twice max
      // (once original, once retry after refresh)
      expect(callCount).toBeLessThanOrEqual(2);
    } finally {
      globalMock.restore();
    }
  });
});
