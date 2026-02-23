# engine/recruitment/f_lmx.py
"""
F_lmx — Compatibilité Leadership (Leader-Member eXchange / Captain's Shadow)

Mesure l'adéquation entre le style de commandement du capitaine
et les préférences du candidat en matière d'autonomie, de feedback
et de structure.

Le contexte yachting est critique ici : en mer, le capitaine a une
autorité totale (maritime law). Un marin qui a besoin d'autonomie
avec un capitaine très directif = turnover garanti.

Formule de base (Temps 1) :
    F_lmx = (1 - ‖L_capt - V_crew‖ / d_max) × 100

    L_capt  = vecteur style capitaine [autonomy_given, feedback_style, structure_imposed]
    V_crew  = vecteur préférences candidat [autonomy_pref, feedback_pref, structure_pref]
    d_max   = √3 (distance maximale dans un espace [0,1]³)

    Plus la distance est petite → plus F_lmx est élevé.
    Distance = 0 → F_lmx = 100 (adéquation parfaite)
    Distance = d_max → F_lmx = 0 (opposition totale)

Dimensions du vecteur leadership :
    ┌────────────────────┬──────────────────────────────────────────────┐
    │ autonomy           │ 0 = directif strict / 1 = autonomie totale  │
    │ feedback_style     │ 0 = silencieux / 1 = coaching intensif      │
    │ structure_imposed  │ 0 = flexible / 1 = procédures rigides       │
    └────────────────────┴──────────────────────────────────────────────┘

Évolution Temps 2 :
    - Intégration du score leadership_satisfaction des surveys
      (valide ou invalide la prédiction F_lmx)
    - Pondération asymétrique des dimensions par poste :
      le Chef a besoin de plus d'autonomie que un steward
    - Modèle d'adaptation : F_lmx évolue avec le temps (LMX quality)
    - Détection de profils incompatibles structurels (ex: dominant
      vs dominant → conflit inévitable)

Sources académiques :
    Graen, G.B. & Uhl-Bien, M. (1995). Relationship-based approach
    to leadership. Leadership Quarterly, 6(2).

    Dulebohn, J.H. et al. (2012). A meta-analysis of LMX and its
    antecedents and consequences. Journal of Management, 38(6).

    Le contexte de l'isolement maritime amplifie l'effet LMX :
    Sandal, G.M. et al. (2006). Human challenges in polar and space
    environments. Reviews in Environmental Science & Bio/Technology.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import math


# ── Pondérations des dimensions du vecteur ───────────────────────────────────

# Poids de chaque dimension dans le calcul de la distance
# Par défaut = distribution uniforme (Temps 1)
# Temps 2 : ajustement par YachtPosition
W_AUTONOMY   = 1.0 / 3.0
W_FEEDBACK   = 1.0 / 3.0
W_STRUCTURE  = 1.0 / 3.0

# Distance maximale dans un espace [0,1]³ (non pondéré)
D_MAX_UNIFORM = math.sqrt(3)

# Seuils d'alerte
CRITICAL_DISTANCE_THRESHOLD = 0.70   # Au-delà → incompatibilité structurelle
HIGH_DISTANCE_THRESHOLD     = 0.50   # Entre 0.5 et 0.7 → tension probable
LOW_DATA_THRESHOLD          = 0.50   # Si < 50% données capitaine → faible confiance


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class DimensionGap:
    """
    Écart sur une dimension spécifique du vecteur leadership.
    Utile pour identifier quelle dimension crée l'incompatibilité.
    """
    dimension: str              # "autonomy" | "feedback" | "structure"
    captain_value: float        # Style capitaine (0-1)
    crew_preference: float      # Préférence candidat (0-1)
    gap: float                  # |L_capt - V_crew| (0-1)
    gap_direction: str          # "CAPTAIN_MORE" | "CREW_MORE" | "ALIGNED"
    gap_label: str              # Description lisible


@dataclass
class VectorDetail:
    """Détail des deux vecteurs comparés."""
    # Capitaine
    captain_autonomy_given: float
    captain_feedback_style: float
    captain_structure_imposed: float
    captain_data_completeness: float   # 0-1, % de dimensions renseignées

    # Candidat
    crew_autonomy_preference: float
    crew_feedback_preference: float
    crew_structure_preference: float
    crew_data_completeness: float


@dataclass
class DistanceDetail:
    """Détail du calcul de distance euclidienne."""
    euclidean_distance: float     # Distance brute (0 à d_max)
    d_max: float                  # Distance max (= √3 sans pondération)
    normalized_distance: float    # Distance normalisée (0 à 1)
    compatibility: float          # 1 - normalized_distance (0 à 1)
    compatibility_label: str      # "EXCELLENT" | "GOOD" | "TENSION" | "CRITICAL"


@dataclass
class FLmxResult:
    """
    Résultat complet du calcul F_lmx.

    score        → valeur finale 0-100, injectée dans l'équation maîtresse
    vectors      → détail des deux vecteurs comparés
    distance     → détail du calcul géométrique
    dimensions   → écart par dimension (diagnostic précis)
    data_quality → 0.0-1.0
    flags        → alertes (incompatibilité critique, données manquantes...)
    """
    score: float

    vectors: VectorDetail
    distance: DistanceDetail
    dimensions: list[DimensionGap] = field(default_factory=list)

    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Extraction des préférences candidat depuis le snapshot ────────────────────

def _extract_crew_preferences(candidate_snapshot: Dict) -> tuple[float, float, float, float]:
    """
    Extrait les préférences de leadership du candidat depuis le snapshot.

    Priorité :
    1. snapshot.leadership_preferences (dédié — calculé par snapshot.py)
    2. Dérivation depuis Big Five :
       - autonomy_pref ≈ Openness (curiosité, indépendance) + (1 - Agreeableness/2)
       - feedback_pref ≈ Openness (réceptivité aux idées)
       - structure_pref ≈ Conscientiousness (besoin d'ordre)
    3. Fallback 0.5 (neutralité)

    Returns:
        (autonomy, feedback, structure, completeness)
        completeness = ratio de dimensions disponibles sans fallback
    """
    lp = candidate_snapshot.get("leadership_preferences") or {}

    fallback_count = 0

    # Autonomy preference
    autonomy = lp.get("autonomy_preference")
    if autonomy is None:
        bf = candidate_snapshot.get("big_five") or {}
        o = bf.get("openness")
        a = bf.get("agreeableness")
        if isinstance(o, dict): o = o.get("score")
        if isinstance(a, dict): a = a.get("score")
        if o is not None:
            autonomy = min(1.0, (float(o) / 100.0) * 0.6 + (1 - float(a or 50) / 100.0) * 0.4)
        else:
            autonomy = 0.5
            fallback_count += 1

    # Feedback preference
    feedback = lp.get("feedback_preference")
    if feedback is None:
        bf = candidate_snapshot.get("big_five") or {}
        o = bf.get("openness")
        if isinstance(o, dict): o = o.get("score")
        if o is not None:
            feedback = float(o) / 100.0
        else:
            feedback = 0.5
            fallback_count += 1

    # Structure preference
    structure = lp.get("structure_preference")
    if structure is None:
        bf = candidate_snapshot.get("big_five") or {}
        c = bf.get("conscientiousness")
        if isinstance(c, dict): c = c.get("score")
        if c is not None:
            structure = float(c) / 100.0
        else:
            structure = 0.5
            fallback_count += 1

    completeness = 1.0 - (fallback_count / 3.0)
    return float(autonomy), float(feedback), float(structure), completeness


def _extract_captain_vector(captain_vector: Dict) -> tuple[float, float, float, float]:
    """
    Extrait le vecteur capitaine depuis Yacht.captain_leadership_vector.

    Attendu :
    {
        "autonomy_given": 0.6,
        "feedback_style": 0.4,
        "structure_imposed": 0.7
    }

    Returns:
        (autonomy, feedback, structure, completeness)
    """
    fallback_count = 0

    autonomy = captain_vector.get("autonomy_given")
    if autonomy is None:
        autonomy = 0.5
        fallback_count += 1

    feedback = captain_vector.get("feedback_style")
    if feedback is None:
        feedback = 0.5
        fallback_count += 1

    structure = captain_vector.get("structure_imposed")
    if structure is None:
        structure = 0.5
        fallback_count += 1

    completeness = 1.0 - (fallback_count / 3.0)
    return float(autonomy), float(feedback), float(structure), completeness


# ── Analyse par dimension ─────────────────────────────────────────────────────

def _analyze_dimension(dim: str, capt: float, crew: float, threshold: float = 0.30) -> DimensionGap:
    gap = abs(capt - crew)
    direction = "ALIGNED"
    if gap > threshold:
        direction = "CAPTAIN_MORE" if capt > crew else "CREW_MORE"

    # Labels lisibles
    labels = {
        "autonomy": {
            "ALIGNED": "Niveau d'autonomie compatible",
            "CAPTAIN_MORE": "Le capitaine délègue plus que le candidat ne souhaite",
            "CREW_MORE": "Le candidat veut plus d'autonomie que le capitaine n'en donne",
        },
        "feedback": {
            "ALIGNED": "Style de feedback compatible",
            "CAPTAIN_MORE": "Le capitaine donne plus de feedback que le candidat n'en attend",
            "CREW_MORE": "Le candidat attend plus de coaching que le capitaine n'en donne",
        },
        "structure": {
            "ALIGNED": "Niveau de structure compatible",
            "CAPTAIN_MORE": "Le capitaine est plus procédurier que le candidat ne préfère",
            "CREW_MORE": "Le candidat préfère plus de structure que le capitaine n'en impose",
        },
    }

    return DimensionGap(
        dimension=dim,
        captain_value=round(capt, 3),
        crew_preference=round(crew, 3),
        gap=round(gap, 3),
        gap_direction=direction,
        gap_label=labels.get(dim, {}).get(direction, ""),
    )


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    captain_vector: Dict,
) -> FLmxResult:
    """
    Calcule F_lmx pour un candidat avec un capitaine donné.

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        captain_vector     : Yacht.captain_leadership_vector
                             {"autonomy_given": 0.6, "feedback_style": 0.4, "structure_imposed": 0.7}
                             Si vide → données manquantes, flag LOW_CONFIDENCE

    Returns:
        FLmxResult avec score final et analyse détaillée par dimension.
    """
    flags: list[str] = []
    data_quality = 1.0

    # ── Extraction ────────────────────────────────────────────
    capt_a, capt_f, capt_s, capt_completeness = _extract_captain_vector(captain_vector)
    crew_a, crew_f, crew_s, crew_completeness  = _extract_crew_preferences(candidate_snapshot)

    # ── Gestion données manquantes ────────────────────────────
    if capt_completeness < LOW_DATA_THRESHOLD:
        flags.append(
            f"CAPTAIN_DATA_INCOMPLETE: vecteur capitaine à {capt_completeness*100:.0f}% "
            f"— configurer Yacht.captain_leadership_vector pour un score fiable"
        )
        data_quality -= 0.35

    if crew_completeness < LOW_DATA_THRESHOLD:
        flags.append(
            "CREW_PREFERENCES_ESTIMATED: préférences candidat dérivées du Big Five "
            "(leadership_preferences non disponible)"
        )
        data_quality -= 0.20

    # ── Analyse par dimension ─────────────────────────────────
    dim_gaps = [
        _analyze_dimension("autonomy",  capt_a, crew_a),
        _analyze_dimension("feedback",  capt_f, crew_f),
        _analyze_dimension("structure", capt_s, crew_s),
    ]

    # Flags par dimension si écart critique
    for d in dim_gaps:
        if d.gap > 0.50:
            flags.append(f"CRITICAL_GAP_{d.dimension.upper()}: écart de {d.gap:.2f} → {d.gap_label}")

    # ── Distance euclidienne pondérée ─────────────────────────
    # Pondération uniforme Temps 1 (W = 1/3 par dimension)
    dist_sq = (
        W_AUTONOMY  * (capt_a - crew_a) ** 2
        + W_FEEDBACK  * (capt_f - crew_f) ** 2
        + W_STRUCTURE * (capt_s - crew_s) ** 2
    )
    distance = math.sqrt(dist_sq)

    # D_max pour pondérations uniformes = √(1/3 + 1/3 + 1/3) = 1.0
    d_max = math.sqrt(W_AUTONOMY + W_FEEDBACK + W_STRUCTURE)
    normalized = distance / d_max

    # Label de compatibilité
    if normalized < 0.25:
        compat_label = "EXCELLENT"
    elif normalized < 0.45:
        compat_label = "GOOD"
    elif normalized < CRITICAL_DISTANCE_THRESHOLD:
        compat_label = "TENSION"
        flags.append(f"LMX_TENSION: distance normalisée = {normalized:.2f} — friction probable")
    else:
        compat_label = "CRITICAL"
        flags.append(f"LMX_CRITICAL: distance = {normalized:.2f} — incompatibilité structurelle")

    dist_detail = DistanceDetail(
        euclidean_distance=round(distance, 4),
        d_max=round(d_max, 4),
        normalized_distance=round(normalized, 4),
        compatibility=round(1.0 - normalized, 4),
        compatibility_label=compat_label,
    )

    # ── Score final ───────────────────────────────────────────
    f_lmx_raw = (1.0 - normalized) * 100.0
    score = round(max(0.0, min(100.0, f_lmx_raw)), 1)

    vectors = VectorDetail(
        captain_autonomy_given=capt_a,
        captain_feedback_style=capt_f,
        captain_structure_imposed=capt_s,
        captain_data_completeness=capt_completeness,
        crew_autonomy_preference=crew_a,
        crew_feedback_preference=crew_f,
        crew_structure_preference=crew_s,
        crew_data_completeness=crew_completeness,
    )

    formula = (
        f"F_lmx = (1 - ‖{[capt_a, capt_f, capt_s]} - {[crew_a, crew_f, crew_s]}‖ / {d_max:.3f})"
        f" = (1 - {distance:.3f}/{d_max:.3f}) × 100"
        f" = {f_lmx_raw:.1f} → {score}"
    )

    return FLmxResult(
        score=score,
        vectors=vectors,
        distance=dist_detail,
        dimensions=dim_gaps,
        data_quality=max(0.0, data_quality),
        flags=flags,
        formula_snapshot=formula,
    )