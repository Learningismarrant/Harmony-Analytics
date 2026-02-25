/**
 * auth.store — unit tests
 *
 * The store touches sessionStorage and document.cookie, both of which are
 * available in jsdom. We reset them between tests to guarantee isolation.
 */

import { act } from "react";

// Mock @harmony/api before importing the store
jest.mock("@harmony/api", () => ({
  setAccessToken: jest.fn(),
  clearAccessToken: jest.fn(),
}));

import { useAuthStore } from "@/features/auth/store";
import { setAccessToken, clearAccessToken } from "@harmony/api";

const mockSetAccessToken = setAccessToken as jest.Mock;
const mockClearAccessToken = clearAccessToken as jest.Mock;

// ── helpers ───────────────────────────────────────────────────────────────────

function getState() {
  return useAuthStore.getState();
}

function resetStore() {
  useAuthStore.setState({
    isAuthenticated: false,
    role: null,
    userId: null,
    profileId: null,
    name: null,
  });
}

// ── setup / teardown ──────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  resetStore();
  sessionStorage.clear();
  // Reset cookies
  document.cookie = "harmony_session=; max-age=0";
});

// ── login ─────────────────────────────────────────────────────────────────────

describe("login()", () => {
  const loginPayload = {
    accessToken: "access-123",
    refreshToken: "refresh-abc",
    role: "employer" as const,
    userId: 42,
    profileId: 7,
    name: "Ada Lovelace",
  };

  it("sets isAuthenticated to true with correct fields", () => {
    act(() => getState().login(loginPayload));

    const s = getState();
    expect(s.isAuthenticated).toBe(true);
    expect(s.role).toBe("employer");
    expect(s.userId).toBe(42);
    expect(s.profileId).toBe(7);
    expect(s.name).toBe("Ada Lovelace");
  });

  it("calls setAccessToken with the access token", () => {
    act(() => getState().login(loginPayload));
    expect(mockSetAccessToken).toHaveBeenCalledWith("access-123");
  });

  it("persists refresh token to sessionStorage", () => {
    act(() => getState().login(loginPayload));
    expect(sessionStorage.getItem("harmony_rt")).toBe("refresh-abc");
  });

  it("sets the session cookie", () => {
    act(() => getState().login(loginPayload));
    expect(document.cookie).toContain("harmony_session=1");
  });
});

// ── logout ────────────────────────────────────────────────────────────────────

describe("logout()", () => {
  it("resets all state fields to null/false", () => {
    act(() =>
      getState().login({
        accessToken: "tok",
        refreshToken: "rt",
        role: "employer",
        userId: 1,
        profileId: 1,
        name: "Test",
      }),
    );

    act(() => getState().logout());

    const s = getState();
    expect(s.isAuthenticated).toBe(false);
    expect(s.role).toBeNull();
    expect(s.userId).toBeNull();
    expect(s.profileId).toBeNull();
    expect(s.name).toBeNull();
  });

  it("calls clearAccessToken", () => {
    act(() => getState().logout());
    expect(mockClearAccessToken).toHaveBeenCalled();
  });

  it("removes refresh token from sessionStorage", () => {
    sessionStorage.setItem("harmony_rt", "some-token");
    act(() => getState().logout());
    expect(sessionStorage.getItem("harmony_rt")).toBeNull();
  });
});

// ── initial state ─────────────────────────────────────────────────────────────

describe("initial state", () => {
  it("starts as unauthenticated with all null fields", () => {
    const s = getState();
    expect(s.isAuthenticated).toBe(false);
    expect(s.role).toBeNull();
    expect(s.userId).toBeNull();
    expect(s.profileId).toBeNull();
    expect(s.name).toBeNull();
  });
});
