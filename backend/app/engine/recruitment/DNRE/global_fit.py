# engine/recruitment/dnre/global_fit.py
"""
Étape 3 du DNRE : Indice de Global Fit (G_fit)

Formule :
    G_fit = (1/K) · Σ_{c=1}^{K} S_{i,c}

    K        = nombre de compétences évaluées
    S_{i,c}  = score SME pondéré pour la compétence c (de sme_score.py)
    G_fit    ∈ [0, 100]

Interprétation :
    G_fit est la moyenne non pondérée des scores SME sur toutes les compétences.
    Contrairement au MLPSM (Σ β_c · F_c avec betas fixes),
    le G_fit ne suppose pas de hiérarchie a priori entre compétences.
    La hiérarchie est gérée en amont par les poids SME dans S_{i,c}.

    Ex : pour un Capitaine, le SME accordera des poids élevés à GCA et C
         dans C1 (Individual Performance), ce qui rendra S_{i,C1} élevé.
         G_fit agrège ensuite C1, C2, C3, C4 à parts égales.

Flexibilité :
    compute() accepte un dict de competency_weights pour pondérer les
    compétences entre elles si nécessaire (Temps 2 — configuré par poste).
    Par défaut : poids uniforme 1/K.

Relation avec le centile :
    G_fit (absolu) + Π_pool (relatif) = vision complète.
    Le master.py expose les deux dans le DNREResult final.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class CompetencyContribution:
    """Contribution d'une compétence au G_fit."""
    competency_key:   str
    competency_label: str
    s_ic:             float   # Score SME S_{i,c}
    weight:           float   # Poids de la compétence dans G_fit (1/K par défaut)
    contribution:     float   # weight × S_{i,c}


@dataclass
class GlobalFitResult:
    """
    Résultat du calcul G_fit.

    g_fit            → score final ∈ [0, 100]
    contributions    → détail par compétence
    k_competencies   → nombre de compétences K
    data_quality     → qualité globale (moyenne des data_quality SME)
    flags            → avertissements (ex: compétences manquantes)
    formula_snapshot → équation résolue pour audit
    """
    g_fit:           float
    contributions:   List[CompetencyContribution] = field(default_factory=list)
    k_competencies:  int = 0
    data_quality:    float = 1.0
    flags:           List[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Labels compétences ────────────────────────────────────────────────────────

COMPETENCY_LABELS = {
    "C1_individual_performance": "Performance Individuelle",
    "C2_team_fit":               "Compatibilité Équipe",
    "C3_environmental_fit":      "Compatibilité Environnement",
    "C4_leadership_fit":         "Compatibilité Leadership",
}


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    sme_scores: Dict[str, float],    # {competency_key: S_{i,c}}
    competency_weights: Optional[Dict[str, float]] = None,
    data_qualities: Optional[Dict[str, float]] = None,  # {competency_key: quality}
) -> GlobalFitResult:
    """
    Calcule G_fit = (1/K) · Σ S_{i,c}.

    Args:
        sme_scores         : {competency_key: S_{i,c}} depuis sme_score.py
        competency_weights : poids par compétence (uniforme 1/K si None)
                             Permet de pondérer C1 > C2 pour un Capitaine, etc.
                             Les poids sont normalisés si leur somme ≠ K.
        data_qualities     : {competency_key: quality} pour la qualité globale

    Returns:
        GlobalFitResult avec G_fit et détail des contributions.
    """
    flags: List[str] = []

    if not sme_scores:
        return GlobalFitResult(
            g_fit=0.0,
            flags=["NO_SME_SCORES: aucun score SME fourni"],
            data_quality=0.0,
        )

    k = len(sme_scores)

    # ── Normalisation des poids ───────────────────────────────
    if competency_weights:
        # Filtrer les poids aux compétences disponibles
        active_weights = {
            c: competency_weights.get(c, 1.0)
            for c in sme_scores.keys()
        }
        total_w = sum(active_weights.values())
        if total_w == 0:
            flags.append("ZERO_WEIGHTS: somme des poids = 0, fallback uniforme")
            active_weights = {c: 1.0 for c in sme_scores.keys()}
            total_w = k
    else:
        # Poids uniforme : 1/K pour chaque compétence
        active_weights = {c: 1.0 for c in sme_scores.keys()}
        total_w = float(k)

    # ── Calcul G_fit ──────────────────────────────────────────
    contributions: List[CompetencyContribution] = []
    weighted_sum = 0.0

    for competency_key, s_ic in sme_scores.items():
        w = active_weights.get(competency_key, 1.0)
        normalized_w = w / total_w  # Normalisation pour que Σw_norm = 1
        contribution = normalized_w * s_ic
        weighted_sum += contribution

        contributions.append(CompetencyContribution(
            competency_key=competency_key,
            competency_label=COMPETENCY_LABELS.get(competency_key, competency_key),
            s_ic=round(s_ic, 1),
            weight=round(normalized_w, 4),
            contribution=round(contribution, 2),
        ))

    g_fit = round(max(0.0, min(100.0, weighted_sum)), 1)

    # ── Qualité des données ───────────────────────────────────
    if data_qualities:
        dq_vals = [data_qualities.get(c, 1.0) for c in sme_scores.keys()]
        data_quality = round(sum(dq_vals) / len(dq_vals), 3) if dq_vals else 1.0
    else:
        data_quality = 1.0

    # ── Formula snapshot ──────────────────────────────────────
    scores_str = " + ".join(
        f"{c.weight:.2f}×{c.s_ic:.1f}" for c in contributions
    )
    formula = f"G_fit = ({scores_str}) = {weighted_sum:.1f} → {g_fit}"

    if competency_weights:
        flags.append("WEIGHTED_G_FIT: poids compétences personnalisés appliqués")

    return GlobalFitResult(
        g_fit=g_fit,
        contributions=contributions,
        k_competencies=k,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )