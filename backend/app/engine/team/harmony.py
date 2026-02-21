# engine/team/harmony.py
"""
Calcul de la dynamique d'équipe — ZÉRO accès DB.
Reçoit une liste de snapshots psychométriques, retourne un HarmonyResult.

Modèles implémentés :
- Modèle disjonctif : min(agreeableness) — le Jerk Filter
- Modèle additif    : mean(emotional_stability)
- Modèle variance   : std(conscientiousness) — Faultlines
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class HarmonyResult:
    performance: float          # 0-100 : capacité à délivrer
    cohesion: float             # 0-100 : capacité à cohabiter
    min_agreeableness: float    # Jerk Filter — input pour F_team
    sigma_conscientiousness: float  # Faultline risk
    mean_emotional_stability: float
    mean_gca: float
    friction_penalty: float


def compute(crew_snapshots: List[Dict]) -> HarmonyResult:
    """
    Calcule la dynamique d'équipe depuis les psychometric_snapshots.

    Args:
        crew_snapshots: Liste de psychometric_snapshot (JSON) des membres actifs.
                        Chaque snapshot vient de CrewProfile.psychometric_snapshot.
    """
    if len(crew_snapshots) < 2:
        return HarmonyResult(
            performance=0, cohesion=0,
            min_agreeableness=0, sigma_conscientiousness=0,
            mean_emotional_stability=0, mean_gca=0, friction_penalty=0
        )

    # Extraction des vecteurs
    conscientiousness = _extract(crew_snapshots, "big_five", "conscientiousness")
    agreeableness = _extract(crew_snapshots, "big_five", "agreeableness")
    emotional_stability = _extract(crew_snapshots, "big_five", "emotional_stability")
    gca = _extract(crew_snapshots, "cognitive", "gca_score")

    # --- PILIER 1 : PERFORMANCE (Taskwork) ---
    # "Can we do the job?"
    avg_gca = np.mean(gca) if gca else 50
    avg_cons = np.mean(conscientiousness) if conscientiousness else 50
    performance = round((avg_gca * 0.6) + (avg_cons * 0.4), 1)

    # --- PILIER 2 : COHÉSION (Teamwork) ---
    # "Will we kill each other?"

    # Jerk Filter : une seule personne désagréable détruit la cohésion
    min_agree = np.min(agreeableness) if agreeableness else 50

    # Maillon faible émotionnel : on regarde le MAX de neuroticism (= MIN de stabilité)
    mean_es = np.mean(emotional_stability) if emotional_stability else 50

    # Friction des standards : variance de conscienciosité
    std_cons = np.std(conscientiousness) if len(conscientiousness) > 1 else 0
    friction_penalty = max(0.0, (std_cons - 10) * 2)

    cohesion = (min_agree * 0.4) + (mean_es * 0.4) - friction_penalty + 20
    cohesion = round(max(0.0, min(100.0, cohesion)), 1)

    return HarmonyResult(
        performance=performance,
        cohesion=cohesion,
        min_agreeableness=round(float(min_agree), 1),
        sigma_conscientiousness=round(float(std_cons), 1),
        mean_emotional_stability=round(float(mean_es), 1),
        mean_gca=round(float(avg_gca), 1),
        friction_penalty=round(float(friction_penalty), 1),
    )


def compute_delta(
    current_snapshots: List[Dict],
    candidate_snapshot: Dict
) -> Dict:
    """
    Calcule l'impact d'un candidat sur la dynamique d'équipe.
    Utilisé par engine/recruitment/simulator.py pour le What-If.

    Returns:
        dict avec delta par composante F_team
    """
    before = compute(current_snapshots)
    after = compute(current_snapshots + [candidate_snapshot])

    return {
        "f_team_before": before.cohesion,
        "f_team_after": after.cohesion,
        "f_team_delta": round(after.cohesion - before.cohesion, 1),

        "jerk_filter_delta": round(after.min_agreeableness - before.min_agreeableness, 1),
        "faultline_risk_delta": round(after.sigma_conscientiousness - before.sigma_conscientiousness, 1),
        "emotional_buffer_delta": round(after.mean_emotional_stability - before.mean_emotional_stability, 1),
        "performance_delta": round(after.performance - before.performance, 1),

        # Flags automatiques
        "flags": _generate_flags(before, after),
    }


def _generate_flags(before: HarmonyResult, after: HarmonyResult) -> List[str]:
    flags = []
    if after.min_agreeableness < before.min_agreeableness:
        flags.append("JERK_FILTER_TRIGGERED: Ce candidat devient le maillon le plus bas en agréabilité.")
    if after.sigma_conscientiousness > before.sigma_conscientiousness + 5:
        flags.append("FAULTLINE_RISK: Augmentation significative de la friction des standards.")
    if after.cohesion < before.cohesion - 10:
        flags.append("COHESION_DROP: Impact négatif fort sur la cohésion d'équipe.")
    if after.cohesion > before.cohesion + 5:
        flags.append("COHESION_BOOST: Ce candidat améliore la dynamique d'équipe.")
    return flags


def _extract(snapshots: List[Dict], category: str, trait: str) -> List[float]:
    """Extrait un vecteur de scores depuis les snapshots, ignore les valeurs manquantes."""
    return [
        s[category][trait]
        for s in snapshots
        if s.get(category, {}).get(trait) is not None
    ]