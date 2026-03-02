import { create } from "zustand";
import type { TestResultOut } from "@harmony/types";

interface LastResultState {
  lastResult: TestResultOut | null;
  setLastResult: (result: TestResultOut) => void;
  clearLastResult: () => void;
}

export const useLastResultStore = create<LastResultState>()((set) => ({
  lastResult: null,
  setLastResult: (result) => set({ lastResult: result }),
  clearLastResult: () => set({ lastResult: null }),
}));
