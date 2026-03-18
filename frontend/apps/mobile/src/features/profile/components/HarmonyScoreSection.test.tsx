import React from "react";
import { render, screen, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// ── Mocks (all factories are self-contained — jest.mock() is hoisted) ─────────

jest.mock("@harmony/api", () => ({
  identityApi: { getReports: jest.fn() },
  queryKeys: {
    identity: {
      reports: (id: number) => ["identity", "reports", id],
    },
  },
}));

jest.mock("@/features/auth/store", () => ({
  useAuthStore: jest.fn(),
}));

// Lightweight stub — tests verify presence/absence, not SVG internals
jest.mock("@/features/assessment/components/result/RadarChart", () => ({
  RadarChart: ({ data }: { data: unknown[] }) =>
    require("react").createElement("View", {
      testID: "radar-chart",
      "data-count": data.length,
    }),
}));

// ── Imports after mocks ───────────────────────────────────────────────────────

import { identityApi, queryKeys } from "@harmony/api";
import { useAuthStore } from "@/features/auth/store";
import { HarmonyScoreSection } from "./HarmonyScoreSection";
import type { PsychometricReportOut } from "@harmony/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockGetReports = identityApi.getReports as jest.Mock;
const mockUseAuthStore = useAuthStore as unknown as jest.Mock;

const makeWrapper = () => {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
};

const MOCK_CREW_PROFILE_ID = 42;

function mockAuth(crewProfileId: number | null) {
  mockUseAuthStore.mockImplementation((sel?: (s: { crewProfileId: number | null }) => unknown) => {
    const state = { crewProfileId };
    return sel ? sel(state) : state;
  });
}

const FULL_DIMENSIONS: PsychometricReportOut = {
  has_data: true,
  view_mode: "candidate",
  dimensions: {
    agreeableness: 78,
    conscientiousness: 85,
    openness: 62,
    extraversion: 70,
    emotional_stability: 65,
  },
  key_signals: [
    { type: "strength", label: "High conscientiousness" },
    { type: "risk", label: "Lower openness to change" },
  ],
};

const NO_DATA_RESPONSE: PsychometricReportOut = {
  has_data: false,
  view_mode: "candidate",
  message: "Complete at least one assessment to unlock your profile.",
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("HarmonyScoreSection", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("shows loading indicator while fetching", () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    // Never resolves during this test
    mockGetReports.mockReturnValue(new Promise(() => undefined));

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    expect(screen.getByTestId("loading-indicator")).toBeTruthy();
  });

  it("shows RadarChart when has_data=true with ≥3 dimensions", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockResolvedValue(FULL_DIMENSIONS);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() => expect(screen.getByTestId("radar-chart")).toBeTruthy());
    // Loading indicator should be gone
    expect(screen.queryByTestId("loading-indicator")).toBeNull();
  });

  it("shows key signals when has_data=true and key_signals present", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockResolvedValue(FULL_DIMENSIONS);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() => expect(screen.getByText("High conscientiousness")).toBeTruthy());
    expect(screen.getByText("Lower openness to change")).toBeTruthy();
  });

  it("shows empty state with backend message when has_data=false", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockResolvedValue(NO_DATA_RESPONSE);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() =>
      expect(
        screen.getByText("Complete at least one assessment to unlock your profile.")
      ).toBeTruthy()
    );
    // Radar should not be present
    expect(screen.queryByTestId("radar-chart")).toBeNull();
    // CTA button
    expect(screen.getByText("Start assessments")).toBeTruthy();
  });

  it("shows fallback empty state message when has_data=false and no message", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    const noMessage: PsychometricReportOut = { has_data: false, view_mode: "candidate" };
    mockGetReports.mockResolvedValue(noMessage);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() =>
      expect(
        screen.getByText("Complete assessments to unlock your Harmony profile.")
      ).toBeTruthy()
    );
  });

  it("shows no-profile fallback when crewProfileId is null", async () => {
    mockAuth(null);
    // getReports should not be called (query disabled)
    mockGetReports.mockResolvedValue(FULL_DIMENSIONS);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    // Wait one tick to confirm query never fires
    await waitFor(() =>
      expect(screen.getByText("No candidate profile found.")).toBeTruthy()
    );
    expect(mockGetReports).not.toHaveBeenCalled();
  });

  it("shows error state when getReports rejects", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockRejectedValue(new Error("Network error"));

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() =>
      expect(screen.getByText("Unable to load your psychometric report.")).toBeTruthy()
    );
  });

  it("shows score bars when has_data=true with 1 or 2 dimensions (< 3)", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    const fewDimensions: PsychometricReportOut = {
      has_data: true,
      view_mode: "candidate",
      dimensions: {
        agreeableness: 78,
        conscientiousness: 85,
      },
    };
    mockGetReports.mockResolvedValue(fewDimensions);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() => expect(screen.getByText("Agreeableness")).toBeTruthy());
    expect(screen.getByText("Conscientiousness")).toBeTruthy();
    // Radar should not appear (< 3 points)
    expect(screen.queryByTestId("radar-chart")).toBeNull();
  });

  it("always shows Coming next section", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockResolvedValue(FULL_DIMENSIONS);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() => expect(screen.getByText("Coming next")).toBeTruthy());
    expect(screen.getByText("DNRE — Need for Exploration")).toBeTruthy();
    expect(screen.getByText("MLPSM — Leadership Style")).toBeTruthy();
  });

  it("calls getReports with the correct crewProfileId", async () => {
    mockAuth(MOCK_CREW_PROFILE_ID);
    mockGetReports.mockResolvedValue(FULL_DIMENSIONS);

    render(<HarmonyScoreSection />, { wrapper: makeWrapper() });

    await waitFor(() => expect(mockGetReports).toHaveBeenCalledWith(MOCK_CREW_PROFILE_ID));
  });
});
