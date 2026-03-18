import type {
  FullCrewProfileOut,
  UserIdentityOut,
  IdentityUpdateIn,
  ExperienceCreateIn,
  ExperienceOut,
  PsychometricReportOut,
} from "@harmony/types";
import { get, patch, post } from "../client";

export const identityApi = {
  /** Get full profile (context-aware: candidate / manager / recruiter) */
  getFullProfile: (crewProfileId: number) =>
    get<FullCrewProfileOut>(`/identity/candidate/${crewProfileId}`),

  /** Get just the identity section */
  getIdentity: (crewProfileId: number) =>
    get<UserIdentityOut>(`/identity/candidate/${crewProfileId}/identity`),

  /** Get psychometric report for a crew profile */
  getReports: (crewProfileId: number) =>
    get<PsychometricReportOut>(`/identity/candidate/${crewProfileId}/reports`),

  /** Update own identity */
  updateMe: (body: IdentityUpdateIn) =>
    patch<UserIdentityOut>("/identity/me", body),

  /** Add a new experience entry */
  addExperience: (body: ExperienceCreateIn) =>
    post<ExperienceOut>("/identity/me/experiences", body),
};
