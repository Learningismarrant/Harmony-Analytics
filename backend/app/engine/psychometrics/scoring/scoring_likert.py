# engine/psychometrics/scoring_likert.py
"""
Scoring Likert — Self-Determination Theory (R-MAWS), Big Five (HBF-50), etc.

Algorithme :
  - Items reverse-scorés : valeur_calculée = (min + max) − valeur_brute
  - Score par trait = somme(valeur_calculée) / max_possible × 100
  - Fiabilité : vitesse + biais extrêmes

Appelé par : engine/psychometrics/scoring.py (dispatcher)
"""
from typing import List, Any, Dict

from .normalizer import to_percentage
from .reliability import check_reliability
from .formatter import (
    format_trait_scores,
    level_label_likert,
    build_result,
)

DEFAULT_LIKERT_MIN = 1


def calculate_likert_scores(
    responses: List[Any],
    questions_map: Dict[int, Any],  # {question_id: Question ORM}
    max_score_per_question: int,
) -> Dict:
    """
    Calcule les scores Likert par trait.

    Paramètres
    ----------
    responses               : liste des objets Response (valeur_choisie, seconds_spent)
    questions_map           : dict {question_id → Question} hydraté en amont
    max_score_per_question  : score maximum d'un item (ex. 5 pour HBF-50, 7 pour R-MAWS)

    Retourne le dict unifié build_result().
    """
    traits = set(q.trait for q in questions_map.values())
    stats: Dict[str, Dict] = {t: {"points": 0.0, "max_possible": 0.0} for t in traits}

    total_time = 0.0

    for r in responses:
        q = questions_map.get(r.question_id)
        if not q:
            continue

        if hasattr(r, "seconds_spent") and r.seconds_spent:
            total_time += r.seconds_spent

        try:
            raw = int(r.valeur_choisie)
        except (ValueError, TypeError):
            continue

        value = (DEFAULT_LIKERT_MIN + max_score_per_question) - raw if q.reverse else raw

        stats[q.trait]["points"] += value
        stats[q.trait]["max_possible"] += max_score_per_question

    trait_scores = format_trait_scores(stats, level_label_likert)
    reliability = check_reliability(responses, max_score_per_question, total_time)

    return build_result(trait_scores, reliability, total_time, len(responses))
