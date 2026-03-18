# engine/psychometrics/reliability.py
"""
Contrôles de fiabilité psychométrique — ZÉRO accès DB.

Deux contrôles partagés par les scorers likert et qcm :
  - vitesse de réponse suspecte (trop rapide)
  - biais de désirabilité sociale (réponses extrêmes systématiques)

"""
from typing import List, Any, Dict

MIN_SECONDS_PER_QUESTION = 2.0
DESIRABILITY_EXTREME_THRESHOLD = 70.0  # % réponses à 1 ou max avant alerte


def check_reliability(
    responses: List[Any],
    max_score_per_question: int,
    total_time_seconds: float,
) -> Dict:
    """
    Évalue la fiabilité globale d'une session de test.

    Paramètres
    ----------
    responses               : liste des objets réponse (ont .valeur_choisie)
    max_score_per_question  : score maximum possible par item (ex. 5 ou 7)
    total_time_seconds      : somme des seconds_spent sur toutes les réponses

    Retourne
    --------
    {"is_reliable": bool, "reasons": [str]}
    """
    result: Dict = {"is_reliable": True, "reasons": []}
    num_responses = len(responses)
    if num_responses == 0:
        return result

    # -- Vitesse suspecte ------------------------------------------------
    avg_time = total_time_seconds / num_responses
    if total_time_seconds > 0 and avg_time < MIN_SECONDS_PER_QUESTION:
        result["is_reliable"] = False
        result["reasons"].append("Temps de réponse suspect (trop rapide)")

    # -- Biais désirabilité (extrêmes 1 / max) ---------------------------
    extreme_count = 0
    for r in responses:
        try:
            v = int(r.valeur_choisie)
            if v in (1, max_score_per_question):
                extreme_count += 1
        except (ValueError, TypeError):
            pass

    if extreme_count > 0:
        extreme_ratio = (extreme_count / num_responses) * 100
        if extreme_ratio > DESIRABILITY_EXTREME_THRESHOLD:
            result["is_reliable"] = False
            result["reasons"].append("Biais de désirabilité (réponses trop extrêmes)")

    return result
