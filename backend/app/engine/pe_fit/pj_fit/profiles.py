# engine/recruitment/pe_fit/pj_fit/profiles.py
# TODO Temps 2: recalibrer les profils via méthode SME structurée (Q-sort) et percentiles normalisés
"""
Profils idéaux par poste — migration depuis content/sme_profiles.py.

Les profils décrivent les scores cibles (0-100) sur les traits de personnalité,
motivationnels et cognitifs pour chaque YachtPosition.

Source : Phase 0 SME panel maritime + littérature I/O (Barrick & Mount 1991,
         Hogan & Hogan 2001).
"""
from __future__ import annotations
from typing import Optional


# ── Mapping des traits par catégorie ──────────────────────────────────────────

CATEGORY_MAPPING: dict[str, list[str]] = {
    "personality": [
        "extraversion", "agreeableness", "openness",
        "neuroticism", "conscientiousness",
    ],
    "motivation": [
        "intrinsic", "extrinsic_social", "extrinsic_material",
        "identified", "introjected", "amotivation",
    ],
    "cognitive": ["numerical", "logical", "verbal"],
}


# ── Définitions lisibles des traits ───────────────────────────────────────────

TRAIT_DEFINITIONS: dict[str, str] = {
    # Personnalité
    "extraversion": (
        "Tendance à être sociable, énergique et orienté vers les interactions "
        "sociales. Une personne extravertie s'épanouit dans les échanges et les "
        "activités de groupe, tandis qu'une personne introvertie préfère la "
        "solitude et la réflexion."
    ),
    "agreeableness": (
        "Capacité à être coopératif, empathique et soucieux de l'harmonie "
        "sociale. Une personne agréable évite les conflits et privilégie la "
        "bienveillance, tandis qu'une personne moins agréable peut être plus "
        "directe ou compétitive."
    ),
    "conscientiousness": (
        "Niveau d'organisation, de persévérance et de fiabilité. Une personne "
        "consciencieuse est méthodique et ponctuelle, tandis qu'une personne "
        "moins consciencieuse peut être plus spontanée ou désorganisée."
    ),
    "neuroticism": (
        "Sensibilité aux émotions négatives comme l'anxiété, l'irritabilité ou "
        "la tristesse. Une personne avec un haut niveau de névrosisme réagit "
        "fortement au stress, tandis qu'une personne stable émotionnellement "
        "reste calme sous pression."
    ),
    "openness": (
        "Ouverture à la curiosité, à la créativité et aux nouvelles expériences. "
        "Une personne ouverte est imaginative et flexible, tandis qu'une personne "
        "moins ouverte préfère la routine et les solutions éprouvées."
    ),

    # Cognitif
    "numerical": (
        "Capacité à comprendre, analyser et manipuler des données numériques. "
        "Une personne avec une forte aptitude numérique excelle dans les calculs "
        "et l'analyse de données."
    ),
    "logical": (
        "Aptitude à analyser des problèmes complexes et à identifier des schémas "
        "logiques. Une personne logique excelle dans la résolution de problèmes "
        "structurés et la planification stratégique."
    ),
    "verbal": (
        "Capacité à comprendre et utiliser le langage de manière précise et "
        "efficace. Une personne avec une forte aptitude verbale s'exprime "
        "clairement et adapte son discours à son audience."
    ),

    # Motivation
    "intrinsic": (
        "Motivation interne liée au plaisir et à la satisfaction de réaliser une "
        "activité pour elle-même. Une personne intrinsèquement motivée agit par "
        "passion ou curiosité."
    ),
    "extrinsic_social": (
        "Motivation externe liée à la reconnaissance sociale, à l'appartenance "
        "ou au statut. Une personne motivée socialement cherche l'approbation et "
        "la collaboration avec les autres."
    ),
    "extrinsic_material": (
        "Motivation externe liée aux récompenses tangibles comme le salaire, "
        "les bonus ou la sécurité financière. Une personne motivée matériellement "
        "valorise les bénéfices concrets."
    ),
    "identified": (
        "Motivation où l'individu adopte une tâche parce qu'il la juge importante, "
        "même si elle n'est pas plaisante. Il agit en alignement avec ses valeurs "
        "ou objectifs personnels."
    ),
    "introjected": (
        "Motivation où l'individu agit pour éviter la culpabilité ou la honte, "
        "souvent en réponse à des attentes internes. Il se sent poussé par une "
        "pression personnelle plutôt que par le plaisir."
    ),
    "amotivation": (
        "Absence de motivation, caractérisée par un manque d'intention ou de "
        "raison d'agir. L'individu peut se sentir désengagé ou dépassé par "
        "les tâches."
    ),
}


