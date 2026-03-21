/**
 * @harmony/types
 *
 * TypeScript mirrors of all backend Pydantic schemas.
 * Single source of truth — generated from app/shared/enums.py
 * and all modules/{module}/schemas.py files.
 */

// ── Enums ────────────────────────────────────────────────────────────────────

export type UserRole = "candidate" | "client" | "admin" | "calibrator";

export type YachtPosition =
  // Deck
  | "Captain"
  | "First Mate"
  | "Second Officer"
  | "Bosun"
  | "Deckhand"
  // Engine
  | "Chief Engineer"
  | "2nd Engineer"
  | "3rd Engineer"
  | "ETO"
  // Interior
  | "Chief Stewardess"
  | "Stewardess"
  | "Butler"
  // Galley
  | "Chef"
  | "Sous Chef"
  // Wellness & Safety
  | "Dive Instructor"
  | "Medic";

export type YachtTypeAlpha =
  | "sailing_cruiser"
  | "sailing_racing"
  | "motor_cruiser"
  | "superyacht"
  | "megayacht"
  | "expedition"
  | "charter";

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

export type TestType = "likert" | "qcm";

/** Type d'une question individuelle (distinct du type de catalogue). */
export type QuestionType = "likert" | "qcm" | "multiple_choice" | "raven" | string;

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

export interface DimensionScoresOut {
  agreeableness?: number | null;
  conscientiousness?: number | null;
  openness?: number | null;
  extraversion?: number | null;
  emotional_stability?: number | null;
  gca?: number | null;
  resilience?: number | null;
}

export interface KeySignalOut {
  type: string; // "strength" | "risk"
  label: string;
  trait?: string | null;
}

