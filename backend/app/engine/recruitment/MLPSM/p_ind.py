# engine/recruitment/p_ind.py
"""
P_ind — Performance Individuelle (Taskwork Capacity)

Prédit la capacité brute d'un candidat à exécuter les tâches techniques
de son poste, indépendamment de l'équipe ou de l'environnement.

SKILL.md V1 — Formule activée :
    P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA × C / 100)

    GCA = General Cognitive Ability (tests cognitifs), normalisé 0-100
    C   = Conscientiousness (Big Five), normalisé 0-100
    GCA × C / 100 : terme d'interaction, normalisé sur l'échelle 0-100

    ω₁ = 0.55  → Schmidt & Hunter (1998) : GCA est le prédicteur dominant
    ω₂ = 0.35  → C, seul trait Big Five prédicateur universel (Barrick & Mount)
    ω₃ = 0.10  → Terme d'interaction : l'association GCA×C n'est pas additive.
                  Un candidat avec GCA=90 ET C=85 est meilleur que la somme
                  de ses parties (engagement + capacité = synergie).
                  Σ ω = 1.0 : vérifié par construction (ω₁+ω₂+ω₃=1.0 au max)

    Vérification de l'invariant ω₁+ω₂+ω₃=1 à GCA=C=100 :
        0.55×100 + 0.35×100 + 0.10×(100×100/100) = 55+35+10 = 100 ✓

Terme d'interaction — justification (Schmidt & Hunter 1998) :
    La méta-analyse de Schmidt & Hunter montre que GCA et C prédisent
    la performance de manière partiellement synergique :
        - GCA seul : ρ ≈ 0.51 (capacité d'apprentissage)
        - C seul   : ρ ≈ 0.31 (persévérance à appliquer)
        - GCA × C  : combiné, l'effet est supralinéaire car la capacité
                     cognitive n'est mobilisée que si la motivation à
                     l'effort est présente (Conscientiousness).
    Un candidat GCA=90/C=20 (capable mais désengagé) est pénalisé
    par rapport à GCA=70/C=75 (capacité moindre mais régulier).

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


# ── Pondérations internes (SKILL.md V1 — évoluent avec la régression Temps 2) ─

OMEGA_GCA               = 0.55   # Poids capacité cognitive (ajusté pour ω₃)
OMEGA_CONSCIENTIOUSNESS = 0.35   # Poids conscienciosité (ajusté pour ω₃)
OMEGA_INTERACTION       = 0.10   # Poids terme d'interaction GCA×C (SKILL V1)
# Σ omegas = 0.55 + 0.35 + 0.10 = 1.0 (au maximum, GCA=C=100)

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

    score             → valeur finale 0-100, injectée dans l'équation maîtresse
    interaction_term  → valeur du terme ω₃·(GCA×C/100) (pour audit)
    gca               → détail capacité cognitive
    conscientiousness → détail trait Big Five
    experience        → détail bonus expérience (Temps 2)
    data_quality      → 0.0-1.0, reflète la complétude des données d'entrée
    flags             → avertissements (ex: "GCA manquant, fallback utilisé")
    formula_snapshot  → Equation résolue — utile pour debug/audit
    """
    score: float

    interaction_term: float   # ω₃·(GCA×C/100) — contribution du terme croisé

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
    position_key: Optional[str] = None,      # Réservé Temps 2 (pondérations par poste)
    omegas: Optional[Dict[str, float]] = None,  # P3 : injectés depuis JobWeightConfig (None = module defaults)
) -> PIndResult:
    """
    Calcule P_ind pour un candidat.

    Formule V1 (SKILL.md) :
        P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA × C / 100)

    Le terme d'interaction (GCA × C / 100) est normalisé sur 0-100 :
        - GCA=100, C=100 → interaction = 100 (contribution max = ω₃×100)
        - GCA=50,  C=50  → interaction = 25
        - GCA=90,  C=20  → interaction = 18  (pénalise le déséquilibre)

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        experience_years   : années d'expérience (depuis CrewProfile.experience_years)
        position_key       : YachtPosition.value — réservé pour ajustements Temps 2
        omegas             : poids injectés depuis JobWeightConfig (SKILL.md P3).
                             Structure attendue : {"omega_gca": float, "omega_conscientiousness": float,
                             "omega_interaction": float}. None = utiliser les constantes du module.

    Returns:
        PIndResult avec score final, terme d'interaction, et détail complet

    Usage typique dans master.py :
        p_ind_result = p_ind.compute(candidate_snapshot, experience_years=crew.experience_years)
        score = p_ind_result.score
    """
    flags: list[str] = []

    # ── 0. Résolution des omegas (P3 : DB ou module defaults) ─
    # Permet la calibration par régression sans toucher au code (SKILL.md DIRECTIVE V1).
    omega_gca = (omegas or {}).get("omega_gca",              OMEGA_GCA)
    omega_c   = (omegas or {}).get("omega_conscientiousness", OMEGA_CONSCIENTIOUSNESS)
    omega_i   = (omegas or {}).get("omega_interaction",       OMEGA_INTERACTION)

    if omegas is not None:
        flags.append(f"OMEGAS_OVERRIDE: ω₁={omega_gca} ω₂={omega_c} ω₃={omega_i} (JobWeightConfig)")

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

    # ── 3. Calcul P_ind avec terme d'interaction ─────────────
    gca = gca_detail.gca_score
    c   = c_detail.c_score

    # Terme d'interaction normalisé : GCA × C / 100 ∈ [0, 100]
    # Ex : GCA=80, C=70 → 80×70/100 = 56.0
    interaction_raw     = (gca * c) / 100.0
    interaction_contrib = omega_i * interaction_raw

    p_ind_raw = (
        (gca * omega_gca)
        + (c * omega_c)
        + interaction_contrib
    )

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
        f"P_ind = ({gca:.1f} × {omega_gca})"
        f" + ({c:.1f} × {omega_c})"
        f" + ({gca:.1f} × {c:.1f} / 100 × {omega_i})"
        f" = {gca * omega_gca:.1f} + {c * omega_c:.1f}"
        f" + {interaction_contrib:.1f}"
        f" = {p_ind_raw:.1f} → {score}"
    )

    return PIndResult(
        score=score,
        interaction_term=round(interaction_contrib, 2),
        gca=gca_detail,
        conscientiousness=c_detail,
        experience=exp_detail,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )
