import React from "react";
import { Alert, BackHandler } from "react-native";
import { renderHook, act, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter, useFocusEffect } from "expo-router";
import { useTakeTest } from "./useTakeTest";

const mockGetQuestions = jest.fn();
const mockGetCatalogue = jest.fn();
const mockSubmit = jest.fn();
const mockRouterReplace = jest.fn();
const mockSetLastResult = jest.fn();

jest.mock("@/features/assessment/store/useLastResultStore", () => ({
  useLastResultStore: {
    getState: () => ({ setLastResult: mockSetLastResult }),
  },
}));

jest.mock("@harmony/api", () => ({
  assessmentApi: {
    getQuestions: (...args: unknown[]) => mockGetQuestions(...args),
    getCatalogue: (...args: unknown[]) => mockGetCatalogue(...args),
    submit: (...args: unknown[]) => mockSubmit(...args),
  },
  queryKeys: {
    assessment: {
      questions: (id: number) => ["assessment", "questions", id],
      catalogue: () => ["assessment", "catalogue"],
      myResults: () => ["assessment", "myResults"],
    },
    identity: {
      fullProfile: (id: number) => ["identity", "fullProfile", id],
    },
  },
}));

// expo-router is globally mocked in jest.setup.ts (useRouter + useFocusEffect).
// We configure their behaviour per-test in beforeEach via jest.mocked().

const CATALOGUE = [
  { id: 1, name: "Big Five", test_type: "likert", instructions: "Be honest." },
  { id: 2, name: "Cutty Sark", test_type: "tirt", instructions: null },
];

const QUESTIONS = [
  { id: 10, text: "Q1", options: null },
  { id: 20, text: "Q2", options: null },
  { id: 30, text: "Q3", options: null },
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
  mockGetCatalogue.mockResolvedValue(CATALOGUE);
  jest.mocked(useRouter).mockReturnValue({
    replace: mockRouterReplace,
    push: jest.fn(),
    back: jest.fn(),
  } as ReturnType<typeof useRouter>);
  // useFocusEffect: execute the callback immediately so the BackHandler is registered
  jest.mocked(useFocusEffect).mockImplementation((cb) => { cb(); });
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
    act(() => result.current.goNext());
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
  it("selectAnswer records the response", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.selectAnswer(10, "3"));
    expect(result.current.responses[10]).toBe("3");
  });

  it("selectAnswer can overwrite a previous answer", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.selectAnswer(10, "2"));
    act(() => result.current.selectAnswer(10, "5"));
    expect(result.current.responses[10]).toBe("5");
  });

  it("selectAnswer is a no-op when questions are not loaded (guard)", () => {
    mockGetQuestions.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    act(() => result.current.selectAnswer(10, "3"));
    expect(result.current.responses[10]).toBeUndefined();
  });

  it("selectAndAdvance records response and moves to next question", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.selectAndAdvance(10, "left"));
    expect(result.current.responses[10]).toBe("left");
    expect(result.current.currentIndex).toBe(1);
  });

  it("selectAndAdvance does not advance past the last question", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.goNext());
    act(() => result.current.goNext()); // index = 2 (last)
    act(() => result.current.selectAndAdvance(30, "right"));
    expect(result.current.currentIndex).toBe(2);
  });
});

describe("useTakeTest — testInfo", () => {
  it("exposes testInfo matching the current testId", async () => {
    const { result } = renderHook(() => useTakeTest(2), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.testInfo?.name).toBe("Cutty Sark");
    expect(result.current.testInfo?.test_type).toBe("tirt");
  });

  it("testInfo is undefined for an unknown testId", async () => {
    const { result } = renderHook(() => useTakeTest(99), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.testInfo).toBeUndefined();
  });
});

describe("useTakeTest — showInstructions", () => {
  it("showInstructions is true on mount", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.showInstructions).toBe(true);
  });

  it("setShowInstructions(false) dismisses the instructions", async () => {
    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.setShowInstructions(false));
    expect(result.current.showInstructions).toBe(false);
  });
});

