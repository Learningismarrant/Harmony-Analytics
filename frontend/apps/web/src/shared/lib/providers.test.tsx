/**
 * Providers — unit tests
 *
 * Key invariants:
 * 1. Children render immediately (no SSR-blocking gate).
 * 2. Session restoration runs after mount (useEffect).
 * 3. ReactQueryDevtools is never rendered in production or during SSR.
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockSetRefreshTokenProvider = jest.fn();
const mockSetAccessToken = jest.fn();
const mockRefresh = jest.fn();

jest.mock("@harmony/api", () => ({
  setRefreshTokenProvider: (...args: unknown[]) =>
    mockSetRefreshTokenProvider(...args),
  setAccessToken: (...args: unknown[]) => mockSetAccessToken(...args),
  clearAccessToken: jest.fn(),
  authApi: {
    refresh: (...args: unknown[]) => mockRefresh(...args),
  },
}));

// Devtools import is async — mock it to avoid dynamic import issues
jest.mock("@tanstack/react-query-devtools", () => ({
  ReactQueryDevtools: () => <div data-testid="devtools" />,
}));

import { Providers } from "@/shared/lib/providers";

// ── helpers ───────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  sessionStorage.clear();
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("Providers", () => {
  it("renders children immediately (no white-screen gate)", () => {
    render(
      <Providers>
        <span data-testid="child">Hello</span>
      </Providers>,
    );
    // Children must be visible without waiting for any effect
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  it("registers the refresh token provider on mount", async () => {
    render(<Providers><div /></Providers>);
    await waitFor(() => {
      expect(mockSetRefreshTokenProvider).toHaveBeenCalledTimes(1);
    });
  });

  it("does NOT call authApi.refresh when there is no stored refresh token", async () => {
    sessionStorage.clear(); // no "harmony_rt" key
    render(<Providers><div /></Providers>);
    await waitFor(() => {
      expect(mockSetRefreshTokenProvider).toHaveBeenCalled();
    });
    expect(mockRefresh).not.toHaveBeenCalled();
  });

  it("calls authApi.refresh and setAccessToken when a refresh token exists", async () => {
    sessionStorage.setItem("harmony_rt", "stored-rt");
    mockRefresh.mockResolvedValue({ access_token: "new-access" });

    render(<Providers><div /></Providers>);

    await waitFor(() => {
      expect(mockRefresh).toHaveBeenCalledWith("stored-rt");
      expect(mockSetAccessToken).toHaveBeenCalledWith("new-access");
    });
  });

  it("clears sessionStorage on failed refresh", async () => {
    sessionStorage.setItem("harmony_rt", "expired-rt");
    mockRefresh.mockRejectedValue(new Error("401"));

    render(<Providers><div /></Providers>);

    await waitFor(() => {
      expect(sessionStorage.getItem("harmony_rt")).toBeNull();
    });
  });

  it("renders multiple children without error", () => {
    render(
      <Providers>
        <span data-testid="a">A</span>
        <span data-testid="b">B</span>
      </Providers>,
    );
    expect(screen.getByTestId("a")).toBeInTheDocument();
    expect(screen.getByTestId("b")).toBeInTheDocument();
  });
});
