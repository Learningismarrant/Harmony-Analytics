import type { SurveyOut, SurveyResponseIn, SurveyResponseOut } from "@harmony/types";
import { get, post } from "../client";

export const surveyApi = {
  /** Surveys en attente pour le marin connecté */
  getPending: () => get<SurveyOut[]>("/surveys/pending"),

  /** Soumet une réponse à un survey */
  respond: (surveyId: number, body: SurveyResponseIn) =>
    post<SurveyResponseOut>(`/surveys/${surveyId}/respond`, body),
};
