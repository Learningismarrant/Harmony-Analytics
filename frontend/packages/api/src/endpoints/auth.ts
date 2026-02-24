import type {
  TokenOut,
  AccessTokenOut,
  RegisterCrewIn,
  RegisterEmployerIn,
  ChangePasswordIn,
} from "@harmony/types";
import { post, get } from "../client";

export const authApi = {
  /** Register a new candidate */
  registerCrew: (body: RegisterCrewIn) =>
    post<TokenOut>("/auth/register/crew", body),

  /** Register a new employer */
  registerEmployer: (body: RegisterEmployerIn) =>
    post<TokenOut>("/auth/register/employer", body),

  /** Login — returns access_token + refresh_token in JSON body */
  login: (email: string, password: string) =>
    post<TokenOut>("/auth/login", { email, password }),

  /** Refresh access token — refresh_token passed in body */
  refresh: (refreshToken: string) =>
    post<AccessTokenOut>("/auth/refresh", { refresh_token: refreshToken }),

  /** Get current user identity */
  me: () => get<{ id: number; email: string; role: string; name: string }>("/auth/me"),

  /** Logout — client clears tokens */
  logout: () => post<void>("/auth/logout"),

  /** Change password */
  changePassword: (body: ChangePasswordIn) =>
    post<void>("/auth/change-password", body),
};
