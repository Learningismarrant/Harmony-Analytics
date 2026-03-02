import { useLastResultStore } from "./useLastResultStore";
import type { TestResultOut } from "@harmony/types";

const MOCK_RESULT: TestResultOut = {
  id: 5,
  test_id: 3,
  crew_profile_id: 10,
  test_name: "CUTTY SARK T-IRT",
  global_score: 74.0,
  scores: {
    traits: {},
    global_score: 74.0,
    tirt_detail: {
      C: { z_score: 1.18, percentile: 88.1 },
      reliability_index: 0.87,
    },
  },
  created_at: "2026-01-01T10:00:00Z",
};

beforeEach(() => {
  useLastResultStore.getState().clearLastResult();
});

describe("useLastResultStore", () => {
  it("initial lastResult is null", () => {
    expect(useLastResultStore.getState().lastResult).toBeNull();
  });

  it("setLastResult stores the result", () => {
    useLastResultStore.getState().setLastResult(MOCK_RESULT);
    expect(useLastResultStore.getState().lastResult).toEqual(MOCK_RESULT);
  });

  it("clearLastResult resets lastResult to null", () => {
    useLastResultStore.getState().setLastResult(MOCK_RESULT);
    useLastResultStore.getState().clearLastResult();
    expect(useLastResultStore.getState().lastResult).toBeNull();
  });

  it("setLastResult overwrites a previous result", () => {
    const other = { ...MOCK_RESULT, id: 99, global_score: 50.0 };
    useLastResultStore.getState().setLastResult(MOCK_RESULT);
    useLastResultStore.getState().setLastResult(other);
    expect(useLastResultStore.getState().lastResult?.id).toBe(99);
  });
});
