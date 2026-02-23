# engine/recruitment/dnre/sme_score.py
"""
Étape 1 du DNRE : Score d'Adéquation SME (Φ_SME)

Formule :
    S_{i,c} = Σ(w_t · x_{i,t}) / Σ(w_t)

    i   = candidat
    c   = compétence (cluster de traits défini par le SME)
    w_t = poids du trait t défini par le Subject Matter Expert
    x_{i,t} = score du candidat i sur le trait t (0-100)

Différence fondamentale avec le MLPSM :
    Le MLPSM utilisait des betas issus de la littérature (fixes, globaux).
    Le DNRE utilise des poids SME — contextualisés par le poste, le yacht,
    la saison. Un SME (cap expérimenté, DRH maritime) pondère les traits
    selon l'importance réelle sur ce bord précis.

    Ex : pour un Chef de rang sur un superyacht charter 5 étoiles,
    un SME ponderera Agreeableness et Conscientiousness plus fortement
    que pour un ingénieur machine.

Compétences standard (K=4, mappées sur les 4 facteurs MLPSM) :
    C1 : INDIVIDUAL_PERFORMANCE → GCA + Conscientiousness
    C2 : TEAM_FIT              → Agreeableness, ES variance, cohésion
    C3 : ENVIRONMENTAL_FIT     → Resilience, tolérance stress (JD-R proxy)
    C4 : LEADERSHIP_FIT        → Préférences autonomie/feedback/structure

Architecture :
    sme_score.py calcule S_{i,c} pour une compétence donnée.
    Il reçoit les traits extraits du psychometric_snapshot + les poids SME.
    Les poids SME peuvent être statiques (defaults) ou dynamiques
    (configurés par le client/poste via CampaignProfile — Temps 2).

Sources :
    Schmidt, F.L. & Hunter, J.E. (1998). The validity and utility of
    selection methods. Psychological Bulletin, 124(2).
    Sackett, P.R. et al. (2022). Revisiting the validity of measures of
    g and Conscientiousness. Journal of Applied Psychology, 107(10).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Compétences définies ───────────────────────────────────────────────────────

COMPETENCY_INDIVIDUAL_PERFORMANCE = "C1_individual_performance"
COMPETENCY_TEAM_FIT               = "C2_team_fit"
COMPETENCY_ENVIRONMENTAL_FIT      = "C3_environmental_fit"
COMPETENCY_LEADERSHIP_FIT         = "C4_leadership_fit"

ALL_COMPETENCIES = [
    COMPETENCY_INDIVIDUAL_PERFORMANCE,
    COMPETENCY_TEAM_FIT,
    COMPETENCY_ENVIRONMENTAL_FIT,
    COMPETENCY_LEADERSHIP_FIT,
]


# ── Poids SME par défaut (priors — Temps 1) ───────────────────────────────────
# Structure : {competency_key: {trait_key: weight}}
# Poids relatifs (non normalisés — la formule normalise via Σw_t)
# Source : revue littérature + consensus panel SME maritime (Phase 0)

DEFAULT_SME_WEIGHTS: Dict[str, Dict[str, float]] = {
    COMPETENCY_INDIVIDUAL_PERFORMANCE: {
        "gca":               0.60,   # Prédicteur le plus robuste (Schmidt & Hunter)
        "conscientiousness": 0.40,   # Seul trait Big Five universellement prédictif
    },
    COMPETENCY_TEAM_FIT: {
        "agreeableness":         0.40,   # Jerk filter — modèle disjonctif
        "conscientiousness":     0.20,   # Contribution à la cohésion standards
        "emotional_stability":   0.40,   # Buffer collectif (ES = 100 - N)
    },
    COMPETENCY_ENVIRONMENTAL_FIT: {
        "resilience":            0.55,   # Tolérance aux demandes élevées
        "emotional_stability":   0.30,   # Stabilité face à l'isolement
        "openness":              0.15,   # Adaptabilité aux environnements changeants
    },
    COMPETENCY_LEADERSHIP_FIT: {
        "autonomy_preference":   0.40,   # Compatibilité avec le style du capitaine
        "feedback_preference":   0.30,
        "structure_preference":  0.30,
    },
}

# Traits disponibles — fallback 50.0 si absent du snapshot
TRAIT_FALLBACK = 50.0


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class TraitContribution:
    """Contribution d'un trait individuel au score S_{i,c}."""
    trait:         str
    raw_score:     float          # x_{i,t} — score brut 0-100
    weight:        float          # w_t — poids SME
    contribution:  float          # w_t · x_{i,t}
    is_fallback:   bool = False   # True si le score vient d'un fallback médian


