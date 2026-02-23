# engine/recruitment/f_team.py
"""
F_team — Compatibilité d'Équipe (Social Harmony & Teamwork Capacity)

Mesure l'impact d'un nouveau membre sur la dynamique collective.
Contrairement à P_ind qui évalue l'individu, F_team est une propriété
émergente du groupe : elle change à chaque ajout ou départ.

Formule de base (Temps 1) :
    F_team = wₐ·min(A_i) - wc·σ(C_i) + wₑ·μ(ES_i)

    Composantes :
    ┌─────────────────────────────────────────────────────────────────┐
    │ Jerk Filter        : min(Agreeableness)  → modèle DISJONCTIF   │
    │   Un seul membre   peu agréable plombe toute l'équipe.          │
    │   Source : Hackman (2002) — "Règle du maillon faible"          │
    │                                                                 │
    │ Faultline Risk     : σ(Conscientiousness) → PÉNALITÉ variance  │
    │   Hétérogénéité C  = conflits sur le soin du travail.           │
    │   Source : Lau & Murnighan (1998) — Faultline Theory           │
    │                                                                 │
    │ Emotional Buffer   : μ(EmotionalStability) → modèle ADDITIF    │
    │   Plus l'ES est élevée en moyenne, plus l'équipe absorbe        │
    │   les tensions sans exploser.                                   │
    │   Source : Jordan et al. (2002) — Team EI                      │
    └─────────────────────────────────────────────────────────────────┘

Évolution Temps 2 :
    - Pondération des sous-scores par YachtPosition (le capitaine
      a plus d'impact sur l'ES collective que un deckhand)
    - Intégration du TVI (Team Volatility Index) depuis les pulses
    - Diversité compétences (O × role_heterogeneity) comme bonus
    - Modèle réseau : poids des dyades (qui travaille avec qui)

Sources académiques :
    Hackman, J.R. (2002). Leading Teams. Harvard Business School Press.
    Lau, D.C. & Murnighan, J.K. (1998). Faultlines. Academy of Mgmt.
    Jordan, P.J. et al. (2002). Emotional intelligence in teams. 
      Small Group Research, 33(3).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import statistics


# ── Pondérations des sous-composantes ────────────────────────────────────────

W_JERK_FILTER    = 0.40   # Agréabilité minimale — modèle disjonctif
W_FAULTLINE_RISK = 0.30   # Variance conscienciosité — pénalité
W_EMOTIONAL_BUFFER = 0.30  # Stabilité émotionnelle moyenne — additif

# Seuils de risque
JERK_FILTER_DANGER   = 35.0   # Sous ce seuil → flag JERK_RISK
FAULTLINE_DANGER     = 20.0   # Au-delà de cette σ → flag FAULTLINE_RISK
ES_MINIMUM_THRESHOLD = 45.0   # Sous ce μ → flag EMOTIONAL_FRAGILITY

# Taille minimale d'équipe pour F_team significatif
MIN_CREW_SIZE = 2


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class JerkFilterDetail:
    """
    Modèle disjonctif — le maillon le plus faible en agréabilité.
    Un score < 35 signale un risque de marin toxique ou conflictuel.
    """
    min_agreeableness: float        # Score le plus bas de l'équipe
    weakest_member_position: Optional[str] = None  # Poste du maillon faible
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class FaultlineRiskDetail:
    """
    Variance conscienciosité — mesure la divergence sur le soin du travail.
    Une forte hétérogénéité génère des conflits autour des standards.
    Ex : un chef cuistot très consciencieux avec un deckhand négligent.
    """
    sigma_conscientiousness: float  # Écart-type (0 = homogène, >20 = risque)
    mean_conscientiousness: float
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class EmotionalBufferDetail:
    """
    Moyenne stabilité émotionnelle (ES = 100 - Neuroticism).
    Un pool élevé absorbe mieux les tensions liées à l'isolement et la pression.
    """
    mean_emotional_stability: float
    min_emotional_stability: float
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class FTeamDelta:
    """
    Delta avant/après ajout du candidat.
    Calculé en comparant l'équipe sans vs avec le candidat.
    C'est l'input principal du simulateur What-If.
    """
    f_team_before: float
    f_team_after: float
    delta: float                         # Positif = candidat améliore l'équipe
    jerk_filter_delta: float
    faultline_risk_delta: float
    emotional_buffer_delta: float
    net_impact: str = ""                 # "POSITIVE" | "NEUTRAL" | "NEGATIVE"


@dataclass
class FTeamResult:
    """
    Résultat complet du calcul F_team.

    score        → valeur finale 0-100, injectée dans l'équation maîtresse
    jerk_filter  → détail du maillon le plus faible
    faultline    → détail de la variance conscienciosité
    emotional    → détail de la stabilité émotionnelle collective
    crew_size    → taille de l'équipe analysée (candidat inclus si intégré)
    delta        → impact marginal du candidat (si compute_delta() appelé)
    data_quality → 0.0-1.0
    flags        → risques détectés
    """
    score: float

    jerk_filter: JerkFilterDetail
    faultline: FaultlineRiskDetail
    emotional: EmotionalBufferDetail

    crew_size: int = 0
    delta: Optional[FTeamDelta] = None

    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Extraction des inputs depuis les snapshots ────────────────────────────────

def _extract_big_five_score(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait un score Big Five depuis le psychometric_snapshot.

    Gère les deux formats :
    - Nouveau : {"big_five": {"agreeableness": {"score": 72.0, "reliable": true}}}
    - Ancien  : {"big_five": {"agreeableness": 72.0}}
    """
    big_five = snapshot.get("big_five") or {}
    val = big_five.get(trait)
    if val is None:
        return None
    if isinstance(val, dict):
        return float(val.get("score", 0))
    return float(val)


