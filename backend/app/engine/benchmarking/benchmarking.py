# Service de benchmarking des scores psychométriques - app/services/engine/benchmarking_engine/benchmark.py
from sqlalchemy.orm import Session
from sqlalchemy import  cast, String,func

from app.models import TestResult, User

from app.services.content.sme_profiles import  TRAIT_POLARITY
from app.services.engine.psychometrics_engine.stats import calculate_relative_percentile


def _get_benchmarking_stat(db: Session, trait: str, user_score: float, target_pos_key: str, test_id: int) -> str:
    """
    Compare le score de l'user avec le pool pertinent.
    target_pos_key : Le poste cible utilisé pour la comparaison (ex: 'captain')
    """
    
    # 1. Formatage pour matcher la DB (souvent stocké en Title Case ou Capitalize)
    # Ex: 'captain' -> 'Captain'
    formatted_position = target_pos_key.capitalize() if " " not in target_pos_key else target_pos_key.title()
    
    # 2. Requête Comparée
    # On sélectionne les scores des utilisateurs qui visent le poste cible (target_pos_key)
    candidates_scores = db.query(TestResult.scores).join(User).filter(
        TestResult.test_id == test_id,
        func.lower(cast(User.position_targeted, String)) == formatted_position.lower()
    ).all()
    
    pool_values = []
    for row in candidates_scores:
        if row.scores and trait in row.scores:
            val = row.scores[trait]
            if isinstance(val, dict):
                pool_values.append(val.get("score", 0))
            else:
                pool_values.append(val)
    
    if not pool_values:
        return "Données insuffisantes"

    # 3. Calcul du percentile
    percentile = calculate_relative_percentile(user_score, pool_values)

    # 4. Ajustement Polarité & Affichage (Identique à ton code)
    polarity = TRAIT_POLARITY.get(trait, "high")
    display_score = percentile
    
    if polarity == "low":
        display_score = 100 - percentile
    elif polarity == "moderate":
        distance_from_center = abs(percentile - 50) 
        display_score = 100 - (distance_from_center * 2)
    
    if display_score >= 90: return "Référence du secteur"
    if display_score >= 75: return "Profil dominant"
    if display_score >= 45: return "Dans les standards"
    if display_score >= 25: return "Marge de progression"
    return "Potentiel à développer"