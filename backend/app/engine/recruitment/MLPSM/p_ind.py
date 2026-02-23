# engine/recruitment/p_ind.py
"""
P_ind — Performance Individuelle (Taskwork Capacity)

Prédit la capacité brute d'un candidat à exécuter les tâches techniques
de son poste, indépendamment de l'équipe ou de l'environnement.

Formule de base (Temps 1) :
    P_ind = ω₁·GCA + ω₂·C

    GCA = General Cognitive Ability (tests cognitifs)
    C   = Conscientiousness (Big Five)

    ω₁ = 0.60  → Schmidt & Hunter (1998) : GCA est le prédicteur
                   de performance le plus robuste (ρ = .51 tous postes)
    ω₂ = 0.40  → C est le seul trait Big Five à prédire la performance
                   sur tous types de postes (Barrick & Mount, 1991)

Évolution Temps 2 :
    - Intégration des années d'expérience (experience_years)
    - Pondération spécifique par YachtPosition (ajustement betas)
    - Intégration des certifications vérifiées (trust_score)
    - Séparation GCA en sous-scores (logique, numérique, verbal)

Sources académiques :
    Schmidt, F.L. & Hunter, J.E. (1998). The validity and utility of
    selection methods in personnel psychology. Psych. Bulletin, 124(2).

    Barrick, M.R. & Mount, M.K. (1991). The Big Five personality
    dimensions and job performance. Personnel Psychology, 44(1).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


# ── Pondérations internes (évoluent avec la régression Temps 2) ──────────────

OMEGA_GCA            = 0.60   # Poids capacité cognitive
OMEGA_CONSCIENTIOUSNESS = 0.40  # Poids conscienciosité

# Bonus expérience (Temps 2 — désactivé tant que la régression n'a pas validé)
EXPERIENCE_BONUS_ENABLED = False
EXPERIENCE_BONUS_CAP     = 10.0   # max +10 points pour l'expérience


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class GCADetail:
    """Détail de la capacité cognitive."""
    gca_score: float          # Score brut 0-100 (moyenne des sous-tests)
    logical_reasoning: Optional[float] = None   # Sous-score logique
    numerical_reasoning: Optional[float] = None # Sous-score numérique
    verbal_reasoning: Optional[float] = None    # Sous-score verbal
    n_cognitive_tests: int = 0                  # Nb de tests cognitifs passés


@dataclass
class ConscientiousnessDetail:
    """Détail de la conscienciosité."""
    c_score: float            # Score brut 0-100
    reliability_flag: bool = True  # False si le test n'est pas fiable


@dataclass
class ExperienceDetail:
    """Détail de l'expérience (Temps 2)."""
    years: int = 0
    bonus_applied: float = 0.0
    note: str = "Bonus expérience désactivé (Temps 1)"


@dataclass
class PIndResult:
    """
    Résultat complet du calcul P_ind.

    score        → valeur finale 0-100, injectée dans l'équation maîtresse
    gca          → détail capacité cognitive
    conscientiousness → détail trait Big Five
    experience   → détail bonus expérience (Temps 2)
    data_quality → 0.0-1.0, reflète la complétude des données d'entrée
    flags        → avertissements (ex: "GCA manquant, fallback utilisé")
    """
    score: float

    gca: GCADetail
    conscientiousness: ConscientiousnessDetail
    experience: ExperienceDetail

    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""   # Equation résolue — utile pour debug/audit


# ── Extraction des inputs depuis le psychometric_snapshot ─────────────────────

def _extract_gca(snapshot: Dict) -> GCADetail:
    """
    Extrait le GCA depuis le psychometric_snapshot.

    Priorité :
    1. snapshot.cognitive.gca_score (pré-calculé par snapshot.py)
    2. Moyenne des sous-scores cognitifs disponibles
    3. Fallback : 50.0 (médiane) avec flag

    Structure attendue dans snapshot :
    {
        "cognitive": {
            "gca_score": 72.4,
            "logical_reasoning": 75.0,
            "numerical_reasoning": 68.0,
            "verbal_reasoning": 74.0,
            "n_tests": 2
        }
    }
    """
    cog = snapshot.get("cognitive") or {}

    gca_score = cog.get("gca_score")
    logical   = cog.get("logical_reasoning")
    numerical = cog.get("numerical_reasoning")
    verbal    = cog.get("verbal_reasoning")
    n_tests   = cog.get("n_tests", 0)

    if gca_score is None:
        # Recalcul depuis les sous-scores disponibles
        sub_scores = [s for s in [logical, numerical, verbal] if s is not None]
        gca_score = sum(sub_scores) / len(sub_scores) if sub_scores else 50.0

    return GCADetail(
        gca_score=float(gca_score),
        logical_reasoning=logical,
        numerical_reasoning=numerical,
        verbal_reasoning=verbal,
        n_cognitive_tests=n_tests,
    )


