# engine/psychometrics/scoring.py
"""
Calcul des scores psychométriques — ZÉRO accès DB.
Reçoit les données en paramètre, retourne un résultat structuré.

Appelé par : modules/assessment/service.py
"""
from typing import List, Any, Dict, Optional

# --- SEUILS ---
THRESHOLD_COGNITIVE_EXCELLENT = 80
THRESHOLD_COGNITIVE_STANDARD = 50
THRESHOLD_LIKERT_HIGH = 70
THRESHOLD_LIKERT_MEDIUM = 30
DEFAULT_LIKERT_MIN_SCORE = 1
MIN_SECONDS_PER_QUESTION = 2.0
DESIRABILITY_EXTREME_THRESHOLD = 70.0


def calculate_scores(
    responses: List[Any],
    questions_map: Dict[int, Any],   # {question_id: Question ORM object}
    test_type: str,                   # "cognitive" | "likert"
    max_score_per_question: int,
) -> Dict:
    """
    Calcule les scores à partir des réponses brutes.
    
    La DB est interrogée en amont (dans le service), les données
    arrivent ici déjà hydratées. Fonction 100% pure et testable.
    """
    traits = set(q.trait for q in questions_map.values())
    stats = {trait: {"points": 0, "max_possible": 0} for trait in traits}

    extreme_responses_count = 0
    total_likert_responses = 0
    total_time_spent = 0

    for response in responses:
        question = questions_map.get(response.question_id)
        if not question:
            continue

        trait = question.trait

        if hasattr(response, "seconds_spent") and response.seconds_spent:
            total_time_spent += response.seconds_spent

        if test_type == "cognitive":
            user_val = str(response.valeur_choisie).strip().lower()
            correct_val = str(question.correct_answer).strip().lower()
            if user_val == correct_val:
                stats[trait]["points"] += 1
            stats[trait]["max_possible"] += 1

        else:  # likert
            try:
                valeur_brute = int(response.valeur_choisie)
            except (ValueError, TypeError):
                continue

            total_likert_responses += 1
            if valeur_brute in (DEFAULT_LIKERT_MIN_SCORE, max_score_per_question):
                extreme_responses_count += 1

            valeur_calculee = valeur_brute
            if question.reverse:
                valeur_calculee = (DEFAULT_LIKERT_MIN_SCORE + max_score_per_question) - valeur_brute

            stats[trait]["points"] += valeur_calculee
            stats[trait]["max_possible"] += max_score_per_question

    # --- Fiabilité ---
    reliability = {"is_reliable": True, "reasons": []}
    num_responses = len(responses)

    if total_likert_responses > 0:
        extreme_ratio = (extreme_responses_count / total_likert_responses) * 100
        if extreme_ratio > DESIRABILITY_EXTREME_THRESHOLD:
            reliability["is_reliable"] = False
            reliability["reasons"].append("Biais de désirabilité (réponses trop extrêmes)")

    if num_responses > 0 and total_time_spent > 0:
        avg_time = total_time_spent / num_responses
        if avg_time < MIN_SECONDS_PER_QUESTION:
            reliability["is_reliable"] = False
            reliability["reasons"].append("Temps de réponse suspect (trop rapide)")

    # --- Rapport final ---
    trait_scores = {}
    for trait, data in stats.items():
        pct = (data["points"] / data["max_possible"]) * 100 if data["max_possible"] > 0 else 0
        trait_scores[trait] = {
            "score": round(pct, 1),
            "niveau": _get_level_label(test_type, pct),
        }

    global_avg = (
        sum(t["score"] for t in trait_scores.values()) / len(trait_scores)
        if trait_scores else 0
    )

    return {
        "traits": trait_scores,
        "global_score": round(global_avg, 1),
        "reliability": reliability,
        "meta": {
            "total_time_seconds": total_time_spent,
            "avg_seconds_per_question": round(total_time_spent / num_responses, 1) if num_responses > 0 else 0,
        },
    }


def _get_level_label(test_type: str, score: float) -> str:
    if test_type == "cognitive":
        if score >= THRESHOLD_COGNITIVE_EXCELLENT:
            return "Excellent"
        if score >= THRESHOLD_COGNITIVE_STANDARD:
            return "Standard"
        return "À renforcer"
    else:
        if score > THRESHOLD_LIKERT_HIGH:
            return "Élevé"
        if score > THRESHOLD_LIKERT_MEDIUM:
            return "Moyen"
        return "Faible"