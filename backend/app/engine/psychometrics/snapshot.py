# engine/psychometrics/snapshot.py
"""
Construction et agrégation du psychometric_snapshot.

Le snapshot est le pont entre les TestResult bruts (source de vérité)
et l'engine de calcul (qui ne lit jamais la DB).

Structure du snapshot :
{
    "big_five": {
        "conscientiousness": 72.4,
        "agreeableness": 68.1,
        "neuroticism": 31.5,   # score brut (bas = stable)
        "emotional_stability": 68.5,  # 100 - neuroticism, utilisé dans F_team
        "openness": 55.0,
        "extraversion": 61.2
    },
    "cognitive": {
        "gca_score": 78.0,     # moyenne des sous-scores cognitifs
        "numerical": 82.0,
        "logical": 74.0,
        "verbal": 71.0
    },
    "motivation": {
        "intrinsic": 80.0,
        "identified": 75.0,
        "amotivation": 12.0,
        ...
    },
    "leadership_preferences": {
        "autonomy_preference": 0.7,    # Dérivé de scores spécifiques
        "feedback_preference": 0.5,
        "structure_preference": 0.4
    },
    "resilience": {                    # Ajouté dès qu'un test resilience est soumis
        "global": 65.0
    },
    "meta": {
        "completeness": 0.85,          # % traits couverts vs. requis par engine
        "last_updated": "2025-01-15T10:30:00",
        "tests_taken": ["big_five_v1", "gca_v2", "motivation_v1"]
    }
}
"""
from datetime import datetime
from typing import List, Dict, Any

from app.content.sme_profiles import CATEGORY_MAPPING

# Mapping trait → catégorie snapshot (plus granulaire que CATEGORY_MAPPING)
TRAIT_TO_SNAPSHOT_CAT = {
    # Big Five
    "conscientiousness": "big_five",
    "agreeableness": "big_five",
    "neuroticism": "big_five",
    "openness": "big_five",
    "extraversion": "big_five",
    # Cognitif
    "numerical": "cognitive",
    "logical": "cognitive",
    "verbal": "cognitive",
    # Motivation
    "intrinsic": "motivation",
    "extrinsic_social": "motivation",
    "extrinsic_material": "motivation",
    "identified": "motivation",
    "introjected": "motivation",
    "amotivation": "motivation",
    # Résilience (test futur)
    "resilience_global": "resilience",
    "stress_tolerance": "resilience",
}

# Traits minimum requis par l'engine pour calculer Ŷ_success
REQUIRED_TRAITS_FOR_ENGINE = {
    "big_five": ["conscientiousness", "agreeableness", "neuroticism", "extraversion"],
    "cognitive": ["logical", "numerical", "verbal"],
    "motivation": ["intrinsic", "identified", "amotivation"],
}


def build_snapshot(test_results: List[Any]) -> Dict:
    """
    Reconstruit le snapshot complet depuis tous les TestResult d'un candidat.
    Les résultats plus récents écrasent les plus anciens (même test repassé).

    Appelé par : modules/assessment/service.py après chaque soumission de test.
    NE PAS appeler depuis un endpoint — uniquement depuis le service post-scoring.
    """
    # Tri chronologique : les plus récents écrasent les anciens
    sorted_results = sorted(test_results, key=lambda r: r.created_at)

    snapshot: Dict[str, Dict] = {
        "big_five": {},
        "cognitive": {},
        "motivation": {},
        "leadership_preferences": {},
        "resilience": {},
    }
    tests_taken = []

    for result in sorted_results:
        if not result.scores:
            continue

        test_name = result.test_name if hasattr(result, "test_name") else f"test_{result.test_id}"
        if test_name not in tests_taken:
            tests_taken.append(test_name)

        traits_data = result.scores.get("traits", result.scores)

        for trait, data in traits_data.items():
            if trait in ("reliability", "meta"):
                continue

            score = data.get("score", 0) if isinstance(data, dict) else data
            cat = TRAIT_TO_SNAPSHOT_CAT.get(trait)

            if cat and cat in snapshot:
                snapshot[cat][trait] = round(score, 1)

    # --- Calculs dérivés ---

    # Stabilité émotionnelle = inverse du névrosisme (utilisée dans F_team)
    if "neuroticism" in snapshot["big_five"]:
        snapshot["big_five"]["emotional_stability"] = round(
            100 - snapshot["big_five"]["neuroticism"], 1
        )

    # GCA score = moyenne cognitive
    if snapshot["cognitive"]:
        snapshot["cognitive"]["gca_score"] = round(
            sum(snapshot["cognitive"].values()) / len(snapshot["cognitive"]), 1
        )

    # Préférences de leadership (dérivées des scores de personnalité/motivation)
    # Calibration à affiner avec les données réelles
    snapshot["leadership_preferences"] = _derive_leadership_preferences(snapshot)

    # --- Meta ---
    completeness = _compute_completeness(snapshot)
    snapshot["meta"] = {
        "completeness": completeness,
        "last_updated": datetime.utcnow().isoformat(),
        "tests_taken": tests_taken,
    }

    return snapshot