# ── Polarités des traits ───────────────────────────────────────────────────────

TRAIT_POLARITY: dict[str, str] = {
    # Personnalité
    "extraversion":        "high",     # Un niveau élevé favorise les interactions sociales et le leadership
    "agreeableness":       "high",     # Un niveau élevé favorise la coopération et l'harmonie
    "conscientiousness":   "high",     # Un niveau élevé favorise l'organisation et la fiabilité
    "openness":            "high",     # Un niveau élevé favorise la créativité et l'adaptabilité
    "neuroticism":         "low",      # Un niveau bas favorise la stabilité émotionnelle et la résilience

    # Cognitif
    "numerical":           "high",     # Un niveau élevé favorise l'analyse et la gestion des données
    "logical":             "high",     # Un niveau élevé favorise la résolution de problèmes complexes
    "verbal":              "high",     # Un niveau élevé favorise la communication et la compréhension

    # Motivation
    "intrinsic":           "high",     # Un niveau élevé favorise l'engagement et la satisfaction personnelle
    "extrinsic_social":    "high",     # Un niveau élevé favorise la collaboration et la reconnaissance sociale
    "extrinsic_material":  "moderate", # Un niveau modéré est idéal
    "identified":          "high",     # Un niveau élevé favorise l'alignement avec les valeurs personnelles
    "introjected":         "low",      # Un niveau bas réduit la pression interne
    "amotivation":         "low",      # Un niveau bas est toujours préférable
}


# ── Profils idéaux SME par poste ──────────────────────────────────────────────

