// frontend/packages/types/src/enums.ts
// TypeScript type aliases (mirrors of backend enums) + UI-facing constants.

// ── Type aliases (mirrors of backend enums) ───────────────────────────────────

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

export type CatalogueDomain =
  | "personality"
  | "cognitive"
  | "motivation"
  | "person_job"
  | "person_org"
  | "person_team"
  | "physical";

// ── UI-facing constants for calibrator forms ──────────────────────────────────
// These mirror the backend Literal constraints in app/modules/calibration/schemas.py

export const NATIONALITIES = [
  "Algérienne", "Américaine", "Argentine", "Australienne", "Brésilienne",
  "Britannique", "Canadienne", "Chinoise", "Coréenne", "Croate",
  "Danoise", "Égyptienne", "Espagnole", "Française", "Grecque",
  "Indonésien(ne)", "Indien(ne)", "Italienne", "Japonaise", "Marocaine",
  "Mexicaine", "Néerlandaise", "Néo-Zélandaise", "Norvégienne",
  "Philippin(e)", "Polonaise", "Portugaise", "Roumaine", "Russe",
  "Singapourienne", "Sud-Africaine", "Turque", "Tunisienne", "Ukrainien(ne)",
  "Autre",
] as const;
export type Nationality = (typeof NATIONALITIES)[number];

export const LANGUAGE_OPTIONS = [
  { value: "french",     label: "Français"  },
  { value: "english",    label: "Anglais"   },
  { value: "spanish",    label: "Espagnol"  },
  { value: "portuguese", label: "Portugais" },
  { value: "arabic",     label: "Arabe"     },
  { value: "mandarin",   label: "Chinois"   },
  { value: "russian",    label: "Russe"     },
  { value: "other",      label: "Autre"     },
] as const;
export type NativeLanguageValue = (typeof LANGUAGE_OPTIONS)[number]["value"];

export const GENDER_OPTIONS = [
  { value: "male",              label: "Homme"                   },
  { value: "female",            label: "Femme"                   },
  { value: "non_binary",        label: "Non-binaire"             },
  { value: "prefer_not_to_say", label: "Préfère ne pas répondre" },
] as const;
export type GenderValue = (typeof GENDER_OPTIONS)[number]["value"];

export const EDUCATION_OPTIONS = [
  { value: "below_bac",  label: "< Bac"    },
  { value: "bac",        label: "Bac"      },
  { value: "bac_plus_2", label: "Bac+2"    },
  { value: "bac_plus_3", label: "Bac+3"    },
  { value: "bac_plus_5", label: "Bac+5"    },
  { value: "phd",        label: "Doctorat" },
] as const;
export type EducationValue = (typeof EDUCATION_OPTIONS)[number]["value"];

/**
 * Calibrator maritime position options.
 * Values = YachtPosition strings (backend DIF groups by department, not individual position).
 * Departments: Deck | Engine | Interior | Galley | Wellness & Safety
 */
export const YACHT_POSITION_OPTIONS: Array<{ value: YachtPosition | "none"; label: string; department: string }> = [
  // Deck
  { value: "Captain",        label: "Captain",         department: "Deck" },
  { value: "First Mate",     label: "First Mate",      department: "Deck" },
  { value: "Second Officer", label: "Second Officer",  department: "Deck" },
  { value: "Bosun",          label: "Bosun",           department: "Deck" },
  { value: "Deckhand",       label: "Deckhand",        department: "Deck" },
  // Engine
  { value: "Chief Engineer", label: "Chief Engineer",  department: "Engine" },
  { value: "2nd Engineer",   label: "2nd Engineer",    department: "Engine" },
  { value: "3rd Engineer",   label: "3rd Engineer",    department: "Engine" },
  { value: "ETO",            label: "ETO",             department: "Engine" },
  // Interior
  { value: "Chief Stewardess", label: "Chief Stewardess", department: "Interior" },
  { value: "Stewardess",       label: "Stewardess",       department: "Interior" },
  { value: "Butler",           label: "Butler",           department: "Interior" },
  // Galley
  { value: "Chef",       label: "Chef",      department: "Galley" },
  { value: "Sous Chef",  label: "Sous Chef", department: "Galley" },
  // Wellness & Safety
  { value: "Dive Instructor", label: "Dive Instructor", department: "Wellness" },
  { value: "Medic",           label: "Medic",           department: "Wellness" },
  // No maritime background
  { value: "none", label: "Aucun", department: "" },
];
export type MaritimeRoleValue = (typeof YACHT_POSITION_OPTIONS)[number]["value"];

export const YEARS_AT_SEA_OPTIONS: Array<{ value: number; label: string }> = [
  { value: 0,  label: "0 an"    },
  { value: 1,  label: "1 an"    },
  { value: 2,  label: "2 ans"   },
  { value: 3,  label: "3 ans"   },
  { value: 5,  label: "5 ans"   },
  { value: 7,  label: "7 ans"   },
  { value: 10, label: "10 ans"  },
  { value: 15, label: "15 ans"  },
  { value: 20, label: "20 ans"  },
  { value: 25, label: "25 ans"  },
  { value: 30, label: "30+ ans" },
];

