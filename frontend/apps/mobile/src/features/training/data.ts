// ─────────────────────────────────────────────────────────────────
// HARMONY TRAINING — Mock data layer
// TODO: replace with API calls once backend training module is built
// All content is asynchronous / self-paced — zero human coaching.
// ─────────────────────────────────────────────────────────────────

export type ExperienceLevel = "junior" | "mid" | "senior";
export type ModuleType = "lesson" | "exercise" | "checklist" | "self_assessment";
export type ModuleStatus = "completed" | "in_progress" | "available" | "locked";

// ── Content types ─────────────────────────────────────────────────

export type LessonSection = { title: string; body: string };
export type ExerciseStep = {
  number: number;
  title: string;
  description: string;
  estimated_min: number;
};
export type ChecklistCategory = { category: string; items: string[] };
export type SelfAssessmentQuestion = {
  id: string;
  text: string;
  scale_low: string;
  scale_high: string;
};

export type LessonContent = { sections: LessonSection[] };
export type ExerciseContent = {
  objective: string;
  steps: ExerciseStep[];
  debrief: string;
};
export type ChecklistContent = {
  intro: string;
  categories: ChecklistCategory[];
  downloadable: boolean;
};
export type SelfAssessmentContent = {
  intro: string;
  questions: SelfAssessmentQuestion[];
};
export type ModuleContent =
  | { type: "lesson"; data: LessonContent }
  | { type: "exercise"; data: ExerciseContent }
  | { type: "checklist"; data: ChecklistContent }
  | { type: "self_assessment"; data: SelfAssessmentContent };

// ── Core types ────────────────────────────────────────────────────

export type TrainingModule = {
  id: string;
  axe_id: string;
  title: string;
  subtitle: string;
  type: ModuleType;
  duration_min: number;
  levels: ExperienceLevel[];
  status: ModuleStatus;
  trigger_description: string | null;
  points: number;
  content: ModuleContent;
};

export type TrainingAxe = {
  id: string;
  title: string;
  subtitle: string;
  icon: string;
  color: string;
  trigger_description: string;
  modules: TrainingModule[];
};

export type PersonalizedPath = {
  level: ExperienceLevel;
  level_label: string;
  level_description: string;
  path_name: string;
  current_module_id: string;
  queued_module_ids: string[];
  global_completion_pct: number;
  trigger_summary: string;
};

// ── Axes & modules mock data ──────────────────────────────────────

