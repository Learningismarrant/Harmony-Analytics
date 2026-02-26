import React from "react";
import { renderHook, waitFor, act } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSurvey } from "./useSurvey";

const mockGetPending = jest.fn();
const mockRespond = jest.fn();

jest.mock("@harmony/api", () => ({
  surveyApi: {
    getPending: (...args: unknown[]) => mockGetPending(...args),
    respond: (...args: unknown[]) => mockRespond(...args),
  },
  queryKeys: {
    survey: {
      pending: () => ["survey", "pending"],
    },
  },
}));

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

beforeEach(() => jest.clearAllMocks());

describe("useSurvey", () => {
  it("isLoading is true while query is pending", () => {
    mockGetPending.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useSurvey(), { wrapper: makeWrapper() });
    expect(result.current.isLoading).toBe(true);
  });

  it("returns empty array when no pending surveys", async () => {
    mockGetPending.mockResolvedValue([]);

    const { result } = renderHook(() => useSurvey(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.pendingSurveys).toEqual([]);
  });

  it("returns pending surveys from API", async () => {
    const surveys = [
      {
        id: 1,
        yacht_id: 10,
        trigger_type: "monthly_pulse",
        target_crew_ids: [5],
        is_open: true,
        created_at: "2026-02-01T00:00:00Z",
        closed_at: null,
        response_count: 0,
      },
    ];
    mockGetPending.mockResolvedValue(surveys);

    const { result } = renderHook(() => useSurvey(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.pendingSurveys).toEqual(surveys);
    expect(result.current.pendingSurveys).toHaveLength(1);
  });

  it("isError is true on fetch failure", async () => {
    mockGetPending.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSurvey(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it("calls surveyApi.respond with correct args on respond()", async () => {
    mockGetPending.mockResolvedValue([]);
    mockRespond.mockResolvedValue({
      id: 99,
      survey_id: 1,
      trigger_type: "monthly_pulse",
      intent_to_stay: 8,
      submitted_at: "2026-02-01T12:00:00Z",
    });

    const { result } = renderHook(() => useSurvey(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const body = { intent_to_stay: 8, team_cohesion: 7 };
    await act(async () => {
      await result.current.respond({ surveyId: 1, body });
    });

    expect(mockRespond).toHaveBeenCalledWith(1, body);
  });
});