export const MMFS_TRAITS = new Set([
  "disponibilite", "geographie", "contraintes_perso", "administratif",
]);

export interface TraitMeta { label: string; description: string }

export const TRAIT_META: Record<string, TraitMeta> = {
  H: { label: "Honnêteté-Humilité",     description: "Sincérité, équité et désintéressement dans les relations." },
  E: { label: "Émotivité",              description: "Sensibilité émotionnelle, anxiété et attachement aux proches." },
  X: { label: "Extraversion",           description: "Aisance sociale, énergie et enthousiasme dans les interactions." },
  A: { label: "Agréabilité",            description: "Patience, tolérance et coopération dans les situations de tension." },
  C: { label: "Conscienciosité",        description: "Organisation, diligence et discipline dans le travail." },
  O: { label: "Ouverture",              description: "Curiosité intellectuelle, créativité et sensibilité esthétique." },
  GCA_Gf:           { label: "Intelligence fluide (GCA)",    description: "Capacité de raisonnement face à des problèmes nouveaux et non verbaux." },
  matrix_reasoning:  { label: "Raisonnement matriciel",       description: "Identification de patterns visuels et règles abstraites." },
  analogy:           { label: "Raisonnement analogique",      description: "Détection de relations logiques entre concepts." },
  induction:         { label: "Induction",                    description: "Généralisation à partir de séries et patterns observés." },
  icar_lnsr:         { label: "Raisonnement lettre-chiffre",  description: "Flexibilité mentale et mémoire de travail sur séquences mixtes." },
  icar_vr:           { label: "Raisonnement verbal",          description: "Compréhension de relations logiques exprimées en langage." },
  intrinsic:          { label: "Motivation intrinsèque",              description: "Engagement par intérêt et plaisir inhérents à l'activité." },
  identified:         { label: "Régulation identifiée",               description: "Motivation par adhésion personnelle aux valeurs du travail." },
  integrated:         { label: "Régulation intégrée",                 description: "Motivation pleinement assimilée à l'identité professionnelle." },
  introjected:        { label: "Régulation introjectée",              description: "Motivation par pression interne (culpabilité, fierté)." },
  extrinsic_material: { label: "Motivation extrinsèque (matérielle)", description: "Engagement principalement lié à la rémunération et avantages." },
  extrinsic_social:   { label: "Motivation extrinsèque (sociale)",    description: "Engagement pour la reconnaissance et l'approbation d'autrui." },
  external:           { label: "Régulation externe",                  description: "Motivation par contraintes et récompenses extérieures." },
  amotivation:        { label: "Amotivation",                         description: "Absence de motivation ou sentiment d'impuissance face à la tâche." },
  lmx_affect:               { label: "LMX — Affect",                description: "Appréciation mutuelle et lien positif avec la hiérarchie." },
  lmx_respect:              { label: "LMX — Respect",               description: "Reconnaissance professionnelle réciproque avec le manager." },
  lmx_mutual_understanding: { label: "LMX — Compréhension mutuelle",description: "Clarté des attentes et connaissance du rôle de chacun." },
  autonomy:    { label: "Préférence d'autonomie",    description: "Appétence pour l'indépendance et la prise de décision propre." },
  feedback:    { label: "Besoin de feedback",        description: "Importance accordée au retour régulier sur la performance." },
  structure:   { label: "Besoin de structure",       description: "Préférence pour des règles, procédures et cadres clairs." },
  achievement: { label: "Valeur d'accomplissement",  description: "Importance accordée au dépassement de soi et à l'excellence." },
  fairness:    { label: "Valeur d'équité",           description: "Attachement à la justice et à l'égalité de traitement." },
  helping:     { label: "Valeur d'aide",             description: "Sens du service et importance du soutien aux autres." },
  honesty:     { label: "Valeur d'honnêteté",        description: "Importance de la transparence et de l'intégrité dans le travail." },
  gse:         { label: "Auto-efficacité générale",  description: "Confiance en sa capacité à faire face aux défis et obstacles." },
  climat:       { label: "Tolérance climatique",      description: "Confort dans des environnements froids, chauds ou instables." },
  confinement:  { label: "Tolérance au confinement",  description: "Capacité à travailler dans des espaces restreints sur la durée." },
  houle:        { label: "Tolérance à la houle",      description: "Adaptation aux mouvements du navire et instabilité du plancher." },
  isolement:    { label: "Tolérance à l'isolement",   description: "Résistance psychologique aux périodes d'éloignement prolongé." },
  mal_de_mer:   { label: "Résistance au mal de mer",  description: "Sensibilité aux nausées et désorientation liées au mouvement marin." },
  sommeil:      { label: "Qualité du sommeil en mer", description: "Capacité à récupérer dans un environnement de travail par quarts." },
  disponibilite:     { label: "Disponibilité",                description: "" },
  geographie:        { label: "Zone géographique",            description: "" },
  contraintes_perso: { label: "Contraintes personnelles",     description: "" },
  administratif:     { label: "Contraintes administratives",  description: "" },
};
