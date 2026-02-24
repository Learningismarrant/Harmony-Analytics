/**
 * @harmony/types
 *
 * TypeScript mirrors of all backend Pydantic schemas.
 * Single source of truth — generated from app/shared/enums.py
 * and all modules/*/schemas.py files.
 */

// ── Enums ────────────────────────────────────────────────────────────────────

export type UserRole = "candidate" | "client" | "admin";

export type YachtPosition =
  | "Captain"
  | "First Mate"
  | "Bosun"
  | "Deckhand"
  | "Chief Engineer"
  | "2nd Engineer"
  | "Chief Stewardess"
  | "Stewardess"
  | "Chef";

export type AvailabilityStatus = "available" | "on_board" | "unavailable" | "soon";

export type CampaignStatus = "open" | "closed" | "draft";

export type ApplicationStatus = "pending" | "hired" | "rejected" | "joined";

export type SurveyTriggerType =
  | "post_charter"
  | "post_season"
  | "monthly_pulse"
  | "conflict_event"
  | "exit_interview";

export type DepartureReason =
  | "performance"
  | "team_conflict"
  | "environment"
  | "leadership"
  | "external"
  | "unknown";

export type TestType = "likert" | "cognitive" | "free";

export type NiveauScore = "Faible" | "Moyen" | "Élevé";

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenOut {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  role: UserRole;
  user_id: number;
  profile_id: number; // crew_profile.id ou employer_profile.id selon le rôle
}

export interface AccessTokenOut {
  access_token: string;
  token_type: "bearer";
}

export interface RegisterCrewIn {
  email: string;
  password: string;
  name: string;
  position_targeted?: YachtPosition;
  experience_years?: number;
  phone?: string;
  location?: string;
}

export interface RegisterEmployerIn {
  email: string;
  password: string;
  name: string;
  company_name?: string;
  phone?: string;
  location?: string;
}

export interface LoginIn {
  email: string;
  password: string;
}

export interface ChangePasswordIn {
  current_password: string;
  new_password: string;
}

// ── Identity ─────────────────────────────────────────────────────────────────

export interface UserIdentityOut {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  avatar_url: string | null;
  location: string | null;
  is_harmony_verified: boolean;
  is_active: boolean;
  created_at: string; // ISO datetime
}

export interface IdentityUpdateIn {
  name?: string;
  phone?: string;
  location?: string;
}

export interface CrewProfileSummary {
  id: number;
  user_id: number;
  position_targeted: YachtPosition;
  experience_years: number;
  availability_status: AvailabilityStatus;
}

export interface ExperienceOut {
  id: number;
  yacht_name: string;
  role: YachtPosition | string;
  start_date: string;
  end_date: string | null;
  is_harmony_approved: boolean;
  reference_comment: string | null;
  candidate_comment: string | null;
  contract_type: string | null;
}

export interface ExperienceCreateIn {
  yacht_id?: number;
  external_yacht_name?: string;
  role: YachtPosition | string;
  start_date: string; // ISO date
  end_date?: string;
  contract_type?: string;
  candidate_comment?: string;
}

export interface AccessContextOut {
  view_mode: "candidate" | "manager" | "recruiter";
  label: string;
  context_position: YachtPosition | null;
  is_active_crew: boolean;
}

export interface FullCrewProfileOut {
  context: AccessContextOut;
  identity: UserIdentityOut;
  crew: CrewProfileSummary;
  experiences: ExperienceOut[];
  documents: DocumentOut[];
  reports: PsychometricReportOut[];
}

export interface DocumentOut {
  id: number;
  title: string;
  document_type: string;
  file_url: string;
  uploaded_at: string;
}

export interface PsychometricReportOut {
  test_name: string;
  global_score: number;
  created_at: string;
  summary: Record<string, unknown>;
}

// ── Assessment ────────────────────────────────────────────────────────────────

export interface TestInfoOut {
  id: number;
  name: string;
  description: string;
  instructions: string | null;
  max_score_per_question: number;
  test_type: TestType;
}

export interface QuestionOut {
  id: number;
  test_id: number;
  text: string;
  question_type: TestType;
  options: string[] | null;
  trait: string | null;
}

export interface ResponseIn {
  question_id: number;
  valeur_choisie: string;
  seconds_spent?: number;
}

export interface SubmitTestIn {
  test_id: number;
  responses: ResponseIn[];
}

export interface TraitScoreOut {
  score: number;
  niveau: NiveauScore;
  percentile?: number;
}

export interface ReliabilityOut {
  is_reliable: boolean;
  reasons: string[];
  social_desirability_flag: boolean;
}

