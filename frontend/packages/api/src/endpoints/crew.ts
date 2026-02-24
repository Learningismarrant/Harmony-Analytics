import type {
  DashboardOut,
  SociogramOut,
  CrewAssignIn,
  DailyPulseIn,
} from "@harmony/types";
import { get, post, del } from "../client";

export const crewApi = {
  /** Get crew dashboard — harmony metrics + diagnosis + sociogram */
  getDashboard: (yachtId: number) =>
    get<DashboardOut>(`/crew/${yachtId}/dashboard`),

  /** Get sociogram data for 3D visualization */
  getSociogram: (yachtId: number) =>
    get<SociogramOut>(`/crew/${yachtId}/sociogram`),

  /** Assign a crew member */
  assignMember: (yachtId: number, body: CrewAssignIn) =>
    post<void>(`/crew/${yachtId}/members`, body),

  /** Remove a crew member */
  removeMember: (yachtId: number, crewProfileId: number) =>
    del(`/crew/${yachtId}/members/${crewProfileId}`),

  /** Submit a daily pulse (1–5) */
  submitPulse: (body: DailyPulseIn) =>
    post<void>("/crew/pulse", body),

  /** Get current assignment info */
  getMyAssignment: () => get<{ yacht_id: number; role: string } | null>("/crew/me/assignment"),
};