def _extract_conscientiousness(snapshot: Dict) -> ConscientiousnessDetail:
    """
    Extrait la Conscienciosité depuis le psychometric_snapshot.

    Structure attendue :
    {
        "big_five": {
            "conscientiousness": {"score": 78.5, "reliable": true}
        }
    }
    """
    big_five = snapshot.get("big_five") or {}
    c_data   = big_five.get("conscientiousness") or {}

    if isinstance(c_data, dict):
        c_score  = c_data.get("score", 50.0)
        reliable = c_data.get("reliable", True)
    else:
        c_score  = float(c_data) if c_data else 50.0
        reliable = True

    return ConscientiousnessDetail(
        c_score=float(c_score),
        reliability_flag=bool(reliable),
    )


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    experience_years: int = 0,
    position_key: Optional[str] = None,  # Réservé Temps 2 (pondérations par poste)
) -> PIndResult:
    """
    Calcule P_ind pour un candidat.

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        experience_years   : années d'expérience (depuis CrewProfile.experience_years)
        position_key       : YachtPosition.value — réservé pour ajustements Temps 2

    Returns:
        PIndResult avec score final et détail complet de chaque sous-mesure

    Usage typique dans master.py :
        p_ind_result = p_ind.compute(candidate_snapshot, experience_years=crew.experience_years)
        score = p_ind_result.score
    """
    flags: list[str] = []

    # ── 1. Extraction ────────────────────────────────────────
    gca_detail = _extract_gca(candidate_snapshot)
    c_detail   = _extract_conscientiousness(candidate_snapshot)

    # ── 2. Détection de données manquantes ───────────────────
    data_quality = 1.0

    if gca_detail.n_cognitive_tests == 0:
        flags.append("GCA_MISSING: aucun test cognitif passé, score médian utilisé (50.0)")
        data_quality -= 0.35

    if not c_detail.reliability_flag:
        flags.append("C_UNRELIABLE: test conscienciosité jugé non fiable (social desirability)")
        data_quality -= 0.20

    if candidate_snapshot.get("big_five") is None:
        flags.append("BIG_FIVE_MISSING: snapshot Big Five absent, C = 50.0 par défaut")
        data_quality -= 0.15

    data_quality = max(0.0, data_quality)

    # ── 3. Calcul P_ind ──────────────────────────────────────
    gca = gca_detail.gca_score
    c   = c_detail.c_score

    p_ind_raw = (gca * OMEGA_GCA) + (c * OMEGA_CONSCIENTIOUSNESS)

    # ── 4. Bonus expérience (Temps 2 — désactivé) ────────────
    exp_detail = ExperienceDetail(years=experience_years)

    if EXPERIENCE_BONUS_ENABLED and experience_years > 0:
        # Courbe log : +3pts à 1 an, +6pts à 5 ans, +9pts à 15 ans
        import math
        bonus = min(EXPERIENCE_BONUS_CAP, math.log1p(experience_years) * 3.0)
        p_ind_raw += bonus
        exp_detail.bonus_applied = round(bonus, 2)
        exp_detail.note = f"+{bonus:.1f}pts pour {experience_years} ans d'expérience"
        flags.append(f"EXP_BONUS: +{bonus:.1f}pts ({experience_years} ans)")

    # ── 5. Clamp 0-100 ───────────────────────────────────────
    score = round(max(0.0, min(100.0, p_ind_raw)), 1)

    formula = (
        f"P_ind = ({gca:.1f} × {OMEGA_GCA}) + ({c:.1f} × {OMEGA_CONSCIENTIOUSNESS})"
        f" = {p_ind_raw:.1f} → {score}"
    )

    return PIndResult(
        score=score,
        gca=gca_detail,
        conscientiousness=c_detail,
        experience=exp_detail,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )