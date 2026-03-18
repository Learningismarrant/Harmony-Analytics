import { renderHook, act } from "@testing-library/react-native";
import { Animated } from "react-native";
import { useQuestionTransition } from "./useQuestionTransition";

beforeEach(() => {
  jest.spyOn(Animated, "parallel").mockReturnValue({
    start: jest.fn((cb?: Animated.EndCallback) => cb?.({ finished: true })),
    stop: jest.fn(),
    reset: jest.fn(),
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("useQuestionTransition", () => {
  it("returns animatedStyle with opacity and transform", () => {
    const { result } = renderHook(() => useQuestionTransition());
    expect(result.current.animatedStyle).toHaveProperty("opacity");
    expect(result.current.animatedStyle).toHaveProperty("transform");
  });

  it("triggerTransition calls the callback", () => {
    const { result } = renderHook(() => useQuestionTransition());
    const callback = jest.fn();
    act(() => result.current.triggerTransition(callback));
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("resetAnimation does not throw", () => {
    const { result } = renderHook(() => useQuestionTransition());
    expect(() => act(() => result.current.resetAnimation())).not.toThrow();
  });

  it("triggerTransition fires the callback only once per call", () => {
    const { result } = renderHook(() => useQuestionTransition());
    const cb = jest.fn();
    act(() => result.current.triggerTransition(cb));
    act(() => result.current.triggerTransition(cb));
    expect(cb).toHaveBeenCalledTimes(2);
  });
});