export const TRAINING_AXES: TrainingAxe[] = [
  // ── AXE 1 — Excellence opérationnelle ─────────────────────────
  {
    id: "operational",
    title: "Excellence opérationnelle",
    subtitle: "Protocols · Safety · Seamanship",
    icon: "⚙",
    color: "#A67C52",
    trigger_description:
      "Triggered when Conscientiousness (T-IRT) < 75 or experience < 3 years",
    modules: [
      {
        id: "op-01",
        axe_id: "operational",
        title: "Protocoles de sécurité MOB",
        subtitle: "Man Overboard — Procédures & réflexes",
        type: "lesson",
        duration_min: 12,
        levels: ["junior", "mid"],
        status: "completed",
        trigger_description: "Recommended for all crew under 3 years",
        points: 50,
        content: {
          type: "lesson",
          data: {
            sections: [
              {
                title: "Pourquoi le MOB reste une priorité",
                body: "Malgré les équipements modernes, l'homme à la mer représente encore la première cause de décès en mer de plaisance. Chaque membre d'équipage doit maîtriser les 30 premières secondes de réaction — avant que le capitaine prenne le commandement.",
              },
              {
                title: "Le principe des 3 V",
                body: "Voir — Signaler — Récupérer. Dès qu'un MOB est détecté : (1) crier 'HOMME À LA MER', pointer continuellement, (2) lancer la bouée, activer le MOB GPS, (3) communiquer VHF canal 16.",
              },
              {
                title: "Les 3 manœuvres à connaître",
                body: "Demi-tour Williamson (fort vent), Scharnow (visibilité limitée), Retour immédiat (conditions calmes). En pratique à bord, votre capitaine choisit. Vous devez exécuter sans questionnement.",
              },
              {
                title: "Ce que vous faites en 30 secondes",
                body: "Pointer sans relâche. Ne jamais quitter la victime des yeux. Lancer la bouée fer à cheval. Déclencher le MOB sur le GPS de bord. Prévenir la timonerie. Tout le reste vient après.",
              },
            ],
          },
        },
      },
      {
        id: "op-02",
        axe_id: "operational",
        title: "Maintenance préventive du pont",
        subtitle: "Routine, check-lists et priorisation",
        type: "exercise",
        duration_min: 20,
        levels: ["junior", "mid"],
        status: "completed",
        trigger_description: null,
        points: 75,
        content: {
          type: "exercise",
          data: {
            objective:
              "Établir une routine de maintenance préventive pour votre zone de responsabilité à bord, en priorisant selon la criticité et la visibilité.",
            steps: [
              {
                number: 1,
                title: "Cartographier votre zone",
                description:
                  "Listez tous les éléments dans votre zone de responsabilité (pont, winches, lignes de vie, bossoirs, housses...). Incluez ce qui est habituellement négligé.",
                estimated_min: 5,
              },
              {
                number: 2,
                title: "Classer par criticité",
                description:
                  "Attribuez A/B/C à chaque élément : A = sécurité directe, B = opérationnel, C = esthétique. La règle : les A ne peuvent jamais être reportés.",
                estimated_min: 5,
              },
              {
                number: 3,
                title: "Estimer les fréquences",
                description:
                  "Quotidien / hebdomadaire / mensuel. Tenez compte du mouillage vs passage vs transit. La fréquence doit être réaliste pour être tenue.",
                estimated_min: 5,
              },
              {
                number: 4,
                title: "Formaliser votre check-list",
                description:
                  "Rédigez votre check-list en 3 colonnes : élément, fréquence, dernier fait. Elle sera votre outil de passation de quart.",
                estimated_min: 5,
              },
            ],
            debrief:
              "Une check-list réaliste vaut mieux qu'un protocole idéal ignoré. Partagez votre version avec votre chef de pont lors du prochain quart.",
          },
        },
      },
      {
        id: "op-03",
        axe_id: "operational",
        title: "Briefing équipage efficace",
        subtitle: "Structure, posture et clarté",
        type: "lesson",
        duration_min: 10,
        levels: ["mid", "senior"],
        status: "completed",
        trigger_description: "Triggered when position_targeted includes management roles",
        points: 50,
        content: {
          type: "lesson",
          data: {
            sections: [
              {
                title: "Le briefing en 5 minutes — cadre mental",
                body: "Un briefing n'est pas une réunion. C'est une transmission d'intention. Chaque participant doit repartir avec une seule question répondue : que dois-je faire précisément dans les 4 prochaines heures ?",
              },
              {
                title: "Structure SBAR adaptée au nautisme",
                body: "Situation (où en sommes-nous), Background (contexte météo/nav), Assessment (risques identifiés), Recommendation (mission de chacun). 5 minutes maximum.",
              },
            ],
          },
        },
      },
      {
        id: "op-04",
        axe_id: "operational",
        title: "Gestion des watch lists",
        subtitle: "Organisation des quarts et passation",
        type: "checklist",
        duration_min: 8,
        levels: ["mid", "senior"],
        status: "in_progress",
        trigger_description: null,
        points: 40,
        content: {
          type: "checklist",
          data: {
            intro:
              "Une passation de quart non structurée est la première cause d'accident par inattention. Cette check-list couvre les points minimaux à transmettre à votre successeur.",
            downloadable: true,
            categories: [
              {
                category: "Navigation & position",
                items: [
                  "Cap actuel et prochain waypoint",
                  "Vitesse sur fond vs vitesse surface",
                  "Alertes ARPA actives",
                  "Dernière mise à jour météo (heure + source)",
                  "Zones de mouillage ou trafic sur la route",
                ],
              },
              {
                category: "Systèmes & moteurs",
                items: [
                  "Niveau carburant (réservoirs principaux + journalier)",
                  "Heures moteur depuis dernier service",
                  "Alarmes actives ou silenciées (pourquoi ?)",
                  "Etat des batteries (banque principale + démarrage)",
                ],
              },
              {
                category: "Équipage & passagers",
                items: [
                  "Situation des passagers (cabines occupées, sorties nocturnes ?)",
                  "Crew en repos — à ne pas déranger avant quelle heure",
                  "Problèmes de santé signalés dans les 12 dernières heures",
                  "Tâches en cours non finalisées",
                ],
              },
            ],
          },
        },
      },
      {
        id: "op-05",
        axe_id: "operational",
        title: "Passage d'autorité et relève de quart",
        subtitle: "CRM et communication verticale",
        type: "lesson",
        duration_min: 15,
        levels: ["senior"],
        status: "locked",
        trigger_description: "Unlocked after completing op-04",
        points: 60,
        content: {
          type: "lesson",
          data: { sections: [] }, // placeholder
        },
      },
      {
        id: "op-06",
        axe_id: "operational",
        title: "Auto-évaluation — Sécurité opérationnelle",
        subtitle: "Évaluez votre niveau actuel",
        type: "self_assessment",
        duration_min: 7,
        levels: ["junior", "mid", "senior"],
        status: "locked",
        trigger_description: "Available after completing 4 operational modules",
        points: 30,
        content: {
          type: "self_assessment",
          data: {
            intro:
              "Cette auto-évaluation n'a pas de bonnes ou mauvaises réponses. Elle calibre les modules suivants à votre niveau réel.",
            questions: [
              {
                id: "op-sa-1",
                text: "Lors d'un MOB, à quelle vitesse initiez-vous la manœuvre de récupération ?",
                scale_low: "J'attends les ordres",
                scale_high: "Je démarre immédiatement",
              },
              {
                id: "op-sa-2",
                text: "Votre check-list de passation de quart est-elle formalisée ?",
                scale_low: "Tout est en mémoire",
                scale_high: "Document écrit et à jour",
              },
            ],
          },
        },
      },
    ],
  },

  // ── AXE 2 — Leadership maritime ───────────────────────────────
  {
    id: "leadership",
    title: "Leadership maritime",
    subtitle: "Command · Team · Decision",
    icon: "⚓",
    color: "#5A8279",
    trigger_description:
      "Triggered when Extraversion (T-IRT) < 65 or position_targeted is Captain/First Mate/Chief",
    modules: [
      {
        id: "lead-01",
        axe_id: "leadership",
        title: "Fondamentaux du commandement",
        subtitle: "Autorité, légitimité et confiance",
        type: "lesson",
        duration_min: 15,
        levels: ["mid", "senior"],
        status: "completed",
        trigger_description: "Recommended for First Mate and above",
        points: 60,
        content: {
          type: "lesson",
          data: {
            sections: [
              {
                title: "L'autorité ne se décrète pas",
                body: "En mer, un titre ne suffit pas. L'équipage suit celui qui est compétent, prévisible et calme sous pression. L'autorité maritime se construit par la cohérence entre ce qu'on dit et ce qu'on fait — et ça se joue dans les 48 premières heures à bord.",
              },
              {
                title: "Les 3 sources de légitimité à bord",
                body: "Technique (vous maîtrisez le bateau), Relationnel (vous respectez l'équipage), Situationnel (vous gérez la crise sans paniquer). Les meilleurs capitaines sont forts sur les 3. La majorité en a 1 ou 2 — l'objectif est d'identifier lequel vous manque.",
              },
            ],
          },
        },
      },
      {
        id: "lead-02",
        axe_id: "leadership",
        title: "Communication sous pression",
        subtitle: "Assertion, écoute et désescalade",
        type: "exercise",
        duration_min: 25,
        levels: ["mid", "senior"],
        status: "in_progress",
        trigger_description:
          "Triggered: T-IRT Extraversion = 62 (below threshold 65)",
        points: 100,
        content: {
          type: "exercise",
          data: {
            objective:
              "Identifier votre style de communication dominant sous pression et pratiquer les techniques CRM (Crew Resource Management) pour maintenir l'efficacité collective en situation dégradée.",
            steps: [
              {
                number: 1,
                title: "Diagnostic — votre style sous stress",
                description:
                  "Rappelez-vous la dernière situation tendue à bord. Avez-vous eu tendance à (a) vous taire et attendre, (b) prendre toutes les décisions seul, ou (c) consulter trop longtemps avant d'agir ? Notez votre réponse — elle sera votre point de départ.",
                estimated_min: 5,
              },
              {
                number: 2,
                title: "Le modèle PACE",
                description:
                  "Probe (sonder), Alert (alerter), Challenge (challenger), Emergency (urgence). Utilisé dans l'aviation civile et repris en navigation commerciale. Apprenez les 4 niveaux et notez un exemple personnel pour chacun.",
                estimated_min: 8,
              },
              {
                number: 3,
                title: "Scénario pratique : désaccord avec le capitaine",
                description:
                  "Situation : vous êtes First Mate, le capitaine décide d'entrer dans un mouillage malgré une météo dégradante. Vous avez des doutes. Rédigez exactement ce que vous diriez — en utilisant le niveau PACE approprié. Soyez direct, respectueux, factuel.",
                estimated_min: 7,
              },
              {
                number: 4,
                title: "Debrief en solo",
                description:
                  "Relisez ce que vous avez écrit. Est-ce que vous le diriez vraiment ? Qu'est-ce qui vous retient ? Notez les 2 obstacles principaux — culturels, hiérarchiques, ou liés à votre personnalité.",
                estimated_min: 5,
              },
            ],
            debrief:
              "Le CRM maritime ne cherche pas à supprimer la hiérarchie — il cherche à s'assurer que l'information critique remonte toujours, même sous pression. C'est une compétence qui s'entraîne.",
          },
        },
      },
      {
        id: "lead-03",
        axe_id: "leadership",
        title: "Gestion des conflits à bord",
        subtitle: "Médiation en espace confiné",
        type: "lesson",
        duration_min: 18,
        levels: ["mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing lead-02",
        points: 70,
        content: { type: "lesson", data: { sections: [] } },
      },
      {
        id: "lead-04",
        axe_id: "leadership",
        title: "Délégation et confiance",
        subtitle: "Lâcher prise sans perdre le contrôle",
        type: "checklist",
        duration_min: 10,
        levels: ["senior"],
        status: "locked",
        trigger_description: "Unlocked after completing lead-03",
        points: 45,
        content: {
          type: "checklist",
          data: {
            intro:
              "Déléguer à bord ne signifie pas abandonner. Cette check-list vous aide à structurer une délégation efficace sur votre prochain poste.",
            downloadable: true,
            categories: [
              {
                category: "Avant de déléguer",
                items: [
                  "La tâche est-elle clairement définie et mesurable ?",
                  "La personne a-t-elle les compétences minimales requises ?",
                  "Y a-t-il un risque sécurité si la tâche est mal exécutée ?",
                  "Ai-je prévu un point de contrôle intermédiaire ?",
                ],
              },
              {
                category: "Lors de la délégation",
                items: [
                  "Expliquer le POURQUOI, pas seulement le QUOI",
                  "Définir le niveau d'autonomie accordé (A/B/C)",
                  "Confirmer la compréhension par reformulation",
                  "Indiquer à qui s'adresser en cas de problème",
                ],
              },
            ],
          },
        },
      },
      {
        id: "lead-05",
        axe_id: "leadership",
        title: "Leadership situationnel marin",
        subtitle: "Adapter son style au contexte",
        type: "self_assessment",
        duration_min: 12,
        levels: ["senior"],
        status: "locked",
        trigger_description: "Available after completing all lead modules",
        points: 50,
        content: {
          type: "self_assessment",
          data: {
            intro:
              "Le leadership situationnel reconnaît qu'il n'existe pas un seul style efficace. Selon la maturité de votre équipage et la situation, vous adaptez votre approche.",
            questions: [
              {
                id: "lead-sa-1",
                text: "Face à un novice en situation de stress, vous avez tendance à :",
                scale_low: "Le laisser gérer seul pour apprendre",
                scale_high: "Prendre le contrôle directement",
              },
              {
                id: "lead-sa-2",
                text: "Lors d'un passage long, votre communication avec l'équipage est :",
                scale_low: "Minimale — chacun fait son quart",
                scale_high: "Régulière — briefings quotidiens",
              },
            ],
          },
        },
      },
    ],
  },

  // ── AXE 3 — Résilience & stress ───────────────────────────────
  {
    id: "resilience",
    title: "Résilience & stress",
    subtitle: "Fatigue · Isolation · Pressure",
    icon: "◎",
    color: "#A68D6A",
    trigger_description:
      "Triggered when Emotional Stability (T-IRT) < 70 or survey mentions fatigue/burnout",
    modules: [
      {
        id: "res-01",
        axe_id: "resilience",
        title: "Comprendre le stress en mer",
        subtitle: "Physiologie, déclencheurs et fenêtres de récupération",
        type: "lesson",
        duration_min: 14,
        levels: ["junior", "mid", "senior"],
        status: "available",
        trigger_description:
          "Triggered: T-IRT Emotional Stability at threshold (65/100)",
        points: 55,
        content: {
          type: "lesson",
          data: {
            sections: [
              {
                title: "Le stress en mer est structurel, pas personnel",
                body: "Rythme de quart perturbé, espaces confinés, imprévisibilité météo, pression sociale d'un équipage restreint, isolement des proches : tous ces facteurs s'accumulent de façon linéaire. Ce n'est pas une faiblesse — c'est de la physique.",
              },
              {
                title: "La courbe d'Yerkes-Dodson en contexte nautique",
                body: "Un niveau de stress modéré améliore la performance. Trop peu (routine monotone du quart de nuit) endort l'attention. Trop (urgence non anticipée, manque de sommeil) dégrade le jugement. Identifier où vous êtes sur cette courbe est la première compétence de résilience.",
              },
              {
                title: "Les 4 signaux d'alerte personnels",
                body: "Chaque personne a ses propres signaux précoces : irritabilité inhabituelle, troubles du sommeil dans les ports, refus de déléguer, sarcasme en briefing. Apprenez à reconnaître les vôtres avant qu'ils impactent l'équipage.",
              },
            ],
          },
        },
      },
      {
        id: "res-02",
        axe_id: "resilience",
        title: "Techniques de décompression à bord",
        subtitle: "Protocoles pratiques entre les quarts",
        type: "exercise",
        duration_min: 15,
        levels: ["junior", "mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing res-01",
        points: 65,
        content: { type: "exercise", data: { objective: "", steps: [], debrief: "" } },
      },
      {
        id: "res-03",
        axe_id: "resilience",
        title: "Fatigue maritime et prise de décision",
        subtitle: "Reconnaître la dégradation cognitive",
        type: "lesson",
        duration_min: 12,
        levels: ["mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing res-02",
        points: 55,
        content: { type: "lesson", data: { sections: [] } },
      },
      {
        id: "res-04",
        axe_id: "resilience",
        title: "Plan de récupération personnel",
        subtitle: "Construire vos routines de bord",
        type: "checklist",
        duration_min: 10,
        levels: ["junior", "mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing res-03",
        points: 40,
        content: { type: "checklist", data: { intro: "", categories: [], downloadable: true } },
      },
    ],
  },

  // ── AXE 4 — Cohésion équipage ─────────────────────────────────
  {
    id: "cohesion",
    title: "Cohésion équipage",
    subtitle: "Communication · Inclusion · Trust",
    icon: "⬡",
    color: "#94A3B8",
    trigger_description:
      "Triggered by DNRE results or Sociogram score < 65 or survey conflict signals",
    modules: [
      {
        id: "coh-01",
        axe_id: "cohesion",
        title: "Dynamiques d'équipe en espace confiné",
        subtitle: "Comprendre les tensions structurelles",
        type: "lesson",
        duration_min: 16,
        levels: ["mid", "senior"],
        status: "available",
        trigger_description: "Triggered after DNRE assessment completion",
        points: 60,
        content: {
          type: "lesson",
          data: {
            sections: [
              {
                title: "Pourquoi les équipages soudés peuvent imploser",
                body: "Les études sur les équipages en espace confiné (sous-marins, stations polaires, superyachts en saison) montrent un pattern récurrent : les conflits éclatent rarement en crise — ils s'accumulent en micro-tensions non verbalisées pendant 3 à 6 semaines.",
              },
              {
                title: "Le modèle Tuckman adapté au bord",
                body: "Forming (embark), Storming (premières frictions), Norming (routines établies), Performing (pic de cohésion), Adjourning (fin de saison, gestion des départs). Savoir où se situe votre équipage sur ce cycle change votre approche de management.",
              },
            ],
          },
        },
      },
      {
        id: "coh-02",
        axe_id: "cohesion",
        title: "Communication non-violente en milieu confiné",
        subtitle: "CNV et assertivité maritime",
        type: "exercise",
        duration_min: 20,
        levels: ["junior", "mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing coh-01",
        points: 80,
        content: { type: "exercise", data: { objective: "", steps: [], debrief: "" } },
      },
      {
        id: "coh-03",
        axe_id: "cohesion",
        title: "Diversité culturelle à bord",
        subtitle: "Codes, attentes et malentendus fréquents",
        type: "checklist",
        duration_min: 12,
        levels: ["mid", "senior"],
        status: "locked",
        trigger_description: "Unlocked after completing coh-02",
        points: 45,
        content: { type: "checklist", data: { intro: "", categories: [], downloadable: true } },
      },
      {
        id: "coh-04",
        axe_id: "cohesion",
        title: "Auto-évaluation — Cohésion d'équipe",
        subtitle: "Mesurez votre contribution à l'ambiance",
        type: "self_assessment",
        duration_min: 8,
        levels: ["junior", "mid", "senior"],
        status: "locked",
        trigger_description: "Available after completing 3 cohesion modules",
        points: 35,
        content: {
          type: "self_assessment",
          data: {
            intro:
              "Ces questions explorent votre rôle naturel dans la dynamique d'équipage.",
            questions: [
              {
                id: "coh-sa-1",
                text: "Lors d'un conflit entre deux collègues, votre réaction naturelle est :",
                scale_low: "Je m'en tiens éloigné",
                scale_high: "Je cherche à faciliter le dialogue",
              },
            ],
          },
        },
      },
    ],
  },
];

// ── Personalized path (for James Whitfield — senior, First Mate) ───
// TODO: compute dynamically from psychometric_snapshot + experience + position
export const MY_PATH: PersonalizedPath = {
  level: "senior",
  level_label: "Senior crew",
  level_description: "7+ years · Leadership & advanced operations",
  path_name: "Parcours First Mate confirmé",
  current_module_id: "lead-02",
  queued_module_ids: ["lead-03", "res-01", "op-04"],
  global_completion_pct: 18,
  trigger_summary:
    "Basé sur votre T-IRT : Extraversion 62 (Leadership recommandé) · Stabilité émotionnelle 65 (Résilience suggérée)",
};

// ── Helper functions ──────────────────────────────────────────────

export function getModuleById(id: string): TrainingModule | undefined {
  for (const axe of TRAINING_AXES) {
    const mod = axe.modules.find((m) => m.id === id);
    if (mod) return mod;
  }
  return undefined;
}

export function getAxeById(id: string): TrainingAxe | undefined {
  return TRAINING_AXES.find((a) => a.id === id);
}

export function getAxeStats(axe: TrainingAxe) {
  const total = axe.modules.length;
  const completed = axe.modules.filter((m) => m.status === "completed").length;
  const in_progress = axe.modules.filter((m) => m.status === "in_progress").length;
  return { total, completed, in_progress, pct: Math.round((completed / total) * 100) };
}

export const MODULE_TYPE_CONFIG: Record<
  ModuleType,
  { icon: string; label: string; color: string }
> = {
  lesson: { icon: "📖", label: "Lesson", color: "#94A3B8" },
  exercise: { icon: "⚡", label: "Exercise", color: "#A67C52" },
  checklist: { icon: "✓", label: "Checklist", color: "#5A8279" },
  self_assessment: { icon: "◎", label: "Self-assessment", color: "#A68D6A" },
};

export const LEVEL_CONFIG: Record<ExperienceLevel, { label: string; color: string; description: string }> = {
  junior: {
    label: "Junior crew",
    color: "#5A8279",
    description: "0–2 yrs · Employability & professionalization",
  },
  mid: {
    label: "Experienced crew",
    color: "#A67C52",
    description: "2–6 yrs · Leadership development",
  },
  senior: {
    label: "Senior crew",
    color: "#2E8A5C",
    description: "6+ yrs · Advanced command & cohesion",
  },
};