@dataclass
class SMEScoreResult:
    """
    Résultat du calcul S_{i,c} pour un candidat sur une compétence.

    score          → S_{i,c} ∈ [0, 100] — score pondéré SME final
    competency_key → identifiant de la compétence
    competency_label → label lisible
    trait_contributions → détail par trait (pour l'explication au client)
    total_weight   → Σw_t (dénominateur de la formule)
    data_quality   → part des traits réels vs fallbacks
    flags          → alertes (traits manquants, poids non normalisés...)
    """
    score:             float
    competency_key:    str
    competency_label:  str = ""
    trait_contributions: List[TraitContribution] = field(default_factory=list)
    total_weight:      float = 0.0
    data_quality:      float = 1.0
    flags:             List[str] = field(default_factory=list)
    formula_snapshot:  str = ""


# ── Étiquettes lisibles ───────────────────────────────────────────────────────

COMPETENCY_LABELS = {
    COMPETENCY_INDIVIDUAL_PERFORMANCE: "Performance Individuelle",
    COMPETENCY_TEAM_FIT:               "Compatibilité Équipe",
    COMPETENCY_ENVIRONMENTAL_FIT:      "Compatibilité Environnement",
    COMPETENCY_LEADERSHIP_FIT:         "Compatibilité Leadership",
}


# ── Extraction des traits depuis le snapshot ──────────────────────────────────