def _derive_leadership_preferences(snapshot: Dict) -> Dict:
    """
    Dérive les préférences de leadership depuis les scores psychométriques.
    Logique provisoire — à calibrer avec les données SME.
    """
    big_five = snapshot.get("big_five", {})
    motivation = snapshot.get("motivation", {})

    # autonomy_preference : Haut openness + bas conscientiousness → préfère autonomie
    openness = big_five.get("openness", 50)
    conscientiousness = big_five.get("conscientiousness", 50)
    autonomy = round(((openness * 0.6) + ((100 - conscientiousness) * 0.4)) / 100, 2)

    # feedback_preference : Haut extraversion + haut agreeableness → cherche feedback
    extraversion = big_five.get("extraversion", 50)
    agreeableness = big_five.get("agreeableness", 50)
    feedback = round(((extraversion * 0.5) + (agreeableness * 0.5)) / 100, 2)

    # structure_preference : Haut conscientiousness + bas openness → aime la structure
    structure = round(((conscientiousness * 0.7) + ((100 - openness) * 0.3)) / 100, 2)

    return {
        "autonomy_preference": autonomy,
        "feedback_preference": feedback,
        "structure_preference": structure,
    }


def _compute_completeness(snapshot: Dict) -> float:
    """Calcule le ratio de traits disponibles vs requis par l'engine."""
    covered = 0
    total = 0
    for cat, required_traits in REQUIRED_TRAITS_FOR_ENGINE.items():
        for trait in required_traits:
            total += 1
            if trait in snapshot.get(cat, {}):
                covered += 1
    return round(covered / total, 2) if total > 0 else 0.0


def extract_engine_inputs(snapshot: Dict) -> Dict:
    """
    Extrait les inputs normalisés pour l'engine de recrutement.
    Retourne un dict propre utilisable par p_ind, f_team, f_env, f_lmx.
    """
    big_five = snapshot.get("big_five", {})
    cognitive = snapshot.get("cognitive", {})
    leadership = snapshot.get("leadership_preferences", {})
    resilience = snapshot.get("resilience", {})

    return {
        # Pour P_ind
        "gca": cognitive.get("gca_score", 0),
        "conscientiousness": big_five.get("conscientiousness", 0),

        # Pour F_team
        "agreeableness": big_five.get("agreeableness", 0),
        "emotional_stability": big_five.get("emotional_stability", 0),

        # Pour F_env
        "resilience": resilience.get("global", big_five.get("emotional_stability", 50)),

        # Pour F_lmx
        "autonomy_preference": leadership.get("autonomy_preference", 0.5),
        "feedback_preference": leadership.get("feedback_preference", 0.5),
        "structure_preference": leadership.get("structure_preference", 0.5),

        # Meta
        "completeness": snapshot.get("meta", {}).get("completeness", 0),
    }