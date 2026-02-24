import type {
  YachtOut,
  YachtCreateIn,
  YachtEnvironmentUpdateIn,
} from "@harmony/types";
import { get, post, patch } from "../client";

export const vesselApi = {
  /** List all yachts for the current employer */
  getAll: () => get<YachtOut[]>("/vessels/"),

  /** Create a new yacht */
  create: (body: YachtCreateIn) => post<YachtOut>("/vessels/", body),

  /** Get yacht details */
  getById: (id: number) => get<YachtOut>(`/vessels/${id}`),

  /** Update JD-R environment parameters */
  updateEnvironment: (id: number, body: YachtEnvironmentUpdateIn) =>
    patch<void>(`/vessels/${id}/environment`, body),

  /** Get the secure boarding token */
  getBoardingToken: (id: number) =>
    get<{ id: number; name: string; boarding_token: string }>(
      `/vessels/${id}/boarding-token`,
    ),
};
