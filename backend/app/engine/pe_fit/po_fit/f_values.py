# pe_fit/po_fit/f_values.py
"""
F_values — PO Fit par congruence de valeurs (Famille 3)

Mesure l'adéquation entre les valeurs professionnelles du candidat
et les valeurs organisationnelles de l'armateur / yacht.

Architecture de mesure (document de référence §3.1, §3 PSI) :
    Série P (candidat)   : snapshot['values_profile'][dim]      ∈ [0, 100]
    Série E (organisation) : vessel_params['org_values'][dim]   ∈ [0, 1]
    Score_dim(i)         : 1 − |P_norm(i) − E(i)|

    P_norm(i) = P(i) / 100

4 dimensions CES (Ravlin & Meglino, 1987) :
    honesty      — honnêteté et transparence
    achievement  — accomplissement par le travail bien fait
    fairness     — équité dans le traitement des collaborateurs
    solidarity   — entraide et solidarité

Score global = Σ(w_i × Score_dim_i) / Σw_i  (équipondéré, w=0.25 chacun)

Retourne None si snapshot['values_profile'] OU vessel_params['org_values'] est absent.

Sources :
    Document de référence Harmony Analytics v0.7, §3.1 (Famille 3 — PO fit)
    Chuang, Shen & Judge (2016) — PPEFS, formule PSI dimensionnelle.
    Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception.
        Journal of Applied Psychology, 72, 666–673.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.po_fit.values_weights import (
    W_HONESTY,
    W_ACHIEVEMENT,
    W_FAIRNESS,
    W_SOLIDARITY,
    LOW_VALUES_ALIGNMENT_THRESHOLD,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class POValuesDimScore:
    """Score PSI pour une dimension de valeurs (CES)."""
    dimension:         str
    candidate_raw:     Optional[float]   # valeur brute snapshot (0-100), None si absente
    environment_level: Optional[float]   # valeur E organisation (0-1), None si absente
    score:             float             # PSI ∈ [0, 1]
    weight:            float
    flags:             List[str] = field(default_factory=list)


@dataclass
class POValuesResult:
    """
    Résultat du PO fit par congruence de valeurs (Famille 3).

    score        : score global ∈ [0, 100]
    dimensions   : détail par dimension (honesty, achievement, fairness, solidarity)
    data_quality : qualité des données (1.0 si complètes, dégradée si partielles)
    flags        : avertissements (désalignement fort, données manquantes)
    """
    score:        float
    dimensions:   List[POValuesDimScore]
    data_quality: float = 1.0
    flags:        List[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _psi_dim(
    p_raw: Optional[float],
    e_level: Optional[float],
    *,
    default_score: float = 0.5,
) -> float:
    """
    PSI = 1 − |P_norm − E|  où P_norm = p_raw / 100.
    Retourne default_score si l'une des valeurs est absente.
    """
    if p_raw is None or e_level is None:
        return default_score
    p_norm = p_raw / 100.0
    return round(max(0.0, min(1.0, 1.0 - abs(p_norm - e_level))), 4)


# ── Extraction ────────────────────────────────────────────────────────────────

def _extract_values_profile(snapshot: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait le profil de valeurs du candidat.

    Clés attendues dans snapshot['values_profile'] :
        honesty       ∈ [0, 100]
        achievement   ∈ [0, 100]
        fairness      ∈ [0, 100]
        solidarity    ∈ [0, 100]
    """
    vp = snapshot.get("values_profile") or {}
    return {
        "honesty":     vp.get("honesty"),
        "achievement": vp.get("achievement"),
        "fairness":    vp.get("fairness"),
        "solidarity":  vp.get("solidarity"),
    }


def _extract_org_values(vessel_params: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait les valeurs organisationnelles depuis vessel_params.

    Clés attendues dans vessel_params['org_values'] :
        honesty       ∈ [0, 1]
        achievement   ∈ [0, 1]
        fairness      ∈ [0, 1]
        solidarity    ∈ [0, 1]
    """
    ov = vessel_params.get("org_values") or {}
    return {
        "honesty":     ov.get("honesty"),
        "achievement": ov.get("achievement"),
        "fairness":    ov.get("fairness"),
        "solidarity":  ov.get("solidarity"),
    }


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    vessel_params: Dict,
) -> POValuesResult:
    """
    Calcule le PO fit par congruence de valeurs (Famille 3).

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        vessel_params      : paramètres du poste (doit contenir 'org_values')

    Returns:
        POValuesResult avec score global et détail par dimension.
    """
    flags: List[str] = []
    data_quality = 1.0

    p_vals = _extract_values_profile(candidate_snapshot)
    e_vals = _extract_org_values(vessel_params)

    p_missing = sum(1 for v in p_vals.values() if v is None)
    e_missing = sum(1 for v in e_vals.values() if v is None)

    if p_missing > 0:
        flags.append(
            f"VALUES_PROFILE_PARTIAL: {p_missing}/4 valeurs candidat absentes — médiane utilisée"
        )
        data_quality -= p_missing * 0.10

    if e_missing > 0:
        flags.append(
            f"ORG_VALUES_PARTIAL: {e_missing}/4 valeurs organisation absentes — médiane utilisée"
        )
        data_quality -= e_missing * 0.08

    # Calcul PSI par dimension + alertes désalignement
    dims_config = [
        ("honesty",     "honesty_3.1a",     W_HONESTY),
        ("achievement", "achievement_3.1b",  W_ACHIEVEMENT),
        ("fairness",    "fairness_3.1c",     W_FAIRNESS),
        ("solidarity",  "solidarity_3.1d",   W_SOLIDARITY),
    ]

    dimensions: List[POValuesDimScore] = []
    for key, label, weight in dims_config:
        p_raw   = p_vals[key]
        e_level = e_vals[key]
        score   = _psi_dim(p_raw, e_level)

        dim_flags: List[str] = []
        if score < LOW_VALUES_ALIGNMENT_THRESHOLD:
            dim_flags.append(
                f"VALUES_MISALIGNMENT_{key.upper()}: PSI={score:.2f} — "
                f"désalignement fort (candidat {p_raw}/100 vs org {e_level})"
            )
            flags.extend(dim_flags)

        dimensions.append(POValuesDimScore(
            dimension=label,
            candidate_raw=p_raw,
            environment_level=e_level,
            score=score,
            weight=weight,
            flags=dim_flags,
        ))

    # Score global pondéré
    total_weight = sum(d.weight for d in dimensions)
    raw_score    = sum(d.score * d.weight for d in dimensions) / total_weight
    score        = round(raw_score * 100.0, 1)

    return POValuesResult(
        score=score,
        dimensions=dimensions,
        data_quality=max(0.0, round(data_quality, 3)),
        flags=flags,
    )


def compute_values_fit(
    snapshot: Dict,
    vessel_params: Optional[Dict] = None,
) -> Optional[POValuesResult]:
    """
    Retourne None si vessel_params est None/vide, OU si aucune donnée de valeurs
    n'est présente ni dans snapshot ni dans vessel_params.

    Args:
        snapshot      : psychometric_snapshot du CrewProfile
        vessel_params : paramètres du poste (None → retourne None)

    Returns:
        POValuesResult ou None
    """
    if not vessel_params:
        return None

    has_candidate_values = bool(snapshot.get("values_profile"))
    has_org_values       = bool(vessel_params.get("org_values"))

    if not has_candidate_values and not has_org_values:
        return None

    return compute(snapshot, vessel_params)
