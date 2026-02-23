# engine/benchmarking/diagnosis.py
"""
Diagnostic combiné équipe — Matrice Performance × Cohésion

Migré depuis engine/team/diagnosis.py (supprimé avec engine/team/).
Ce module est la source unique pour les diagnostics textuels et les
indices composites (TVI, HCD) utilisés par le dashboard crew.

Dépendances supprimées :
    - engine.team.harmony (remplacé par engine.recruitment.f_team)
    - Les métriques arrivent ici déjà calculées par f_team.compute_baseline()
      et mappées via crew/service._to_harmony_metrics()

Architecture :
    crew/service.get_full_dashboard()
        → f_team.compute_baseline()           → FTeamResult
        → _to_harmony_metrics(f_team_result)  → harmony_metrics dict
        → diagnosis.generate_combined_diagnosis(harmony_metrics, weather)
        → FullDiagnosisOut

    benchmarking/matrice.py appelle directement generate_matrix_diagnosis()
    pour afficher le quadrant P×C dans le sociogramme.

Sources :
    Hackman, J.R. (2002). Leading Teams. Harvard Business School Press.
    Kozlowski, S.W.J. & Bell, B.S. (2003). Work groups and teams in
      organizations. Handbook of Industrial, Organizational, and
      Organizational Psychology, vol 12.
    Tuckman, B.W. (1965). Developmental sequence in small groups.
      Psychological Bulletin, 63(6).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


# ── Seuils psychométriques ────────────────────────────────────────────────────

HIGH_PERF     = 70.0
MED_PERF      = 50.0
HIGH_COHESION = 70.0
MED_COHESION  = 40.0

TVI_CRITICAL  = 60.0
TVI_HIGH      = 45.0
TVI_MEDIUM    = 25.0

HCD_CRITICAL  = 65.0
HCD_HIGH      = 45.0
HCD_MEDIUM    = 25.0

WEATHER_DAYS_FULL_CONFIDENCE = 7
WEATHER_NEUTRAL_BASELINE     = 3.0


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class MatrixDiagnosis:
    """
    Diagnostic issu de la matrice Performance × Cohésion (2×3 quadrants).
    Utilisé par le sociogramme pour la légende du quadrant courant.
    """
    quadrant:          str    # ex: "HIGH_PERF_HIGH_COHESION"
    crew_type_label:   str    # ex: "Équipe Elite"
    description:       str
    risk_signal:       str    # "none" | "social" | "performance" | "both"


@dataclass
class FullDiagnosis:
    """
    Diagnostic complet combinant harmonie psychométrique + pulses (weather).

    crew_type          → catégorie qualitative de l'équipage
    risk_level         → "low" | "medium" | "high" | "critical"
    volatility_index   → TVI ∈ [0, 100] (Team Volatility Index)
    hidden_conflict    → HCD ∈ [0, 100] (Hidden Conflict Detector)
    short_term_prediction → texte prédictif 30 jours
    recommended_action    → action prioritaire selon crew_type × risk_level
    early_warning         → signal faible (conflit latent détecté)
    """
    crew_type:             str
    risk_level:            str
    volatility_index:      float
    hidden_conflict:       float
    short_term_prediction: str
    recommended_action:    str
    early_warning:         str


# ── Matrice Performance × Cohésion ───────────────────────────────────────────

def generate_matrix_diagnosis(perf: float, cohesion: float) -> MatrixDiagnosis:
    """
    Diagnostic basé sur la matrice 3×3 Performance × Cohésion.

    Args:
        perf    : score de performance 0-100 (f_team.score ou vessel_snapshot)
        cohesion: score de cohésion sociale 0-100

    Returns:
        MatrixDiagnosis avec quadrant, label et description orientée action.

    Matrice :
        P↑ C↑  → ELITE CREW
        P↑ C~  → HIGH OUTPUT / FRAGILE SOCIAL
        P↑ C↓  → HIGH RISK SOCIAL
        P~ C↑  → SOCIAL BUT UNDERPOWERED
        P~ C~  → STANDARD CREW
        P~ C↓  → VULNERABLE
        P↓ C↑  → CONVIVIAL BUT INEFFECTIVE
        P↓ C~  → STRUGGLING
        P↓ C↓  → BREAKDOWN ZONE
    """
    if perf >= HIGH_PERF and cohesion >= HIGH_COHESION:
        return MatrixDiagnosis(
            quadrant="HIGH_PERF_HIGH_COHESION",
            crew_type_label="Équipe Elite",
            description=(
                "Performance élevée et climat social résilient. "
                "Équipage rare — protéger la composition actuelle."
            ),
            risk_signal="none",
        )
    elif perf >= HIGH_PERF and cohesion >= MED_COHESION:
        return MatrixDiagnosis(
            quadrant="HIGH_PERF_MED_COHESION",
            crew_type_label="Performant & Stable",
            description=(
                "Capacité à délivrer avec une cohésion satisfaisante. "
                "Surveiller les tensions liées aux standards de travail."
            ),
            risk_signal="none",
        )
    elif perf >= HIGH_PERF and cohesion < MED_COHESION:
        return MatrixDiagnosis(
            quadrant="HIGH_PERF_LOW_COHESION",
            crew_type_label="Haut Risque Social",
            description=(
                "Performance élevée mais climat social fragile. "
                "Conflit latent probable — le résultat masque la tension."
            ),
            risk_signal="social",
        )
    elif perf >= MED_PERF and cohesion >= HIGH_COHESION:
        return MatrixDiagnosis(
            quadrant="MED_PERF_HIGH_COHESION",
            crew_type_label="Social mais Sous-Performant",
            description=(
                "Bonne ambiance mais productivité en dessous du potentiel. "
                "Introduire des challenges de performance sans casser la cohésion."
            ),
            risk_signal="performance",
        )
    elif perf >= MED_PERF and cohesion >= MED_COHESION:
        return MatrixDiagnosis(
            quadrant="MED_PERF_MED_COHESION",
            crew_type_label="Équipe Fonctionnelle",
            description=(
                "Performance et cohésion dans la moyenne. "
                "Potentiel de progression avec un recrutement ciblé."
            ),
            risk_signal="none",
        )
    elif perf >= MED_PERF and cohesion < MED_COHESION:
        return MatrixDiagnosis(
            quadrant="MED_PERF_LOW_COHESION",
            crew_type_label="Équipe Vulnérable",
            description=(
                "Performance acceptable mais climat social dégradé. "
                "Risque de turnover élevé en fin de saison."
            ),
            risk_signal="social",
        )
    elif perf < MED_PERF and cohesion >= HIGH_COHESION:
        return MatrixDiagnosis(
            quadrant="LOW_PERF_HIGH_COHESION",
            crew_type_label="Convivial mais Peu Efficace",
            description=(
                "Ambiance positive mais résultats insuffisants. "
                "Déficit de compétences ou de leadership technique."
            ),
            risk_signal="performance",
        )
    elif perf < MED_PERF and cohesion >= MED_COHESION:
        return MatrixDiagnosis(
            quadrant="LOW_PERF_MED_COHESION",
            crew_type_label="Équipe en Difficulté",
            description=(
                "Ni performante ni dysfonctionnelle. "
                "Recrutement ciblé sur des profils à fort GCA et Conscienciosité."
            ),
            risk_signal="performance",
        )
    else:  # perf < MED_PERF and cohesion < MED_COHESION
        return MatrixDiagnosis(
            quadrant="LOW_PERF_LOW_COHESION",
            crew_type_label="Zone de Crise",
            description=(
                "Performance et cohésion insuffisantes. "
                "Intervention immédiate requise — recomposition partielle ou totale."
            ),
            risk_signal="both",
        )


# ── Diagnostic combiné (harmonie + pulses) ────────────────────────────────────

def generate_combined_diagnosis(
    harmony_metrics: Dict,
    weather: Dict,
) -> Dict:
    """
    Diagnostic complet combinant les métriques psychométriques et les pulses.

    Calcule :
        TVI (Team Volatility Index) — instabilité prévisionnelle
        HCD (Hidden Conflict Detector) — tension silencieuse

    Args:
        harmony_metrics : dict issu de crew/service._to_harmony_metrics()
            {
                "performance": float,
                "cohesion": float,
                "risk_factors": {
                    "conscientiousness_divergence": float,
                    "weakest_link_stability": float
                }
            }
        weather : dict issu de crew/service._compute_weather_trend()
            {
                "average": float,       # 1-5
                "std": float,
                "days_observed": int,
                "response_count": int,
                "status": str
            }

    Returns:
        Dict compatible avec FullDiagnosisOut schema.
    """
    perf         = harmony_metrics.get("performance", 50.0)
    cohesion     = harmony_metrics.get("cohesion", 50.0)
    risk         = harmony_metrics.get("risk_factors", {})
    c_divergence = risk.get("conscientiousness_divergence", 0.0)
    wl_stability = risk.get("weakest_link_stability", 50.0)

    w_avg          = weather.get("average", WEATHER_NEUTRAL_BASELINE)
    weather_days   = weather.get("days_observed", 0)
    weather_std    = weather.get("std", 0.0)

    # ── Pondération dynamique du weather (confiance proportionnelle à n jours) ──
    weather_confidence = min(1.0, weather_days / WEATHER_DAYS_FULL_CONFIDENCE)
    effective_weather  = (
        w_avg * weather_confidence +
        WEATHER_NEUTRAL_BASELINE * (1 - weather_confidence)
    )

    # ── Hidden Conflict Detector (HCD) ───────────────────────────────────────
    # Signal : gap perf/cohésion (tension silencieuse), divergence C,
    # instabilité du maillon faible, météo basse
    hcd = (
        max(0, perf - cohesion) * 0.35 +
        c_divergence             * 0.25 +
        (100 - wl_stability)     * 0.25 +
        (5 - effective_weather)  * 0.15
    )
    hidden_conflict = round(max(0.0, min(100.0, hcd)), 1)

    # ── Team Volatility Index (TVI) ───────────────────────────────────────────
    # Signal : instabilité émotionnelle du maillon faible, divergence C,
    # météo basse, variance météo
    tvi = (
        (100 - wl_stability)     * 0.35 +
        c_divergence             * 0.25 +
        (5 - effective_weather)  * 20 * 0.25 +
        weather_std              * 10 * 0.15
    )
    volatility = round(max(0.0, min(100.0, tvi)), 1)

    crew_type          = _classify_crew(perf, cohesion, volatility, hidden_conflict)
    risk_level         = _get_risk_level(volatility, cohesion, hidden_conflict)
    prediction         = _generate_prediction(volatility, hidden_conflict, effective_weather)
    recommended_action = _get_recommended_action(crew_type, risk_level)
    early_warning      = _check_early_warning(perf, cohesion, effective_weather, weather_std)

    return {
        "crew_type":             crew_type,
        "risk_level":            risk_level,
        "volatility_index":      volatility,
        "hidden_conflict":       hidden_conflict,
        "short_term_prediction": prediction,
        "recommended_action":    recommended_action,
        "early_warning":         early_warning,
    }


# ── Fonctions de classification ───────────────────────────────────────────────

def _classify_crew(
    perf: float, cohesion: float,
    volatility: float, hidden_conflict: float,
) -> str:
    if perf > 70 and cohesion > 70 and volatility < 25 and hidden_conflict < 25:
        return "ELITE CREW"
    elif perf > 70 and (cohesion < 70 or volatility > 25 or hidden_conflict > 25):
        return "HIGH OUTPUT / FRAGILE"
    elif perf < 60 and cohesion > 65 and hidden_conflict < 45:
        return "SOCIAL BUT UNDERPOWERED"
    elif (cohesion < 40 or hidden_conflict > 45) and volatility > 45:
        return "AT RISK CREW"
    elif perf < 50 and cohesion < 40 and volatility > 60 and hidden_conflict > 65:
        return "BREAKDOWN ZONE"
    else:
        return "STANDARD CREW"


def _generate_prediction(
    volatility: float, hidden_conflict: float, effective_weather: float
) -> str:
    if hidden_conflict > HCD_CRITICAL:
        return "Critique : conflit latent susceptible d'éclater sous 30 jours."
    elif volatility > TVI_CRITICAL:
        return "Forte probabilité de conflit ou burnout dans les 30 jours."
    elif volatility > TVI_HIGH or hidden_conflict > HCD_HIGH:
        return "Tensions croissantes prévisibles lors des pics de charge."
    elif effective_weather < 2.5:
        return "Détérioration du climat émotionnel attendue si la pression augmente."
    else:
        return "Stable — aucun risque majeur détecté."


def _get_risk_level(
    volatility: float, cohesion: float, hidden_conflict: float
) -> str:
    if hidden_conflict > HCD_CRITICAL or volatility > TVI_CRITICAL or cohesion < 30:
        return "critical"
    elif hidden_conflict > HCD_HIGH or volatility > TVI_HIGH or cohesion < 40:
        return "high"
    elif hidden_conflict > HCD_MEDIUM or volatility > TVI_MEDIUM or cohesion < 50:
        return "medium"
    return "low"


def _get_recommended_action(crew_type: str, risk_level: str) -> str:
    actions = {
        "ELITE CREW": {
            "low":      "Maintenir les pratiques actuelles. Envisager un plan de succession.",
            "medium":   "Surveiller la charge de travail pour éviter la complacence.",
            "high":     "Préparer des scénarios haute pression ; soutien émotionnel disponible.",
            "critical": "Revue de leadership immédiate requise.",
        },
        "HIGH OUTPUT / FRAGILE": {
            "low":      "Aligner les attentes et réduire l'ambiguïté de rôle.",
            "medium":   "Check-in de prévention des conflits ; clarifier les standards.",
            "high":     "Atelier de cohésion d'équipe obligatoire.",
            "critical": "Remplacer le maillon émotionnel le plus faible ou réduire la charge.",
        },
        "SOCIAL BUT UNDERPOWERED": {
            "low":      "Introduire des défis de performance pour augmenter l'engagement.",
            "medium":   "Évaluation des compétences et formation ciblée.",
            "high":     "Restructurer les rôles en fonction des compétences réelles.",
            "critical": "Recrutement externe ou coaching spécialisé.",
        },
        "AT RISK CREW": {
            "low":      "Session d'alignement d'équipe immédiate.",
            "medium":   "Médiation externe et réduction de la charge.",
            "high":     "Prise en main du leadership ; coaching individuel.",
            "critical": "Remplacement partiel imminent — anticiper la recomposition.",
        },
        "BREAKDOWN ZONE": {
            "low":      "Revue complète de l'équipe et restructuration.",
            "medium":   "Intervention externe urgente.",
            "high":     "Remplacement des rôles critiques en urgence.",
            "critical": "Dissolution et reconstruction de l'équipage.",
        },
        "STANDARD CREW": {
            "low":      "Recrutement ciblé pour élever le niveau collectif.",
            "medium":   "Identifier et développer les points de progression prioritaires.",
            "high":     "Évaluation individuelle et plan de développement.",
            "critical": "Intervention immédiate sur les facteurs de risque identifiés.",
        },
    }
    return actions.get(crew_type, {}).get(
        risk_level, "Analyser les dynamiques et les tendances de météo."
    )


def _check_early_warning(
    perf: float, cohesion: float,
    effective_weather: float, weather_std: float,
) -> str:
    """
    Détecte le conflit latent (performance maintenue, cohésion se dégradant).
    Signal faible mais précoce — à surveiller avant que le TVI monte.
    """
    if (effective_weather < 3.0 and perf > 60 and MED_COHESION < cohesion < HIGH_COHESION) \
            or weather_std > 1.2:
        return (
            "Conflit latent détecté — performance soutenue mais "
            "climat émotionnel en dégradation silencieuse."
        )
    return "Aucun signal d'alerte précoce."