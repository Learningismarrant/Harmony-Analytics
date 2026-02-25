/**
 * useMatching — unit tests
 */

import { renderHook, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockUseQuery    = jest.fn();
const mockUseMutation = jest.fn();
const mockInvalidate  = jest.fn();

jest.mock("@tanstack/react-query", () => ({
  ...jest.requireActual("@tanstack/react-query"),
  useQuery:       (...args: unknown[]) => mockUseQuery(...args),
  useMutation:    (...args: unknown[]) => mockUseMutation(...args),
  useQueryClient: () => ({ invalidateQueries: mockInvalidate }),
}));

import { useMatching } from "./useMatching";

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeCandidate(id: number, ySuccess: number, hired = false, rejected = false) {
  return {
    crew_profile_id: id,
    name: `Crew ${id}`,
    is_hired: hired,
    is_rejected: rejected,
    team_integration: { y_success: ySuccess, available: true },
    profile_fit: { g_fit: 70, safety_flags: [] },
  };
}

// ── Test wrapper ──────────────────────────────────────────────────────────────

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client: qc }, children);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks();
  mockUseMutation.mockReturnValue({ mutate: jest.fn(), isPending: false });
});

describe("useMatching", () => {
  it("sorts candidates by y_success descending (hired last)", () => {
    mockUseQuery.mockReturnValue({
      data: [
        makeCandidate(1, 60),
        makeCandidate(2, 90),
        makeCandidate(3, 75, true), // hired — should go last
      ],
      isLoading: false,
    });
    const { result } = renderHook(() => useMatching(1), { wrapper });
    const ids = result.current.candidates.map((c) => c.crew_profile_id);
    expect(ids).toEqual([2, 1, 3]); // 90 > 60, then hired
  });

  it("returns empty candidates when campaignId is null", () => {
    mockUseQuery.mockReturnValue({ data: undefined, isLoading: false });
    const { result } = renderHook(() => useMatching(null), { wrapper });
    expect(result.current.candidates).toHaveLength(0);
  });

  it("calls reject mutation with the correct crewProfileId", () => {
    const mockMutate = jest.fn();
    mockUseMutation.mockReturnValue({ mutate: mockMutate, isPending: false });
    mockUseQuery.mockReturnValue({ data: [], isLoading: false });

    const { result } = renderHook(() => useMatching(5), { wrapper });
    act(() => { result.current.reject(42); });
    expect(mockMutate).toHaveBeenCalledWith(42);
  });
});
