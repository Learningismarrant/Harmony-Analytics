/**
 * @harmony/api
 *
 * API client layer — do not import platform-specific code here.
 * Platform-specific hooks (React / React Native) live in the apps.
 */

export {
  apiClient,
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  setRefreshTokenProvider,
} from "./client";
export { authApi } from "./endpoints/auth";
export { assessmentApi } from "./endpoints/assessment";
export { recruitmentApi } from "./endpoints/recruitment";
export { crewApi } from "./endpoints/crew";
export { vesselApi } from "./endpoints/vessel";
export { identityApi } from "./endpoints/identity";
export { surveyApi } from "./endpoints/survey";

// ── Query key factories — centralized for cache invalidation ──────────────────
// Pattern: queryKeys.module.action(params)

export const queryKeys = {
  auth: {
    me: () => ["auth", "me"] as const,
  },
  assessment: {
    catalogue: () => ["assessment", "catalogue"] as const,
    questions: (testId: number) => ["assessment", "questions", testId] as const,
    myResults: () => ["assessment", "results", "me"] as const,
    candidateResults: (id: number) => ["assessment", "results", id] as const,
  },
  recruitment: {
    campaigns: () => ["recruitment", "campaigns"] as const,
    campaign: (id: number) => ["recruitment", "campaign", id] as const,
    matching: (campaignId: number) =>
      ["recruitment", "matching", campaignId] as const,
    simulation: (yachtId: number, crewProfileId: number) =>
      ["recruitment", "simulation", yachtId, crewProfileId] as const,
  },
  crew: {
    dashboard: (yachtId: number) => ["crew", "dashboard", yachtId] as const,
    sociogram: (yachtId: number) => ["crew", "sociogram", yachtId] as const,
    assignment: () => ["crew", "assignment"] as const,
    pulseHistory: () => ["crew", "pulse", "history"] as const,
  },
  vessel: {
    all: () => ["vessel", "all"] as const,
    byId: (id: number) => ["vessel", id] as const,
  },
  identity: {
    fullProfile: (id: number) => ["identity", "profile", id] as const,
    identity: (id: number) => ["identity", "identity", id] as const,
  },
  survey: {
    pending: () => ["survey", "pending"] as const,
  },
} as const;
