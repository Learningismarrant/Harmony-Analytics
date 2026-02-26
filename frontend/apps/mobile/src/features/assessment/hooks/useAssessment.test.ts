import React from "react";
import { renderHook, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAssessment } from "./useAssessment";

const mockGetCatalogue = jest.fn();
const mockGetMyResults = jest.fn();

jest.mock("@harmony/api", () => ({
  assessmentApi: {
    getCatalogue: (...args: unknown[]) => mockGetCatalogue(...args),
    getMyResults: (...args: unknown[]) => mockGetMyResults(...args),
  },
  queryKeys: {
    assessment: {
      catalogue: () => ["assessment", "catalogue"],
      myResults: () => ["assessment", "myResults"],
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

describe("useAssessment", () => {
  it("isLoading is true while both queries are pending", () => {
    mockGetCatalogue.mockReturnValue(new Promise(() => {}));
    mockGetMyResults.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useAssessment(), { wrapper: makeWrapper() });
    expect(result.current.isLoading).toBe(true);
  });

  it("completedTestIds contains IDs from myResults", async () => {
    mockGetCatalogue.mockResolvedValue([
      { id: 1, name: "Big Five", test_type: "likert" },
      { id: 2, name: "IQ", test_type: "cognitive" },
    ]);
    mockGetMyResults.mockResolvedValue([{ test_id: 1, global_score: 80 }]);

    const { result } = renderHook(() => useAssessment(), { wrapper: makeWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.completedTestIds.has(1)).toBe(true);
    expect(result.current.completedTestIds.has(2)).toBe(false);
  });

  it("completedTestIds is empty when myResults is empty", async () => {
    mockGetCatalogue.mockResolvedValue([]);
    mockGetMyResults.mockResolvedValue([]);

    const { result } = renderHook(() => useAssessment(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.completedTestIds.size).toBe(0);
  });

  it("exposes catalogue and myResults from queries", async () => {
    const catalogue = [{ id: 3, name: "MBTI", test_type: "likert" }];
    const myResults = [{ test_id: 3, global_score: 72 }];
    mockGetCatalogue.mockResolvedValue(catalogue);
    mockGetMyResults.mockResolvedValue(myResults);

    const { result } = renderHook(() => useAssessment(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.catalogue).toEqual(catalogue);
    expect(result.current.myResults).toEqual(myResults);
  });
});