describe("useTakeTest — reset on testId change", () => {
  it("resets currentIndex, responses, showInstructions and isSubmitted when testId changes", async () => {
    const { result, rerender } = renderHook(
      ({ id }: { id: number }) => useTakeTest(id),
      { wrapper: makeWrapper(), initialProps: { id: 1 } },
    );
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goNext());
    act(() => result.current.selectAnswer(20, "4"));
    act(() => result.current.setShowInstructions(false));
    expect(result.current.currentIndex).toBe(1);
    expect(result.current.showInstructions).toBe(false);

    rerender({ id: 2 });

    await waitFor(() => expect(result.current.currentIndex).toBe(0));
    expect(result.current.responses).toEqual({});
    expect(result.current.showInstructions).toBe(true);
    expect(result.current.isSubmitted).toBe(false);
  });
});

describe("useTakeTest — submit", () => {
  it("handleSubmit shows alert when questions are unanswered", async () => {
    jest.spyOn(Alert, "alert").mockImplementation(() => {});

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.selectAnswer(10, "1")); // only 1 of 3
    act(() => result.current.handleSubmit());

    expect(Alert.alert).toHaveBeenCalledWith(
      "Test incomplet",
      expect.stringContaining("2"),
      expect.any(Array),
    );
  });

  it("handleSubmit submits directly when all questions are answered", async () => {
    mockSubmit.mockResolvedValue({ global_score: 78 });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(10, "1");
      result.current.selectAnswer(20, "2");
      result.current.selectAnswer(30, "3");
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(mockSubmit).toHaveBeenCalled());
    expect(mockSubmit).toHaveBeenCalledWith(expect.objectContaining({ test_id: 1 }));
  });

  it("sets isSubmitted to true after successful submit — no direct navigation", async () => {
    mockSubmit.mockResolvedValue({ global_score: 78.6 });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(10, "1");
      result.current.selectAnswer(20, "2");
      result.current.selectAnswer(30, "3");
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(result.current.isSubmitted).toBe(true));
    expect(mockRouterReplace).not.toHaveBeenCalled();
  });

  it("stores the result in useLastResultStore on success", async () => {
    const mockResult = { global_score: 91.0 };
    mockSubmit.mockResolvedValue(mockResult);

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(10, "1");
      result.current.selectAnswer(20, "2");
      result.current.selectAnswer(30, "3");
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(mockSetLastResult).toHaveBeenCalledWith(mockResult));
  });
});

describe("useTakeTest — BackHandler (Android)", () => {
  it("registers a BackHandler listener on focus", async () => {
    const addEventSpy = jest.spyOn(BackHandler, "addEventListener");

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(addEventSpy).toHaveBeenCalledWith("hardwareBackPress", expect.any(Function));
  });

  it("shows a confirmation alert when back is pressed mid-test", async () => {
    jest.spyOn(Alert, "alert").mockImplementation(() => {});
    let capturedHandler: (() => boolean) | undefined;
    jest.spyOn(BackHandler, "addEventListener").mockImplementation((_event, handler) => {
      capturedHandler = handler as () => boolean;
      return { remove: jest.fn() };
    });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.setShowInstructions(false));

    const blocked = capturedHandler?.();
    expect(blocked).toBe(true);
    expect(Alert.alert).toHaveBeenCalledWith("Analyse en cours", expect.any(String), expect.any(Array));
  });

  it("does not block back when instructions are still visible", async () => {
    let capturedHandler: (() => boolean) | undefined;
    jest.spyOn(BackHandler, "addEventListener").mockImplementation((_event, handler) => {
      capturedHandler = handler as () => boolean;
      return { remove: jest.fn() };
    });

    const { result } = renderHook(() => useTakeTest(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const blocked = capturedHandler?.();
    expect(blocked).toBe(false);
  });
});
