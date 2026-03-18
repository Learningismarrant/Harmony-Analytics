# engine/psychometrics/scoring.py
"""
Dispatcher psychométrique — ZÉRO accès DB.

Route les réponses vers le scorer adapté selon le type de test :
  - "likert"  → scoring_likert.calculate_likert_scores()
  - "qcm"     → scoring_qcm.calculate_qcm_scores()
  - "Ipsatif" → tirt_scoring.calculate_tirt_scores()

Appelé par : modules/assessment/service.py
"""
from typing import List, Any, Dict

from .scoring_likert import calculate_likert_scores
from .scoring_qcm import calculate_qcm_scores


def calculate_scores(
    responses: List[Any],
    questions_map: Dict[int, Any],  # {question_id: Question ORM}
    test_type: str,                  # "likert" | "qcm"
    max_score_per_question: int,
) -> Dict:
    """
    Point d'entrée unique pour le scoring psychométrique.

    Délègue au scorer spécialisé selon test_type.
    Lève ValueError si test_type est inconnu.
    """
    if test_type == "likert":
        return calculate_likert_scores(responses, questions_map, max_score_per_question)

    if test_type == "qcm":
        return calculate_qcm_scores(responses, questions_map, max_score_per_question)

    raise ValueError(
        f"Type de test inconnu : '{test_type}'. "
        "Valeurs acceptées : likert, qcm."
    )