def _extract_emotional_stability(snapshot: Dict) -> Optional[float]:
    """
    Stabilité émotionnelle = 100 - Neuroticism.
    Stockée directement dans le snapshot si pré-calculée par snapshot.py.
    """
    # Priorité : valeur pré-calculée dans le snapshot
    es = snapshot.get("emotional_stability")
    if es is not None:
        return float(es)

    # Fallback : calculer depuis neuroticism
    neuroticism = _extract_big_five_score(snapshot, "neuroticism")
    if neuroticism is not None:
        return 100.0 - neuroticism

    # Fallback : ES directement dans big_five (certains tests la calculent)
    return _extract_big_five_score(snapshot, "emotional_stability")


# ── Calcul du F_team sur une liste de snapshots ───────────────────────────────

def _compute_from_snapshots(snapshots: List[Dict]) -> tuple[FTeamResult, list[str]]:
    """
    Calcul interne du F_team sur une liste de snapshots fournie.
    Retourne (FTeamResult, flags).
    """
    flags: list[str] = []
    data_quality = 1.0

    # ── Extraction des scores ──────────────────────────────────
    agreeableness_scores  = []
    conscientiousness_scores = []
    es_scores             = []

    for snap in snapshots:
        a = _extract_big_five_score(snap, "agreeableness")
        c = _extract_big_five_score(snap, "conscientiousness")
        e = _extract_emotional_stability(snap)

        if a is not None: agreeableness_scores.append(a)
        if c is not None: conscientiousness_scores.append(c)
        if e is not None: es_scores.append(e)

    n = len(snapshots)
    missing = []
    if len(agreeableness_scores) < n:
        missing.append("agreeableness")
        data_quality -= 0.15
    if len(conscientiousness_scores) < n:
        missing.append("conscientiousness")
        data_quality -= 0.15
    if len(es_scores) < n:
        missing.append("emotional_stability")
        data_quality -= 0.10
    if missing:
        flags.append(f"PARTIAL_DATA: {', '.join(missing)} manquant(s) pour certains membres")

    # ── Fallback valeurs médianes ──────────────────────────────
    while len(agreeableness_scores) < n:
        agreeableness_scores.append(50.0)
    while len(conscientiousness_scores) < n:
        conscientiousness_scores.append(50.0)
    while len(es_scores) < n:
        es_scores.append(50.0)

    # ── Jerk Filter (modèle disjonctif) ───────────────────────
    min_a = min(agreeableness_scores)
    jerk_risk = min_a < JERK_FILTER_DANGER
    if jerk_risk:
        flags.append(f"JERK_RISK: agréabilité minimale à {min_a:.1f} (seuil: {JERK_FILTER_DANGER})")

    jerk_detail = JerkFilterDetail(
        min_agreeableness=min_a,
        scores_all=agreeableness_scores,
        risk_detected=jerk_risk,
    )

    # ── Faultline Risk (variance conscienciosité) ──────────────
    sigma_c = statistics.stdev(conscientiousness_scores) if len(conscientiousness_scores) > 1 else 0.0
    mean_c  = statistics.mean(conscientiousness_scores)
    fl_risk = sigma_c > FAULTLINE_DANGER
    if fl_risk:
        flags.append(f"FAULTLINE_RISK: σ(C) = {sigma_c:.1f} > {FAULTLINE_DANGER} (conflits standards)")

    faultline_detail = FaultlineRiskDetail(
        sigma_conscientiousness=sigma_c,
        mean_conscientiousness=mean_c,
        scores_all=conscientiousness_scores,
        risk_detected=fl_risk,
    )

    # ── Emotional Buffer (modèle additif) ─────────────────────
    mean_es = statistics.mean(es_scores)
    min_es  = min(es_scores)
    es_risk = mean_es < ES_MINIMUM_THRESHOLD
    if es_risk:
        flags.append(f"EMOTIONAL_FRAGILITY: μ(ES) = {mean_es:.1f} < {ES_MINIMUM_THRESHOLD}")

    emotional_detail = EmotionalBufferDetail(
        mean_emotional_stability=mean_es,
        min_emotional_stability=min_es,
        scores_all=es_scores,
        risk_detected=es_risk,
    )

    # ── Calcul F_team ─────────────────────────────────────────
    # La variance est une PÉNALITÉ → on la soustrait
    # On normalise sigma (max théorique ~35 pour des scores 0-100)
    sigma_c_norm = min(sigma_c / 35.0, 1.0) * 100.0

    f_team_raw = (
        (min_a      * W_JERK_FILTER)
        - (sigma_c_norm * W_FAULTLINE_RISK)
        + (mean_es   * W_EMOTIONAL_BUFFER)
    )
    score = round(max(0.0, min(100.0, f_team_raw)), 1)

    formula = (
        f"F_team = ({min_a:.1f}×{W_JERK_FILTER})"
        f" - ({sigma_c_norm:.1f}×{W_FAULTLINE_RISK})"
        f" + ({mean_es:.1f}×{W_EMOTIONAL_BUFFER})"
        f" = {f_team_raw:.1f} → {score}"
    )

    result = FTeamResult(
        score=score,
        jerk_filter=jerk_detail,
        faultline=faultline_detail,
        emotional=emotional_detail,
        crew_size=n,
        data_quality=max(0.0, data_quality),
        flags=flags,
        formula_snapshot=formula,
    )

    return result, flags


