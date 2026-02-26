import React from "react";
import { Alert } from "react-native";
import { renderHook, act, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useTakeTest } from "./useTakeTest";

const mockGetQuestions = jest.fn();
const mockSubmit = jest.fn();
const mockRouterReplace = jest.fn();

jest.mock("@harmony/api", () => ({
  assessmentApi: {
    getQuestions: (...args: unknown[]) => mockGetQuestions(...args),
    submit: (...args: unknown[]) => mockSubmit(...args),
  },
  queryKeys: {
    assessment: {
      questions: (id: number) => ["assessment", "questions", id],
      myResults: () => ["assessment", "myResults"],
    },
    identity: {
      fullProfile: (id: number) => ["identity", "fullProfile", id],
    },
  },
}));

const QUESTIONS = [
  { id: 1, text: "Q1", options: null },
  { id: 2, text: "Q2", options: null },
  { id: 3, text: "Q3", options: null },
];

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

beforeEach(() => {
  jest.clearAllMocks();
  mockGetQuestions.mockResolvedValue(QUESTIONS);
  jest.mocked(useRouter).mockReturnValue({
    replace: mockRouterReplace,
    push: jest.fn(),
    back: jest.fn(),
  } as ReturnType<typeof useRouter>);
});

describe("useTakeTest — navigation", () => {
  it("starts at index 0", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.currentIndex).toBe(0);
  });

  it("goNext advances the index", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.goNext());
    expect(result.current.currentIndex).toBe(1);
  });

  it("goNext does nothing on the last question", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.goNext());
    act(() => result.current.goNext());
    act(() => result.current.goNext()); // already at last
    expect(result.current.currentIndex).toBe(2);
  });

  it("goPrev does nothing at index 0", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.goPrev());
    expect(result.current.currentIndex).toBe(0);
  });

  it("goPrev goes back after goNext", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.goNext());
    act(() => result.current.goPrev());
    expect(result.current.currentIndex).toBe(0);
  });
});

describe("useTakeTest — answers", () => {
  it("selectAnswer records the response for the question", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.selectAnswer(1, "3"));
    expect(result.current.responses[1]).toBe("3");
  });

  it("selectAnswer can overwrite a previous answer", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.selectAnswer(1, "2"));
    act(() => result.current.selectAnswer(1, "5"));
    expect(result.current.responses[1]).toBe("5");
  });
});

describe("useTakeTest — submit", () => {
  it("handleSubmit shows alert when questions are unanswered", async () => {
    jest.spyOn(Alert, "alert").mockImplementation(() => {});

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // Answer only 1 of 3
    act(() => result.current.selectAnswer(1, "1"));
    act(() => result.current.handleSubmit());

    expect(Alert.alert).toHaveBeenCalledWith(
      "Incomplete",
      expect.stringContaining("unanswered"),
      expect.any(Array),
    );
  });

  it("handleSubmit submits directly when all questions are answered", async () => {
    mockSubmit.mockResolvedValue({ global_score: 78 });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(1, "1");
      result.current.selectAnswer(2, "2");
      result.current.selectAnswer(3, "3");
    });

    await act(async () => {
      result.current.handleSubmit();
    });

    await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
    expect(mockSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ test_id: 1 }),
    );
  });

  it("navigates to result screen with score after successful submit", async () => {
    mockSubmit.mockResolvedValue({ global_score: 78.6 });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(1, "1");
      result.current.selectAnswer(2, "2");
      result.current.selectAnswer(3, "3");
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(mockRouterReplace).toHaveBeenCalled());

    expect(mockRouterReplace).toHaveBeenCalledWith(
      expect.stringContaining("score=79"),
    );
  });
});
