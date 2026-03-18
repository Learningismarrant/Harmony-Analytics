# engine/psychometrics/scoring_qcm.py
"""
Scoring QCM — COG-IQ (Carroll, 1993) et tout test à réponse correcte unique.

Algorithme :
  - 1 point si valeur_choisie == correct_answer (insensible à la casse)
  - 0 sinon
  - Score par trait = items_corrects / items_total × 100
  - Fiabilité : vitesse suspecte uniquement (pas de biais extrêmes sur QCM)

Appelé par : engine/psychometrics/scoring.py (dispatcher)
"""
from typing import List, Any, Dict

from .reliability import check_reliability
from .formatter import (
    format_trait_scores,
    level_label_qcm,
    build_result,
)


def calculate_qcm_scores(
    responses: List[Any],
    questions_map: Dict[int, Any],  # {question_id: Question ORM}
    max_score_per_question: int = 1,
) -> Dict:
    """
    Calcule les scores QCM par trait.

    Paramètres
    ----------
    responses               : liste des objets Response (valeur_choisie, seconds_spent)
    questions_map           : dict {question_id → Question} hydraté en amont
    max_score_per_question  : toujours 1 pour les QCM binaires (présent pour cohérence)

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

        user_val = str(r.valeur_choisie).strip().lower()
        correct_val = str(q.correct_answer).strip().lower()

        if user_val == correct_val:
            stats[q.trait]["points"] += 1
        stats[q.trait]["max_possible"] += 1

    trait_scores = format_trait_scores(stats, level_label_qcm)
    # Les réponses QCM sont des lettres ("A"/"B"...) — check_reliability tentera int()
    # et ignorera silencieusement les erreurs de parse → seul le contrôle vitesse s'applique.
    reliability = check_reliability(responses, max_score_per_question=1, total_time_seconds=total_time)

    return build_result(trait_scores, reliability, total_time, len(responses))
