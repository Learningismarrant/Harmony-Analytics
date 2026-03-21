import React from "react";
import { Alert, BackHandler } from "react-native";
import { renderHook, act, waitFor } from "@testing-library/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter, useFocusEffect } from "expo-router";
import { useCalibPassation } from "./useCalibPassation";

const mockStartSession = jest.fn();
const mockGetQuestions = jest.fn();
const mockSubmitSession = jest.fn();
const mockRouterReplace = jest.fn();

jest.mock("@harmony/api", () => ({
  calibrationApi: {
    startSession: (...args: unknown[]) => mockStartSession(...args),
    getQuestions: (...args: unknown[]) => mockGetQuestions(...args),
    submitSession: (...args: unknown[]) => mockSubmitSession(...args),
  },
  calibrationQueryKeys: {
    questions: (id: number) => ["calibration", "questions", id],
    sessions: () => ["calibration", "sessions"],
    me: () => ["calibration", "me"],
    catalogues: () => ["calibration", "catalogues"],
    sessionScore: (id: number) => ["calibration", "session", "score", id],
  },
}));

const SESSION = {
  id: 1,
  calibrator_id: 1,
  catalogue_id: 1,
  status: "in_progress" as const,
  started_at: "2026-03-21T10:00:00Z",
  completed_at: null,
  response_count: 0,
};

const QUESTIONS = [
  { id: 1, catalogue_id: 1, order_index: 1, text: "Q1", question_type: "likert", trait: "A", options: null },
  { id: 2, catalogue_id: 1, order_index: 2, text: "Q2", question_type: "likert", trait: "A", options: null },
  { id: 3, catalogue_id: 1, order_index: 3, text: "Q3", question_type: "likert", trait: "B", options: null },
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
  mockStartSession.mockResolvedValue(SESSION);
  mockGetQuestions.mockResolvedValue(QUESTIONS);
  mockSubmitSession.mockResolvedValue({ session_id: 1, status: "completed", score: null, message: "OK" });
  jest.mocked(useRouter).mockReturnValue({
    replace: mockRouterReplace,
    push: jest.fn(),
    back: jest.fn(),
  } as ReturnType<typeof useRouter>);
  jest.mocked(useFocusEffect).mockImplementation((cb) => { cb(); });
});

describe("useCalibPassation — initialisation", () => {
  it("démarre à l'index 0 après chargement", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.session).not.toBeNull());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.currentIndex).toBe(0);
  });

  it("showInstructions est true au départ", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.session).not.toBeNull());
    expect(result.current.showInstructions).toBe(true);
  });

  it("appelle startSession au mount", async () => {
    renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(mockStartSession).toHaveBeenCalledWith(1));
  });
});

describe("useCalibPassation — selectAnswer stocke un entier", () => {
  it("selectAnswer stores integer value", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.selectAnswer(1, 3));
    expect(result.current.responses[1]).toBe(3);
  });

  it("selectAnswer peut écraser une réponse précédente", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.selectAnswer(1, 2));
    act(() => result.current.selectAnswer(1, 5));
    expect(result.current.responses[1]).toBe(5);
  });

  it("selectAnswer est un no-op si questions non chargées", () => {
    mockGetQuestions.mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    act(() => result.current.selectAnswer(1, 3));
    expect(result.current.responses[1]).toBeUndefined();
  });
});

describe("useCalibPassation — navigation", () => {
  it("goNext increments index", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goNext());
    expect(result.current.currentIndex).toBe(1);
  });

  it("goPrev decrements index", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goNext());
    act(() => result.current.goPrev());
    expect(result.current.currentIndex).toBe(0);
  });

  it("goNext s'arrête à la dernière question", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goNext());
    act(() => result.current.goNext());
    act(() => result.current.goNext()); // pas au-delà de 2
    expect(result.current.currentIndex).toBe(2);
  });

  it("goPrev ne descend pas en dessous de 0", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goPrev());
    expect(result.current.currentIndex).toBe(0);
  });
});

describe("useCalibPassation — reset sur changement catalogueId", () => {
  it("remet à zéro l'état quand catalogueId change", async () => {
    const { result, rerender } = renderHook(
      ({ id }: { id: number }) => useCalibPassation(id),
      { wrapper: makeWrapper(), initialProps: { id: 1 } },
    );
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.goNext());
    act(() => result.current.selectAnswer(2, 4));
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

describe("useCalibPassation — submit", () => {
  it("handleSubmit affiche une alerte si des questions sont sans réponse", async () => {
    jest.spyOn(Alert, "alert").mockImplementation(() => {});

    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.selectAnswer(1, 1)); // seulement 1 sur 3
    act(() => result.current.handleSubmit());

    expect(Alert.alert).toHaveBeenCalledWith(
      "Test incomplet",
      expect.stringContaining("2"),
      expect.any(Array),
    );
  });

  it("handleSubmit soumet directement si toutes les questions sont répondues", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(1, 1);
      result.current.selectAnswer(2, 2);
      result.current.selectAnswer(3, 3);
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(mockSubmitSession).toHaveBeenCalled());
  });

  it("navigue vers le résultat après succès de soumission", async () => {
    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => {
      result.current.selectAnswer(1, 1);
      result.current.selectAnswer(2, 2);
      result.current.selectAnswer(3, 3);
    });

    await act(async () => result.current.handleSubmit());
    await waitFor(() => expect(mockRouterReplace).toHaveBeenCalled());
  });
});

describe("useCalibPassation — BackHandler (Android)", () => {
  it("enregistre un listener BackHandler au focus", async () => {
    const addEventSpy = jest.spyOn(BackHandler, "addEventListener");

    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(addEventSpy).toHaveBeenCalledWith("hardwareBackPress", expect.any(Function));
  });

  it("ne bloque pas le retour quand les instructions sont affichées", async () => {
    let capturedHandler: (() => boolean) | undefined;
    jest.spyOn(BackHandler, "addEventListener").mockImplementation((_event, handler) => {
      capturedHandler = handler as () => boolean;
      return { remove: jest.fn() };
    });

    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // showInstructions = true par défaut
    const blocked = capturedHandler?.();
    expect(blocked).toBe(false);
  });

  it("affiche une alerte de confirmation si retour pressé en cours de test", async () => {
    jest.spyOn(Alert, "alert").mockImplementation(() => {});
    let capturedHandler: (() => boolean) | undefined;
    jest.spyOn(BackHandler, "addEventListener").mockImplementation((_event, handler) => {
      capturedHandler = handler as () => boolean;
      return { remove: jest.fn() };
    });

    const { result } = renderHook(() => useCalibPassation(1), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.setShowInstructions(false));

    const blocked = capturedHandler?.();
    expect(blocked).toBe(true);
    expect(Alert.alert).toHaveBeenCalledWith(
      "Session en cours",
      expect.any(String),
      expect.any(Array),
    );
  });
});
