import type {
  CampaignOut,
  CampaignCreateIn,
  MatchResultOut,
  SimulationPreviewOut,
} from "@harmony/types";
import { get, post, patch, del } from "../client";

export const recruitmentApi = {
  /** List employer's campaigns */
  getCampaigns: () => get<CampaignOut[]>("/recruitment/campaigns"),

  /** Create a new campaign */
  createCampaign: (body: CampaignCreateIn) =>
    post<CampaignOut>("/recruitment/campaigns", body),

  /** Get campaign details */
  getCampaign: (id: number) => get<CampaignOut>(`/recruitment/campaigns/${id}`),

  /** Archive a campaign */
  archiveCampaign: (id: number) =>
    patch<CampaignOut>(`/recruitment/campaigns/${id}/archive`),

  /** Delete a campaign */
  deleteCampaign: (id: number) =>
    del(`/recruitment/campaigns/${id}`),

  /** Get matching results — runs DNRE + MLPSM pipeline */
  getMatching: (campaignId: number) =>
    get<MatchResultOut[]>(`/recruitment/campaigns/${campaignId}/matching`),

  /** Simulate adding a candidate to a yacht — delta sociogram preview */
  simulateImpact: (yachtId: number, crewProfileId: number) =>
    get<SimulationPreviewOut>(
      `/crew/${yachtId}/simulate/${crewProfileId}`,
    ),

  /** Hire a candidate */
  hire: (campaignId: number, crewProfileId: number) =>
    post<void>(`/recruitment/campaigns/${campaignId}/hire/${crewProfileId}`),

  /** Reject a candidate */
  reject: (
    campaignId: number,
    crewProfileId: number,
    reason?: string,
  ) =>
    post<void>(
      `/recruitment/campaigns/${campaignId}/reject/${crewProfileId}`,
      { rejected_reason: reason },
    ),
};