# ── Point d'entrée public ─────────────────────────────────────────────────────

def compute(
    all_snapshots: List[Dict],
) -> FTeamResult:
    """
    Calcule F_team pour une équipe donnée (candidat inclus dans la liste).

    Args:
        all_snapshots : liste des psychometric_snapshot de TOUS les membres
                        y compris le candidat si on veut le score intégré.
                        Pour le delta, utiliser compute_delta() à la place.

    Returns:
        FTeamResult avec score final et détail des 3 sous-composantes.

    Usage dans master.py :
        # Score avec candidat intégré
        all_snaps = current_crew_snapshots + [candidate_snapshot]
        f_team_result = f_team.compute(all_snaps)
    """
    if len(all_snapshots) < MIN_CREW_SIZE:
        return FTeamResult(
            score=50.0,
            jerk_filter=JerkFilterDetail(min_agreeableness=50.0),
            faultline=FaultlineRiskDetail(sigma_conscientiousness=0.0, mean_conscientiousness=50.0),
            emotional=EmotionalBufferDetail(mean_emotional_stability=50.0, min_emotional_stability=50.0),
            crew_size=len(all_snapshots),
            data_quality=0.5,
            flags=["CREW_TOO_SMALL: moins de 2 membres, F_team non significatif (50.0 par défaut)"],
        )

    result, _ = _compute_from_snapshots(all_snapshots)
    return result