export interface PsychometricReportOut {
  has_data: boolean;
  view_mode: string;
  context_position?: string | null;
  snapshot_version?: string | null;
  message?: string | null;
  dimensions?: DimensionScoresOut | null;
  raw_scores?: Record<string, unknown> | null;
  benchmarks?: Record<string, unknown> | null;
  test_history?: unknown[] | null;
  key_signals?: KeySignalOut[] | null;
  risk_signals?: unknown[] | null;
  work_style?: Record<string, unknown> | null;
  team_contribution?: Record<string, unknown> | null;
  communication_tips?: string[] | null;
  onboarding_tips?: Record<string, unknown> | null;
  integration_risks?: unknown[] | null;
  management_advice?: Record<string, unknown> | null;
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
  question_type: QuestionType;
  options: string[] | RavenMatrixConfig | null;
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

export interface ProfileFitOut {
  g_fit: number;
  fit_label: string;
  overall_centile: number;
  centile_by_competency: Record<string, number>;
  safety_level: string;
  safety_flags: string[];
}

export interface TeamIntegrationOut {
  available: boolean;
  y_success: number | null;
  success_label: string | null;
  p_ind: number | null;
  f_team: number | null;
  f_env: number | null;
  f_lmx: number | null;
  team_delta: number | null;
  confidence: "HIGH" | "MEDIUM" | "LOW" | null;
  reason: string | null;
}

export interface MatchResultOut {
  crew_profile_id: number;
  name: string;
  avatar_url: string | null;
  location: string | null;
  experience_years: number;
  test_status: "completed" | "pending";
  is_pipeline_pass: boolean;
  filtered_at: string | null;
  profile_fit: ProfileFitOut;
  team_integration: TeamIntegrationOut;
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
// ── RadarChart ───────────────────────────────────────────────────────

export interface RadarPoint {
  trait: string;
  label: string;
  A: number;
  B: number;
  fullMark: number;
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

// ── PE Fit Engine Results ─────────────────────────────────────────────────────

export interface POValuesDimScore {
  dimension: string;
  candidate_raw: number | null;
  environment_level: number | null;
  score: number; // PSI ∈ [0, 1]
  weight: number;
  flags: string[];
}

export interface POValuesResult {
  score: number; // ∈ [0, 100]
  dimensions: POValuesDimScore[];
  data_quality: number;
  flags: string[];
}

export interface FPhysicalDimScore {
  dimension: string;
  candidate_raw: number | null;
  environment_level: number | null;
  score: number; // PSI ∈ [0, 1]
  weight: number;
  flags: string[];
}

export interface FPhysicalResult {
  score: number; // ∈ [0, 100]
  dimensions: FPhysicalDimScore[];
  data_quality: number;
  flags: string[];
}

export interface FMobilityDimScore {
  dimension: string;
  candidate_raw: number | null;
  environment_level: number | null;
  score: number; // PSI ∈ [0, 1]
  weight: number;
  flags: string[];
}

export interface FMobilityResult {
  score: number; // ∈ [0, 100]
  dimensions: FMobilityDimScore[];
  data_quality: number;
  flags: string[];
}

/** Résultat complet PE Fit pour un candidat (endpoint /impact). */
export interface PEFitResult {
  global_score: number;
  safety_level: "CLEAR" | "ADVISORY" | "HIGH_RISK" | "DISQUALIFIED";
  is_disqualified: boolean;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  data_quality: number;
  dimension_weights: Record<string, number>;
  pj_fit: {
    score: number;
    p_ind_score: number;
    fit_label: string;
    overall_centile: number;
    ns_fit_score: number | null;
    motivation_score: number | null;
    safety: { level: string; flags: string[] };
    flags: string[];
  };
  po_fit: {
    score: number;
    jdr_ratio: number;
    jdr_status: string;
    resilience: number;
    note: string;
    flags: string[];
  } | null;
  po_values_fit: {
    score: number;
    dimensions: POValuesDimScore[];
    data_quality: number;
    flags: string[];
  } | null;
  pt_fit: {
    score: number;
    min_agreeableness: number;
    mean_es: number;
    sigma_c: number;
    crew_size: number;
    flags: string[];
  } | null;
  ps_fit: {
    score: number;
    compatibility_label: string;
    normalized_distance: number;
    dimension_gaps: Array<{
      dimension: string;
      gap: number;
      direction: string;
      label: string;
    }>;
    flags: string[];
  } | null;
  physical_fit: {
    score: number;
    dimensions: FPhysicalDimScore[];
    flags: string[];
  } | null;
  mobility_fit: {
    score: number;
    dimensions: FMobilityDimScore[];
    flags: string[];
  } | null;
  all_flags: string[];
}

// ── Calibration ───────────────────────────────────────────────────────────────

export interface CalibratorTokenOut {
  access_token: string;
  token_type: "bearer";
  calibrator_id: number;
  name: string;
}

export interface CalibratorMeOut {
  id: number;
  name: string;
  email: string;
  cohort: string | null;
  age: number | null;
  gender: string | null;
  education_level: string | null;
  occupation: string | null;
  years_experience: number | null;
  nationality: string | null;
  created_at: string;
}

export interface CalibratorDemographicsIn {
  age?: number;
  gender?: string;
  education_level?: string;
  occupation?: string;
  years_experience?: number;
  nationality?: string;
  cohort?: string;
}

export interface CalibCatalogueOut {
  id: number;
  name: string;
  description: string;
  instructions: string | null;
  test_type: string;
  question_count: number;
  estimated_minutes: number;
  is_etalon: boolean;
}

export interface CalibQuestionOut {
  id: number;
  catalogue_id: number;
  text: string;
  question_type: QuestionType;
  options: string[] | RavenMatrixConfig | null;
  trait: string | null;
  order_index: number;
}

export interface CalibSessionOut {
  id: number;
  calibrator_id: number;
  catalogue_id: number;
  status: "in_progress" | "completed";
  started_at: string;
  completed_at: string | null;
  response_count: number;
}

export interface CalibResponseItemIn {
  question_id: number;
  valeur_choisie: string;
  seconds_spent: number;
}

export interface CalibSubmitIn {
  session_id: number;
  responses: CalibResponseItemIn[];
}

export interface CalibSubmitOut {
  session_id: number;
  status: "completed";
  score: number | null;
  message: string;
}

export interface CalibTraitScoreOut {
  trait: string;
  label: string;
  score: number;
  n_items: number;
}

export interface CalibSessionScoreOut {
  session_id: number;
  catalogue_id: number;
  catalogue_name: string;
  test_type: string;
  global_score: number | null;
  traits: CalibTraitScoreOut[];
  completed_at: string;
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

// ── Harmony Matrix Reasoning Test (HMR-24) ───────────────────────────────────

/** Forme d'une cellule dans une matrice Raven. */
export type RavenShape = "circle" | "square" | "triangle" | "diamond";

/** État de remplissage d'une cellule. */
export type RavenFill = "empty" | "half" | "full";

/** Une cellule dans la grille 3×3. null = cellule manquante (à compléter). */
export interface RavenCell {
  shape: RavenShape;
  size: 1 | 2 | 3;
  fill: RavenFill;
  count: 1 | 2 | 3;
  rotation?: 0 | 90 | 180 | 270;
}

/** Une option de réponse (candidate pour compléter la matrice). */
export interface RavenAnswerOption {
  id: string; // "A" | "B" | "C" | "D" | "E" | "F"
  shape: RavenShape;
  size: 1 | 2 | 3;
  fill: RavenFill;
  count: 1 | 2 | 3;
  rotation?: 0 | 90 | 180 | 270;
}

/**
 * Configuration complète d'une question HMR-24, stockée dans Question.options (JSON).
 * La case manquante est toujours [2][2] (dernière case, bas-droite).
 */
export interface RavenMatrixConfig {
  matrix: (RavenCell | null)[][];
  answer_options: RavenAnswerOption[];
  difficulty: 1 | 2 | 3;
  rule: string;
}