SME_PROFILES: dict[str, dict] = {
    "Captain": {
        "personality": {
            "conscientiousness": 95, "neuroticism": 15, "extraversion": 75,
            "agreeableness": 70, "openness": 80,
        },
        "motivation": {
            "intrinsic": 90, "identified": 85, "extrinsic_material": 60,
            "amotivation": 0,
        },
        "cognitive": {"logical": 90, "verbal": 85, "numerical": 80},
    },
    "First Mate": {
        "personality": {
            "conscientiousness": 90, "neuroticism": 20, "extraversion": 70,
            "agreeableness": 75, "openness": 75,
        },
        "motivation": {
            "intrinsic": 85, "identified": 80, "extrinsic_material": 65,
            "amotivation": 0,
        },
        "cognitive": {"logical": 85, "verbal": 80, "numerical": 85},
    },
    "Bosun": {
        "personality": {
            "conscientiousness": 85, "neuroticism": 25, "extraversion": 65,
            "agreeableness": 80, "openness": 60,
        },
        "motivation": {
            "intrinsic": 80, "identified": 85, "extrinsic_material": 70,
            "amotivation": 0,
        },
        "cognitive": {"logical": 75, "verbal": 60, "numerical": 70},
    },
    "Deckhand": {
        "personality": {
            "conscientiousness": 80, "neuroticism": 30, "extraversion": 60,
            "agreeableness": 85, "openness": 50,
        },
        "motivation": {
            "identified": 90, "extrinsic_social": 80, "extrinsic_material": 75,
            "amotivation": 0,
        },
        "cognitive": {"logical": 65, "verbal": 60, "numerical": 60},
    },
    "Chief Engineer": {
        "personality": {
            "conscientiousness": 98, "neuroticism": 10, "extraversion": 40,
            "agreeableness": 65, "openness": 70,
        },
        "motivation": {
            "intrinsic": 95, "identified": 80, "extrinsic_material": 60,
            "amotivation": 0,
        },
        "cognitive": {"logical": 95, "numerical": 95, "verbal": 70},
    },
    "2nd Engineer": {
        "personality": {
            "conscientiousness": 90, "neuroticism": 15, "extraversion": 45,
            "agreeableness": 70, "openness": 70,
        },
        "motivation": {
            "intrinsic": 90, "identified": 85, "extrinsic_material": 65,
            "amotivation": 0,
        },
        "cognitive": {"logical": 90, "numerical": 90, "verbal": 65},
    },
    "Chief Stewardess": {
        "personality": {
            "conscientiousness": 95, "neuroticism": 20, "extraversion": 85,
            "agreeableness": 90, "openness": 80,
        },
        "motivation": {
            "intrinsic": 85, "identified": 90, "extrinsic_social": 90,
            "amotivation": 0,
        },
        "cognitive": {"verbal": 90, "logical": 75, "numerical": 70},
    },
    "Stewardess": {
        "personality": {
            "conscientiousness": 85, "neuroticism": 25, "extraversion": 80,
            "agreeableness": 95, "openness": 75,
        },
        "motivation": {
            "extrinsic_social": 95, "identified": 80, "extrinsic_material": 70,
            "amotivation": 0,
        },
        "cognitive": {"verbal": 85, "logical": 60, "numerical": 60},
    },
    "Chef": {
        "personality": {
            "conscientiousness": 90, "neuroticism": 35, "extraversion": 50,
            "agreeableness": 60, "openness": 95,
        },
        "motivation": {
            "intrinsic": 98, "identified": 70, "extrinsic_material": 60,
            "amotivation": 0,
        },
        "cognitive": {"logical": 80, "verbal": 70, "numerical": 75},
    },

    # ── Nouveaux postes (phase alpha) ─────────────────────────────────────────

    "Second Officer": {
        "personality": {
            "conscientiousness": 88, "neuroticism": 22, "extraversion": 65,
            "agreeableness": 72, "openness": 70,
        },
        "motivation": {
            "intrinsic": 82, "identified": 80, "extrinsic_material": 65,
            "amotivation": 0,
        },
        "cognitive": {"logical": 80, "verbal": 78, "numerical": 80},
    },
    "3rd Engineer": {
        "personality": {
            "conscientiousness": 85, "neuroticism": 20, "extraversion": 42,
            "agreeableness": 68, "openness": 65,
        },
        "motivation": {
            "intrinsic": 85, "identified": 80, "extrinsic_material": 65,
            "amotivation": 0,
        },
        "cognitive": {"logical": 85, "numerical": 85, "verbal": 62},
    },
    "ETO": {
        "personality": {
            "conscientiousness": 95, "neuroticism": 15, "extraversion": 38,
            "agreeableness": 65, "openness": 75,
        },
        "motivation": {
            "intrinsic": 90, "identified": 80, "extrinsic_material": 65,
            "amotivation": 0,
        },
        "cognitive": {"logical": 90, "numerical": 95, "verbal": 65},
    },
    "Butler": {
        "personality": {
            "conscientiousness": 97, "neuroticism": 18, "extraversion": 78,
            "agreeableness": 92, "openness": 82,
        },
        "motivation": {
            "intrinsic": 88, "identified": 92, "extrinsic_social": 90,
            "amotivation": 0,
        },
        "cognitive": {"verbal": 92, "logical": 78, "numerical": 68},
    },
    "Sous Chef": {
        "personality": {
            "conscientiousness": 85, "neuroticism": 38, "extraversion": 48,
            "agreeableness": 65, "openness": 90,
        },
        "motivation": {
            "intrinsic": 92, "identified": 72, "extrinsic_material": 62,
            "amotivation": 0,
        },
        "cognitive": {"logical": 75, "verbal": 65, "numerical": 70},
    },
    "Dive Instructor": {
        "personality": {
            "conscientiousness": 88, "neuroticism": 20, "extraversion": 80,
            "agreeableness": 85, "openness": 88,
        },
        "motivation": {
            "intrinsic": 95, "identified": 80, "extrinsic_social": 82,
            "amotivation": 0,
        },
        "cognitive": {"logical": 78, "verbal": 80, "numerical": 65},
    },
    "Medic": {
        "personality": {
            "conscientiousness": 95, "neuroticism": 15, "extraversion": 60,
            "agreeableness": 88, "openness": 72,
        },
        "motivation": {
            "intrinsic": 90, "identified": 88, "extrinsic_social": 75,
            "amotivation": 0,
        },
        "cognitive": {"logical": 88, "verbal": 85, "numerical": 82},
    },
}

# Version normalisée (minuscules) pour faciliter la recherche
JOB_PROFILES_NORM: dict[str, dict] = {k.lower(): v for k, v in SME_PROFILES.items()}


