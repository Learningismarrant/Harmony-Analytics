# app/engine/benchmarking/gap.py
"""
Gap analysis engine — candidat vs profil SME idéal.

Compare le psychometric_snapshot d'un candidat au profil SME pour son poste
cible et retourne une liste de GapTrait avec conseil associé.

Règles d'architecture :
    - Zéro accès DB — calcul pur.
    - Inputs : snapshot dict + position str.
    - Output : List[GapTrait] + helper get_gap_summary().

Références scientifiques :
    - Barrick & Mount (1991) — Big Five et performance
    - Deci & Ryan (2000) — Self-Determination Theory
    - Cattell-Horn-Carroll — Raisonnement fluide (Gf)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.content.sme_profiles import SME_PROFILES, TRAIT_POLARITY
from app.content.advice.advice_candidate import CANDIDATE_GAP_ADVICE


# ── Mapping catégories snapshot → catégories SME ─────────────────────────────

SNAPSHOT_TO_SME_CAT: Dict[str, str] = {
    "big_five":  "personality",
    "cognitive":  "cognitive",
    "motivation": "motivation",
}

# Traits à exclure du gap (absents des profils SME ou dérivés d'un autre trait)
_EXCLUDED_TRAITS = frozenset({
    "emotional_stability",   # SME utilise "neuroticism" ; dérivé = 100 - neuroticism
    "gca_score",             # score global cognitif, pas dans SME
    "fluid_reasoning",       # HMR — pas dans SME
    "hfr_induction",         # HMR — pas dans SME
    "hfr_analogy",           # HMR — pas dans SME
    "hfr_matrix_reasoning",  # HMR — pas dans SME
    "leadership_preferences",# catégorie entière absente du SME
    "resilience",            # pas dans SME
})


# ── Dataclass de sortie ───────────────────────────────────────────────────────

@dataclass
class GapTrait:
    trait:           str
    candidate_score: float
    sme_target:      float
    gap_pts:         float   # candidate_score - sme_target (positif = au-dessus)
    gap_band:        str     # "strength" | "developing" | "gap" | "too_high"
    advice:          str


# ── Logique de banding ────────────────────────────────────────────────────────

def _gap_band(trait: str, gap_pts: float) -> str:
    """
    Calcule la bande de gap selon la polarité du trait.

    Polarité "high" (cible = score élevé souhaité) :
        gap_pts >= -10       → strength
        -25 <= gap_pts < -10 → developing
        gap_pts < -25        → gap
        gap_pts > +15        → too_high

    Polarité "low" (cible = score bas souhaité) :
        gap_pts <= 10        → strength    (candidat proche ou sous la cible = bon)
        10 < gap_pts <= 25   → developing
        gap_pts > 25         → gap
        gap_pts < -15        → too_high    (trop bas — ex : amotivation = 0)

    Polarité "moderate" (cible = score modéré souhaité) :
        abs(gap_pts) <= 10   → strength
        10 < abs(gap) <= 25  → developing
        abs(gap_pts) > 25    → gap
        (pas de "too_high" pour moderate)
    """
    polarity = TRAIT_POLARITY.get(trait, "high")

    if polarity == "high":
        if gap_pts > 15:
            return "too_high"
        if gap_pts >= -10:
            return "strength"
        if gap_pts >= -25:
            return "developing"
        return "gap"

    if polarity == "low":
        if gap_pts < -15:
            return "too_high"
        if gap_pts <= 10:
            return "strength"
        if gap_pts <= 25:
            return "developing"
        return "gap"

    # moderate
    abs_gap = abs(gap_pts)
    if abs_gap <= 10:
        return "strength"
    if abs_gap <= 25:
        return "developing"
    return "gap"


def _get_advice(trait: str, band: str) -> str:
    """
    Récupère le conseil depuis CANDIDATE_GAP_ADVICE.
    Fallback sur "default" si le trait est absent.
    """
    trait_advice = CANDIDATE_GAP_ADVICE.get(trait)
    if trait_advice and band in trait_advice:
        return trait_advice[band]
    # fallback générique
    return CANDIDATE_GAP_ADVICE["default"].get(band, "")


# ── Fonction principale ───────────────────────────────────────────────────────

def compute_gap_profile(
    snapshot: Dict[str, Any],
    position: str,
) -> List[GapTrait]:
    """
    Compare le snapshot du candidat au profil SME pour son poste cible.

    Retourne une liste de GapTrait pour tous les traits couverts à la fois
    dans le snapshot et dans le profil SME.
    Retourne [] si position inconnue ou snapshot vide.
    Zéro accès DB.
    """
    if not snapshot or position not in SME_PROFILES:
        return []

    sme_profile = SME_PROFILES[position]
    results: List[GapTrait] = []

    for snap_cat, sme_cat in SNAPSHOT_TO_SME_CAT.items():
        snap_section: Dict[str, Any] = snapshot.get(snap_cat, {})
        sme_section: Dict[str, float] = sme_profile.get(sme_cat, {})

        if not snap_section or not sme_section:
            continue

        for trait, raw_value in snap_section.items():
            # Exclure les traits non couverts par le SME
            if trait in _EXCLUDED_TRAITS:
                continue
            if trait not in sme_section:
                continue

            # Normaliser la valeur candidate (supporte float direct ou dict {"score": x})
            candidate_score: Optional[float] = None
            if isinstance(raw_value, dict):
                candidate_score = raw_value.get("score")
            elif isinstance(raw_value, (int, float)):
                candidate_score = float(raw_value)

            if candidate_score is None:
                continue

            sme_target = float(sme_section[trait])
            gap_pts = round(candidate_score - sme_target, 2)
            band = _gap_band(trait, gap_pts)
            advice = _get_advice(trait, band)

            results.append(GapTrait(
                trait=trait,
                candidate_score=candidate_score,
                sme_target=sme_target,
                gap_pts=gap_pts,
                gap_band=band,
                advice=advice,
            ))

    return results


# ── Résumé agrégé ─────────────────────────────────────────────────────────────

def get_gap_summary(gap_traits: List[GapTrait]) -> Dict[str, Any]:
    """
    Résumé agrégé du gap profile.

    Retourne :
        total_traits  : nombre total de traits analysés
        strengths     : traits en "strength"
        developing    : traits en "developing"
        gaps          : traits en "gap"
        too_high      : traits en "too_high"
        completeness  : ratio traits couverts / traits SME total (0.0 - 1.0)
    """
    if not gap_traits:
        return {
            "total_traits": 0,
            "strengths":    0,
            "developing":   0,
            "gaps":         0,
            "too_high":     0,
            "completeness": 0.0,
        }

    counts: Dict[str, int] = {"strength": 0, "developing": 0, "gap": 0, "too_high": 0}
    for gt in gap_traits:
        counts[gt.gap_band] = counts.get(gt.gap_band, 0) + 1

    # Nombre total de traits définis dans tous les profils SME (union)
    all_sme_traits: set[str] = set()
    for profile in SME_PROFILES.values():
        for section in profile.values():
            all_sme_traits.update(section.keys())
    # Exclure les traits systématiquement ignorés
    all_sme_traits -= _EXCLUDED_TRAITS

    total_sme = len(all_sme_traits) if all_sme_traits else 1
    completeness = round(len(gap_traits) / total_sme, 3)

    return {
        "total_traits": len(gap_traits),
        "strengths":    counts["strength"],
        "developing":   counts["developing"],
        "gaps":         counts["gap"],
        "too_high":     counts["too_high"],
        "completeness": min(completeness, 1.0),
    }
