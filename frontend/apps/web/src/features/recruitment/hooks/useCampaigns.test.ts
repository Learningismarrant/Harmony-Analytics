/**
 * useCampaigns — unit tests
 */

import { renderHook } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const mockUseQuery = jest.fn();
jest.mock("@tanstack/react-query", () => ({
  ...jest.requireActual("@tanstack/react-query"),
  useQuery: (...args: unknown[]) => mockUseQuery(...args),
}));

import { useCampaigns } from "./useCampaigns";

// ── Fixtures ──────────────────────────────────────────────────────────────────

const makeCampaign = (id: number, yachtId: number, archived = false) => ({
  id,
  yacht_id: yachtId,
  title: `Campaign ${id}`,
  position: "Deckhand",
  candidate_count: 0,
  is_archived: archived,
  invite_token: `tok-${id}`,
});

// ── Test wrapper ──────────────────────────────────────────────────────────────

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client: qc }, children);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

beforeEach(() => jest.clearAllMocks());

describe("useCampaigns", () => {
  it("returns only campaigns matching the given yachtId", () => {
    mockUseQuery.mockReturnValue({
      data: [
        makeCampaign(1, 10),
        makeCampaign(2, 10),
        makeCampaign(3, 99), // different yacht
      ],
      isLoading: false,
    });
    const { result } = renderHook(() => useCampaigns(10), { wrapper });
    expect(result.current.campaigns).toHaveLength(2);
    expect(result.current.campaigns.every((c) => c.yacht_id === 10)).toBe(true);
  });

  it("excludes archived campaigns", () => {
    mockUseQuery.mockReturnValue({
      data: [makeCampaign(1, 10), makeCampaign(2, 10, true)],
      isLoading: false,
    });
    const { result } = renderHook(() => useCampaigns(10), { wrapper });
    expect(result.current.campaigns).toHaveLength(1);
    expect(result.current.campaigns[0].id).toBe(1);
  });

  it("returns empty array when no campaign matches the yacht", () => {
    mockUseQuery.mockReturnValue({
      data: [makeCampaign(5, 999)],
      isLoading: false,
    });
    const { result } = renderHook(() => useCampaigns(10), { wrapper });
    expect(result.current.campaigns).toHaveLength(0);
  });

  it("forwards isLoading from the query", () => {
    mockUseQuery.mockReturnValue({ data: undefined, isLoading: true });
    const { result } = renderHook(() => useCampaigns(10), { wrapper });
    expect(result.current.isLoading).toBe(true);
  });
});
