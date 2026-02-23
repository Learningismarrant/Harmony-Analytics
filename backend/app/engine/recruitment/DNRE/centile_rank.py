# engine/recruitment/dnre/centile_rank.py
"""
Étape 2 du DNRE : Rang Centile Dynamique (Π_pool)

Formule :
    Π_{i,c} = ((cf_i + 0.5 · f_i) / N) × 100

    cf_i  = cumulative frequency = nombre de candidats avec S_{j,c} < S_{i,c}
    f_i   = frequency = nombre de candidats avec S_{j,c} = S_{i,c}
            (incluant le candidat lui-même — banded equality)
    N     = taille totale du pool (tous les candidats scorés)
    100   = normalisation vers 0-100

    La formule de percentile de Tukey (demi-point f_i/2) évite les biais
    de rang ex-aequo : le candidat médian d'un groupe à score égal
    reçoit le centile correspondant à sa position centrale.

Pourquoi le centile est crucial dans le DNRE :
    Le score SME S_{i,c} est absolu — il dit si un candidat est bon.
    Le centile Π_{i,c} est relatif — il dit si un candidat est meilleur
    que les autres dans CE pool, pour CETTE campagne.

    Exemple : S_{i,c} = 72 est excellent si le pool est faible (centile 90),
              mais banal si le pool est fort (centile 45).

    Sans le centile, l'employeur ne peut pas hiérarchiser. Avec le centile,
    il voit immédiatement le classement relatif, compétence par compétence.

Dynamisme du pool :
    Contrairement aux normes statiques (percentile population générale),
    le pool est dynamique : il correspond aux candidats ayant postulé
    à CETTE campagne. Le centile est recalculé à chaque nouveau candidat.
    C'est le "D" de DNRE (Dynamique).

Gestion des pools petits :
    - N < 3 : centile peu fiable → flag LOW_POOL_SIZE, valeur retournée
              mais confidence = LOW
    - N = 1 : le candidat est seul → centile 50.0 (rang médian par défaut)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import bisect


# ── Seuils de fiabilité ───────────────────────────────────────────────────────

MIN_POOL_SIZE_RELIABLE = 5    # En-dessous : centile peu fiable
MIN_POOL_SIZE_VALID    = 2    # En-dessous de 2 : centile non calculable

# Résolution pour le binning ex-aequo (arrondi à 1 décimale)
SCORE_ROUNDING = 1


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class PoolStats:
    """Statistiques du pool pour une compétence donnée."""
    n:      int             # Taille du pool
    mean:   float           # Moyenne S_{pool,c}
    median: float           # Médiane S_{pool,c}
    std:    float           # Écart-type S_{pool,c}
    min:    float
    max:    float
    distribution: List[float] = field(default_factory=list)  # Scores triés


@dataclass
class CentileResult:
    """
    Résultat du rang centile pour un candidat sur une compétence.

    centile        → Π_{i,c} ∈ [0, 100]
    score          → S_{i,c} du candidat (input)
    pool_stats     → statistiques du pool
    rank           → rang absolu (1 = meilleur)
    cf_i           → cumulative frequency
    f_i            → frequency (ex-aequo)
    confidence     → "HIGH" | "MEDIUM" | "LOW" selon taille pool
    percentile_label → "Top 10%" | "Top 25%" etc.
    """
    centile:         float
    score:           float
    pool_stats:      PoolStats
    rank:            int = 0
    cf_i:            int = 0
    f_i:             int = 1
    confidence:      str = "HIGH"
    percentile_label: str = ""
    flags:           List[str] = field(default_factory=list)


# ── Statistiques du pool ──────────────────────────────────────────────────────

def compute_pool_stats(pool_scores: List[float]) -> PoolStats:
    """Calcule les statistiques descriptives du pool."""
    if not pool_scores:
        return PoolStats(n=0, mean=50.0, median=50.0, std=0.0, min=0.0, max=100.0)

    sorted_scores = sorted(pool_scores)
    n = len(sorted_scores)
    mean = sum(sorted_scores) / n

    mid = n // 2
    median = (sorted_scores[mid] + sorted_scores[mid - 1]) / 2 if n % 2 == 0 else sorted_scores[mid]

    variance = sum((s - mean) ** 2 for s in sorted_scores) / n
    std = variance ** 0.5

    return PoolStats(
        n=n,
        mean=round(mean, 1),
        median=round(median, 1),
        std=round(std, 1),
        min=sorted_scores[0],
        max=sorted_scores[-1],
        distribution=sorted_scores,
    )


# ── Calcul du centile (formule de Tukey) ──────────────────────────────────────

def _percentile_label(centile: float) -> str:
    """Étiquette lisible du centile pour le rapport client."""
    if centile >= 90:  return "Top 10%"
    if centile >= 75:  return "Top 25%"
    if centile >= 60:  return "Dessus de la médiane"
    if centile >= 40:  return "Autour de la médiane"
    if centile >= 25:  return "Sous la médiane"
    return "Bas du pool"


def compute(
    candidate_score: float,
    pool_scores: List[float],
    competency_key: str = "",
) -> CentileResult:
    """
    Calcule le rang centile dynamique Π_{i,c}.

    Args:
        candidate_score : S_{i,c} du candidat (0-100)
        pool_scores     : liste des S_{j,c} de TOUS les candidats du pool
                          (incluant le candidat lui-même)
        competency_key  : pour le logging

    Returns:
        CentileResult avec Π_{i,c} et statistiques du pool.

    Gestion edge cases :
        - Pool vide ou singleton → centile 50.0 (neutre)
        - Candidat non présent dans le pool → ajout automatique
        - Scores identiques → banding via f_i/2
    """
    flags: List[str] = []

    # ── Edge cases ──────────────────────────────────────────
    if not pool_scores:
        stats = compute_pool_stats([candidate_score])
        return CentileResult(
            centile=50.0,
            score=candidate_score,
            pool_stats=stats,
            rank=1,
            cf_i=0,
            f_i=1,
            confidence="LOW",
            percentile_label="Pool vide",
            flags=[f"EMPTY_POOL [{competency_key}]: centile non calculable, 50.0 par défaut"],
        )

    # S'assurer que le candidat est inclus dans le pool
    full_pool = list(pool_scores)
    if candidate_score not in full_pool:
        full_pool.append(candidate_score)

    n = len(full_pool)

    if n == 1:
        stats = compute_pool_stats(full_pool)
        return CentileResult(
            centile=50.0,
            score=candidate_score,
            pool_stats=stats,
            rank=1,
            cf_i=0,
            f_i=1,
            confidence="LOW",
            percentile_label=_percentile_label(50.0),
            flags=[f"SINGLETON_POOL [{competency_key}]: 1 candidat, centile 50.0"],
        )

    # ── Formule de Tukey ──────────────────────────────────────
    # cf_i = nombre de candidats STRICTEMENT inférieurs
    rounded_pool = [round(s, SCORE_ROUNDING) for s in full_pool]
    rounded_candidate = round(candidate_score, SCORE_ROUNDING)

    sorted_pool = sorted(rounded_pool)

    # bisect_left : position du premier élément >= candidate_score
    cf_i = bisect.bisect_left(sorted_pool, rounded_candidate)

    # f_i : nombre d'ex-aequo (dont le candidat)
    f_i = sorted_pool.count(rounded_candidate)
    f_i = max(f_i, 1)  # Au moins 1 (le candidat lui-même)

    # Π_{i,c} = (cf_i + 0.5 · f_i) / N × 100
    centile_raw = ((cf_i + 0.5 * f_i) / n) * 100.0
    centile = round(max(0.0, min(100.0, centile_raw)), 1)

    # Rang absolu (1 = meilleur)
    rank = n - cf_i - f_i + 1

    # ── Fiabilité selon taille du pool ───────────────────────
    if n < MIN_POOL_SIZE_VALID:
        confidence = "LOW"
        flags.append(f"LOW_POOL [{competency_key}]: N={n} < {MIN_POOL_SIZE_VALID}")
    elif n < MIN_POOL_SIZE_RELIABLE:
        confidence = "MEDIUM"
        flags.append(f"SMALL_POOL [{competency_key}]: N={n} < {MIN_POOL_SIZE_RELIABLE}, centile approximatif")
    else:
        confidence = "HIGH"

    stats = compute_pool_stats(full_pool)

    return CentileResult(
        centile=centile,
        score=candidate_score,
        pool_stats=stats,
        rank=rank,
        cf_i=cf_i,
        f_i=f_i,
        confidence=confidence,
        percentile_label=_percentile_label(centile),
        flags=flags,
    )


def compute_batch(
    candidates_scores: Dict[str, float],   # {crew_profile_id: S_{i,c}}
    competency_key: str = "",
) -> Dict[str, CentileResult]:
    """
    Calcule les centiles pour TOUS les candidats d'un pool en une passe.
    Efficace car le pool est identique pour tous — calcul O(n log n).

    Args:
        candidates_scores : {crew_profile_id: S_{i,c}}
        competency_key    : pour le logging

    Returns:
        {crew_profile_id: CentileResult}

    Usage dans dnre/master.py :
        for competency in ALL_COMPETENCIES:
            pool = {cid: scores[cid][competency] for cid in candidates}
            centiles[competency] = centile_rank.compute_batch(pool, competency)
    """
    if not candidates_scores:
        return {}

    pool_scores = list(candidates_scores.values())

    return {
        crew_id: compute(score, pool_scores, competency_key)
        for crew_id, score in candidates_scores.items()
    }