def _extract_trait_score(snapshot: Dict, trait: str) -> tuple[float, bool]:
    """
    Extrait le score d'un trait depuis le psychometric_snapshot.
    Retourne (score, is_fallback).

    Gère les structures :
    - snapshot["big_five"]["agreeableness"]["score"]   (Big Five complet)
    - snapshot["big_five"]["agreeableness"]             (float direct)
    - snapshot["cognitive"]["gca_score"]               (cognitif)
    - snapshot["resilience"]                           (dédié)
    - snapshot["leadership_preferences"]["autonomy_preference"] × 100  (normalisé)
    - snapshot["emotional_stability"]                  (pré-calculé)
    """
    # Traits cognitifs
    if trait == "gca":
        cog = snapshot.get("cognitive") or {}
        val = cog.get("gca_score")
        if val is not None:
            return float(val), False

    # Résilience dédiée
    if trait == "resilience":
        val = snapshot.get("resilience")
        if val is not None:
            return float(val), False
        # Proxy : ES si résilience absente
        es = snapshot.get("emotional_stability")
        if es is not None:
            return float(es), False

    # Stabilité émotionnelle
    if trait == "emotional_stability":
        val = snapshot.get("emotional_stability")
        if val is not None:
            return float(val), False
        bf = snapshot.get("big_five") or {}
        n = bf.get("neuroticism")
        if n is not None:
            n_score = n.get("score", n) if isinstance(n, dict) else n
            return 100.0 - float(n_score), False

    # Préférences leadership (normalisées 0-1 → 0-100)
    if trait in ("autonomy_preference", "feedback_preference", "structure_preference"):
        lp = snapshot.get("leadership_preferences") or {}
        val = lp.get(trait)
        if val is not None:
            return float(val) * 100.0, False
        # Dérivation depuis Big Five si absent
        bf = snapshot.get("big_five") or {}
        if trait == "structure_preference":
            c = bf.get("conscientiousness")
            if c is not None:
                c_score = c.get("score", c) if isinstance(c, dict) else c
                return float(c_score), False
        if trait in ("autonomy_preference", "feedback_preference"):
            o = bf.get("openness")
            if o is not None:
                o_score = o.get("score", o) if isinstance(o, dict) else o
                return float(o_score), False

    # Traits Big Five génériques
    big_five = snapshot.get("big_five") or {}
    val = big_five.get(trait)
    if val is not None:
        if isinstance(val, dict):
            return float(val.get("score", TRAIT_FALLBACK)), False
        return float(val), False

    # Fallback médiane
    return TRAIT_FALLBACK, True


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    competency_key: str,
    sme_weights: Optional[Dict[str, float]] = None,
) -> SMEScoreResult:
    """
    Calcule S_{i,c} pour un candidat sur une compétence donnée.

    Formule : S_{i,c} = Σ(w_t · x_{i,t}) / Σ(w_t)

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        competency_key     : clé de compétence (ex: COMPETENCY_TEAM_FIT)
        sme_weights        : poids SME personnalisés (DEFAULT_SME_WEIGHTS si None)
                             Permet au client de définir ses propres priorités.

    Returns:
        SMEScoreResult avec S_{i,c} et détail par trait.
    """
    flags: List[str] = []

    # Poids SME — defaults si non fournis
    weights_map = sme_weights or DEFAULT_SME_WEIGHTS.get(competency_key, {})
    if not weights_map:
        return SMEScoreResult(
            score=TRAIT_FALLBACK,
            competency_key=competency_key,
            competency_label=COMPETENCY_LABELS.get(competency_key, competency_key),
            flags=[f"NO_WEIGHTS: aucun poids SME défini pour {competency_key}"],
            data_quality=0.0,
        )

    # ── Calcul Σ(w_t · x_{i,t}) ────────────────────────────
    trait_contributions: List[TraitContribution] = []
    weighted_sum   = 0.0
    total_weight   = 0.0
    fallback_count = 0

    for trait, weight in weights_map.items():
        x_it, is_fallback = _extract_trait_score(candidate_snapshot, trait)
        contribution = weight * x_it

        if is_fallback:
            fallback_count += 1
            flags.append(f"FALLBACK_{trait.upper()}: score médian utilisé (50.0)")

        trait_contributions.append(TraitContribution(
            trait=trait,
            raw_score=round(x_it, 1),
            weight=weight,
            contribution=round(contribution, 2),
            is_fallback=is_fallback,
        ))

        weighted_sum += contribution
        total_weight += weight

    # ── Score final ──────────────────────────────────────────
    if total_weight == 0:
        return SMEScoreResult(
            score=TRAIT_FALLBACK,
            competency_key=competency_key,
            competency_label=COMPETENCY_LABELS.get(competency_key, competency_key),
            flags=["ZERO_WEIGHT: somme des poids = 0"],
            data_quality=0.0,
        )

    s_ic = weighted_sum / total_weight
    score = round(max(0.0, min(100.0, s_ic)), 1)

    # Qualité des données : proportion de traits réels vs fallbacks
    n_traits = len(weights_map)
    data_quality = round(1.0 - (fallback_count / n_traits), 3) if n_traits > 0 else 0.0

    # Résumé des contributions pour l'audit
    contrib_str = " + ".join(
        f"{tc.weight}×{tc.raw_score:.0f}" for tc in trait_contributions
    )
    formula = f"S[{competency_key}] = ({contrib_str}) / {total_weight} = {s_ic:.1f} → {score}"

    return SMEScoreResult(
        score=score,
        competency_key=competency_key,
        competency_label=COMPETENCY_LABELS.get(competency_key, competency_key),
        trait_contributions=trait_contributions,
        total_weight=total_weight,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )


def compute_all_competencies(
    candidate_snapshot: Dict,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_keys: Optional[List[str]] = None,
) -> Dict[str, SMEScoreResult]:
    """
    Calcule S_{i,c} pour toutes les compétences d'un candidat.

    Args:
        candidate_snapshot    : psychometric_snapshot
        sme_weights_override  : poids SME personnalisés par compétence
                                {competency_key: {trait: weight}}
        competency_keys       : liste des compétences à calculer
                                (ALL_COMPETENCIES si None)

    Returns:
        Dict {competency_key: SMEScoreResult}

    Usage dans dnre/master.py :
        all_scores = sme_score.compute_all_competencies(snapshot)
        g_fit_input = {k: v.score for k, v in all_scores.items()}
    """
    keys = competency_keys or ALL_COMPETENCIES
    results: Dict[str, SMEScoreResult] = {}

    for key in keys:
        custom_weights = None
        if sme_weights_override:
            custom_weights = sme_weights_override.get(key)
        results[key] = compute(candidate_snapshot, key, sme_weights=custom_weights)

    return results