def compute_baseline(
    current_crew_snapshots: List[Dict],
) -> FTeamResult:
    """
    Évalue la santé de l'équipe ACTUELLE sans candidat.

    Point d'entrée sémantique pour deux usages distincts :
        1. crew/service.py → dashboard (état courant de l'équipe)
        2. vessel/service.py → recalcul vessel_snapshot après assignment

    Remplace engine.team.harmony.compute() — même calcul, structure unifiée.
    Les champs FTeamResult mappent directement sur HarmonyMetricsOut :
        score                          → performance
        (min_agreeableness + mean_ES)/2 → cohesion (proxy)
        faultline.sigma_conscientiousness → risk_factors.conscientiousness_divergence
        emotional.min_emotional_stability → risk_factors.weakest_link_stability

    Distinct sémantiquement de compute() (candidat inclus dans la liste)
    et de compute_delta() (impact marginal d'un candidat spécifique).
    """
    return compute(current_crew_snapshots)


def compute_delta(
    current_crew_snapshots: List[Dict],
    candidate_snapshot: Dict,
) -> FTeamResult:
    """
    Calcule l'impact MARGINAL du candidat sur l'équipe existante.

    Compare F_team avant et après l'ajout du candidat.
    Enrichit le FTeamResult avec un objet FTeamDelta.

    Args:
        current_crew_snapshots : snapshots de l'équipe actuelle (sans candidat)
        candidate_snapshot     : snapshot du candidat

    Returns:
        FTeamResult avec .delta renseigné → utilisé par simulator.py

    Usage dans master.py (mode simulation) :
        f_team_result = f_team.compute_delta(current_crew_snaps, candidate_snap)
        delta = f_team_result.delta.delta   # +/- impact
    """
    # Score équipe SANS candidat
    if len(current_crew_snapshots) >= MIN_CREW_SIZE:
        result_before, _ = _compute_from_snapshots(current_crew_snapshots)
        score_before = result_before.score
    else:
        score_before = 50.0   # Équipe trop petite pour un score significatif

    # Score équipe AVEC candidat
    all_snapshots = current_crew_snapshots + [candidate_snapshot]
    result_after, _ = _compute_from_snapshots(all_snapshots)
    score_after = result_after.score

    # Delta par composante
    if len(current_crew_snapshots) >= MIN_CREW_SIZE:
        jf_delta = result_after.jerk_filter.min_agreeableness - result_before.jerk_filter.min_agreeableness
        fl_delta = result_after.faultline.sigma_conscientiousness - result_before.faultline.sigma_conscientiousness
        eb_delta = result_after.emotional.mean_emotional_stability - result_before.emotional.mean_emotional_stability
    else:
        jf_delta = fl_delta = eb_delta = 0.0

    global_delta = score_after - score_before
    if global_delta > 3.0:
        net = "POSITIVE"
    elif global_delta < -3.0:
        net = "NEGATIVE"
    else:
        net = "NEUTRAL"

    result_after.delta = FTeamDelta(
        f_team_before=score_before,
        f_team_after=score_after,
        delta=round(global_delta, 1),
        jerk_filter_delta=round(jf_delta, 1),
        faultline_risk_delta=round(fl_delta, 1),
        emotional_buffer_delta=round(eb_delta, 1),
        net_impact=net,
    )

    if global_delta > 5.0:
        result_after.flags.append(f"TEAM_POSITIVE_IMPACT: +{global_delta:.1f} sur F_team")
    elif global_delta < -5.0:
        result_after.flags.append(f"TEAM_NEGATIVE_IMPACT: {global_delta:.1f} sur F_team")

    return result_after