import type {
  CalibratorTokenOut,
  CalibratorMeOut,
  CalibratorDemographicsIn,
  CalibCatalogueOut,
  CalibQuestionOut,
  CalibSessionOut,
  CalibSubmitIn,
  CalibSubmitOut,
  CalibSessionScoreOut,
} from "@harmony/types";
import { get, post, patch } from "../client";

export const calibrationApi = {
  /** Login calibrateur — retourne un access token (pas de refresh) */
  login: (email: string, password: string) =>
    post<CalibratorTokenOut>("/calibration/auth/login", { email, password }),

  /** Register calibrateur */
  register: (body: {
    email: string;
    name: string;
    password: string;
    cohort?: string;
  }) => post<CalibratorTokenOut>("/calibration/auth/register", body),

  /** Profil du calibrateur connecté */
  getMe: () => get<CalibratorMeOut>("/calibration/me"),

  /** Mettre à jour les données démographiques */
  updateDemographics: (body: CalibratorDemographicsIn) =>
    patch<CalibratorMeOut>("/calibration/me", body),

  /** Catalogue de tests disponibles */
  getCatalogues: () => get<CalibCatalogueOut[]>("/calibration/catalogues"),

  /** Questions d'un catalogue */
  getQuestions: (catalogueId: number) =>
    get<CalibQuestionOut[]>(`/calibration/catalogues/${catalogueId}/questions`),

  /** Démarrer une session (ou récupérer la session en cours) */
  startSession: (catalogueId: number) =>
    post<CalibSessionOut>("/calibration/sessions", { catalogue_id: catalogueId }),

  /** Toutes les sessions du calibrateur connecté */
  getSessions: () => get<CalibSessionOut[]>("/calibration/sessions"),

  /** Soumettre toutes les réponses d'une session */
  submitResponses: (sessionId: number, body: CalibSubmitIn) =>
    post<CalibSubmitOut>(`/calibration/sessions/${sessionId}/responses`, body),

  /** Score d'une session terminée */
  getSessionScore: (sessionId: number) =>
    get<CalibSessionScoreOut>(`/calibration/sessions/${sessionId}/score`),
};

// ── Query key factories ───────────────────────────────────────────────────────

export const calibrationQueryKeys = {
  me: () => ["calibration", "me"] as const,
  catalogues: () => ["calibration", "catalogues"] as const,
  questions: (catalogueId: number) =>
    ["calibration", "questions", catalogueId] as const,
  sessions: () => ["calibration", "sessions"] as const,
  sessionScore: (sessionId: number) =>
    ["calibration", "session", "score", sessionId] as const,
};