# ── Lookup matriciel (position × yacht_type) — Phase alpha ────────────────────
#
# Patches appliqués sur le profil générique par type de yacht.
# Seuls les traits significativement différents sont listés (diff minimal).
# Clés : (position_lower, yacht_type_lower)  — YachtTypeAlpha.value en minuscules.
#
# Calibration SME Phase 0 — à recalibrer en Phase 1 sur données terrain.

SME_MATRIX_PATCHES: dict[tuple[str, str], dict] = {

    # ── Captain ────────────────────────────────────────────────────────────────
    # Voilier de course : forte précision technique, moins d'interface client
    ("captain", "sailing_racing"): {
        "personality": {"conscientiousness": 98, "extraversion": 55, "openness": 85},
        "motivation":  {"intrinsic": 98, "extrinsic_material": 50},
        "cognitive":   {"logical": 95},
    },
    # Expédition : résilience extrême, autonomie opérationnelle
    ("captain", "expedition"): {
        "personality": {"openness": 92, "neuroticism": 12},
        "motivation":  {"intrinsic": 95, "identified": 92},
    },
    # Mégayacht : interaction UHNWI, hiérarchie formelle complexe
    ("captain", "megayacht"): {
        "personality": {"extraversion": 82, "conscientiousness": 97},
        "motivation":  {"extrinsic_material": 70},
        "cognitive":   {"verbal": 92},
    },

    # ── Chef ───────────────────────────────────────────────────────────────────
    # Charter : rotation constante de guests, menus courts préavis
    ("chef", "charter"): {
        "personality": {"neuroticism": 45, "extraversion": 62},
        "motivation":  {"intrinsic": 92, "extrinsic_material": 72},
    },
    # Mégayacht : gastronomie formelle, cuisine de prestige
    ("chef", "megayacht"): {
        "personality": {"conscientiousness": 95, "openness": 98},
    },

    # ── Chief Stewardess ───────────────────────────────────────────────────────
    # Charter : forte rotation guests, adaptabilité sociale maximale
    ("chief stewardess", "charter"): {
        "personality": {"extraversion": 90, "neuroticism": 28},
    },
    # Mégayacht : protocoles formels stricts, coordination d'équipe étendue
    ("chief stewardess", "megayacht"): {
        "personality": {"conscientiousness": 98},
        "motivation":  {"extrinsic_social": 95},
    },

    # ── Chief Engineer ─────────────────────────────────────────────────────────
    # Expédition : fiabilité critique, autosuffisance technique totale
    ("chief engineer", "expedition"): {
        "personality": {"conscientiousness": 99},
        "cognitive":   {"numerical": 98},
    },
}

# Lookup normalisé (clés déjà en minuscules)
_MATRIX_NORM: dict[tuple[str, str], dict] = {
    (pos, yt): patch for (pos, yt), patch in SME_MATRIX_PATCHES.items()
}


def _deep_merge(base: dict, patch: dict) -> dict:
    """Retourne une copie de base avec les valeurs de patch appliquées (1 niveau de profondeur)."""
    merged: dict = {}
    for category in set(base) | set(patch):
        base_cat = base.get(category, {})
        patch_cat = patch.get(category, {})
        merged[category] = {**base_cat, **patch_cat}
    return merged


# ── Accesseur public ──────────────────────────────────────────────────────────

def get_ideal_profile(position: str, yacht_type: Optional[str] = None) -> Optional[dict]:
    """
    Retourne le profil idéal SME pour une position donnée.

    Lookup en 2 étapes :
    1. Cherche un profil spécifique dans SME_MATRIX_PATCHES pour (position, yacht_type).
       Si trouvé, applique le patch sur le profil générique.
    2. Fallback sur le profil générique SME_PROFILES[position].

    La recherche est case-insensitive pour position et yacht_type.

    Args:
        position   : YachtPosition.value ou libellé libre (ex: "captain", "Captain")
        yacht_type : YachtTypeAlpha.value (ex: "megayacht", "sailing_racing") — optionnel.
                     Si None ou absent de la matrice, retourne le profil générique.

    Returns:
        dict avec les clés "personality", "motivation", "cognitive",
        ou None si le poste n'est pas référencé dans SME_PROFILES.
    """
    base = JOB_PROFILES_NORM.get(position.lower())
    if base is None:
        return None

    if yacht_type is not None:
        patch = _MATRIX_NORM.get((position.lower(), yacht_type.lower()))
        if patch:
            return _deep_merge(base, patch)

    return base