export interface TestResultOut {
  id: number;
  test_id: number;
  crew_profile_id: number;
  test_name: string;
  global_score: number;
  scores: {
    traits?: Record<string, TraitScoreOut>;
    reliability?: ReliabilityOut;
    global_score?: number;
    meta?: {
      total_time_seconds: number;
      avg_seconds_per_question: number;
    };
  };
  created_at: string;
}

// ── Vessel ────────────────────────────────────────────────────────────────────

export interface YachtOut {
  id: number;
  name: string;
  type: string;
  length: number | null;
  employer_profile_id: number;
  boarding_token: string;
  created_at: string;
}

export interface YachtCreateIn {
  name: string;
  type: string;
  length?: number;
}

export interface YachtEnvironmentUpdateIn {
  charter_intensity?: number;
  management_pressure?: number;
  salary_index?: number;
  rest_days_ratio?: number;
  private_cabin_ratio?: number;
  captain_autonomy_given?: number;
  captain_feedback_style?: number;
  captain_structure_imposed?: number;
}

// ── Recruitment ───────────────────────────────────────────────────────────────

export interface CampaignOut {
  id: number;
  title: string;
  position: string;
  description: string | null;
  status: CampaignStatus;
  yacht_id: number | null;
  yacht_name: string | null;
  invite_token: string;
  is_archived: boolean;
  candidate_count: number;
  created_at: string;
}

export interface CampaignCreateIn {
  title: string;
  position: string;
  description?: string;
  yacht_id: number;
}

export interface MatchResultOut {
  crew_profile_id: number;
  name: string;
  avatar_url: string | null;
  location: string | null;
  experience_years: number;
  test_status: "completed" | "pending";
  global_fit: number;
  y_success: number;
  f_team_delta: number;
  impact_flags: string[];
  confidence: "HIGH" | "MEDIUM" | "LOW";
  is_hired: boolean;
  is_rejected: boolean;
  application_status: ApplicationStatus;
  rejected_reason: string | null;
}

// ── Crew / Dashboard ──────────────────────────────────────────────────────────

export interface CrewAssignIn {
  crew_profile_id: number;
  role: YachtPosition;
}

export interface DailyPulseIn {
  score: number; // 1–5
  comment?: string;
}

export interface HarmonyMetrics {
  performance_index: number; // F_team score
  cohesion_index: number;
  stability_index: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  data_quality: number;
}

export interface DiagnosisOut {
  diagnosis_type: string;
  label: string;
  description: string;
  recommendations: string[];
  risk_level: "LOW" | "MEDIUM" | "HIGH";
}

export interface DashboardOut {
  yacht_id: number;
  crew_count: number;
  harmony_metrics: HarmonyMetrics;
  diagnosis: DiagnosisOut | null;
  weather_trend: "improving" | "stable" | "degrading" | "unknown";
  sociogram: SociogramOut | null;
}

// ── Sociogram / Matrice ───────────────────────────────────────────────────────

export interface SociogramNode {
  crew_profile_id: number;
  name: string;
  avatar_url: string | null;
  position: YachtPosition | string;
  psychometric_completeness: number; // 0–1
  p_ind: number; // Individual performance score 0–100
}

export interface SociogramEdge {
  source_id: number;
  target_id: number;
  dyad_score: number; // 0–100 compatibility
  agreeableness_compatibility: number;
  conscientiousness_compatibility: number;
  es_compatibility: number;
  risk_flags: string[];
}

export interface SociogramOut {
  nodes: SociogramNode[];
  edges: SociogramEdge[];
  f_team_global: number;
  computed_at: string;
}

export interface SimulationPreviewOut {
  candidate_id: number;
  candidate_name: string;
  delta_f_team: number; // positive = improvement
  delta_cohesion: number;
  new_edges: SociogramEdge[];
  impact_flags: string[];
  recommendation: "STRONG_FIT" | "MODERATE_FIT" | "WEAK_FIT" | "RISK";
}

// ── Survey ────────────────────────────────────────────────────────────────────

export interface SurveyOut {
  id: number;
  yacht_id: number;
  trigger_type: SurveyTriggerType;
  target_crew_ids: number[];
  is_open: boolean;
  created_at: string;
  closed_at: string | null;
  response_count: number;
}

export interface SurveyResponseIn {
  team_cohesion?: number; // 1–10
  workload_felt?: number;
  leadership_fit?: number;
  self_performance?: number;
  intent_to_stay: number; // required
  free_text?: string;
  departure_reason?: DepartureReason;
  actual_tenure_days?: number;
}

export interface SurveyAggregatedOut {
  survey_id: number;
  trigger_type: SurveyTriggerType;
  response_count: number;
  avg_team_cohesion: number | null;
  avg_workload_felt: number | null;
  avg_leadership_fit: number | null;
  avg_intent_to_stay: number | null;
  predicted_vs_observed: Record<string, unknown> | null;
}

// ── API response wrappers ─────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status: number;
}

export interface PaginatedOut<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
