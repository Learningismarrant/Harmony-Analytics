# engine/psychometrics/formatter.py
"""
Mise en forme des sorties psychométriques.

Fournit une structure de résultat uniforme pour tous les scorers
(Likert, QCM, Ipsatif/T-IRT).

Structure de sortie :
{
    "traits": {
        "trait_name": {"score": float, "niveau": str},
        ...
    },
    "global_score": float,
    "reliability": {"is_reliable": bool, "reasons": [str]},
    "meta": {
        "total_time_seconds": float,
        "avg_seconds_per_question": float,
    },
}
"""
from typing import Dict

# ── Seuils ────────────────────────────────────────────────────────────────────
THRESHOLD_QCM_EXCELLENT = 80
THRESHOLD_QCM_STANDARD  = 50

THRESHOLD_LIKERT_HIGH   = 70
THRESHOLD_LIKERT_MEDIUM = 30


def level_label_qcm(score: float) -> str:
    if score >= THRESHOLD_QCM_EXCELLENT:
        return "Excellent"
    if score >= THRESHOLD_QCM_STANDARD:
        return "Standard"
    return "À renforcer"


def level_label_likert(score: float) -> str:
    if score > THRESHOLD_LIKERT_HIGH:
        return "Élevé"
    if score > THRESHOLD_LIKERT_MEDIUM:
        return "Moyen"
    return "Faible"


def format_trait_scores(
    stats: Dict[str, Dict],   # {trait: {"points": float, "max_possible": float}}
    level_fn,                 # level_label_qcm | level_label_likert
) -> Dict[str, Dict]:
    """
    Convertit les stats brutes (points/max) en dict de scores normalisés.

    Retourne : {trait: {"score": float, "niveau": str}}
    """
    from .normalizer import to_percentage

    result = {}
    for trait, data in stats.items():
        pct = to_percentage(data["points"], data["max_possible"])
        result[trait] = {"score": pct, "niveau": level_fn(pct)}
    return result


def build_result(
    trait_scores: Dict,
    reliability: Dict,
    total_time_seconds: float,
    num_responses: int,
) -> Dict:
    """
    Assemble le résultat final uniforme retourné par tous les scorers.
    """
    global_score = (
        round(sum(t["score"] for t in trait_scores.values()) / len(trait_scores), 1)
        if trait_scores else 0.0
    )
    avg_secs = (
        round(total_time_seconds / num_responses, 1) if num_responses > 0 else 0.0
    )
    return {
        "traits": trait_scores,
        "global_score": global_score,
        "reliability": reliability,
        "meta": {
            "total_time_seconds": total_time_seconds,
            "avg_seconds_per_question": avg_secs,
        },
    }
