import type {
  FullCrewProfileOut,
  UserIdentityOut,
  IdentityUpdateIn,
  ExperienceCreateIn,
  ExperienceOut,
} from "@harmony/types";
import { get, patch, post } from "../client";

export const identityApi = {
  /** Get full profile (context-aware: candidate / manager / recruiter) */
  getFullProfile: (crewProfileId: number) =>
    get<FullCrewProfileOut>(`/identity/candidate/${crewProfileId}`),

  /** Get just the identity section */
  getIdentity: (crewProfileId: number) =>
    get<UserIdentityOut>(`/identity/candidate/${crewProfileId}/identity`),

  /** Update own identity */
  updateMe: (body: IdentityUpdateIn) =>
    patch<UserIdentityOut>("/identity/me", body),

  /** Add a new experience entry */
  addExperience: (body: ExperienceCreateIn) =>
    post<ExperienceOut>("/identity/me/experiences", body),
};
