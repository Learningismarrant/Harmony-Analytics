from __future__ import annotations
"""
Utilitaire transversal P-E Fit — extraction de traits psychométriques depuis le snapshot.

Ce module fournit deux fonctions publiques partagées par tous les sous-modules P-E Fit :

    extract_with_fallback(snapshot, trait) → float
        Extrait le score d'un trait. Retourne 50.0 si toutes les sources sont absentes.
        Utilisé par les calculs de score pondéré où un fallback médian est acceptable
        (ex: DNRE/sme_score).

    extract_strict(snapshot, trait) → float | None
        Extrait le score d'un trait. Retourne None si le trait est absent.
        Utilisé par les évaluations non-compensatoires où un fallback invaliderait
        le calcul (ex: DNRE/safety_barrier — veto non applicable si trait non mesuré).

Traits gérés :
    - gca                  : cognitive/gca_score, fallback depuis moyenne sous-scores
    - emotional_stability  : direct, ou 100 - big_five/neuroticism/score
    - resilience           : direct, ou proxy depuis emotional_stability (fallback only)
    - Big Five             : agreeableness, conscientiousness, openness, extraversion,
                             neuroticism — format {"score": x} ou float direct
    - Leadership prefs     : autonomy_preference, feedback_preference, structure_preference
                             — leadership_preferences[trait] × 100, avec dérivation
                             depuis Big Five si absent

Aucun import depuis DNRE/ ou MLPSM/ — ce module est une dépendance de bas niveau.
"""
from typing import Dict, Optional

# Fallback médian utilisé par extract_with_fallback
_FALLBACK: float = 50.0

# Traits Big Five reconnus
_BIG_FIVE_TRAITS = frozenset({
    "agreeableness",
    "conscientiousness",
    "openness",
    "extraversion",
    "neuroticism",
})

# Traits de préférences leadership
_LEADERSHIP_PREFS = frozenset({
    "autonomy_preference",
    "feedback_preference",
    "structure_preference",
})


# ── Helpers internes ──────────────────────────────────────────────────────────

def _get_big_five_score(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait un score Big Five depuis snapshot["big_five"][trait].
    Gère les deux formats : {"score": x} (objet) ou float direct.
    Retourne None si absent.
    """
    bf = snapshot.get("big_five") or {}
    val = bf.get(trait)
    if val is None:
        return None
    if isinstance(val, dict):
        score = val.get("score")
        return float(score) if score is not None else None
    return float(val)


def _get_gca(snapshot: Dict) -> Optional[float]:
    """
    Extrait le score GCA depuis snapshot["cognitive"]["gca_score"].
    Si gca_score est absent, tente la moyenne des sous-scores (logical, numerical, verbal).
    Retourne None si aucune source n'est disponible.
    """
    cog = snapshot.get("cognitive") or {}
    val = cog.get("gca_score")
    if val is not None:
        return float(val)

    # Fallback : moyenne des sous-scores cognitifs
    sub_keys = ("logical", "numerical", "verbal")
    sub_scores = [float(cog[k]) for k in sub_keys if cog.get(k) is not None]
    if sub_scores:
        return sum(sub_scores) / len(sub_scores)

    return None


def _get_emotional_stability(snapshot: Dict) -> Optional[float]:
    """
    Extrait l'ES depuis snapshot["emotional_stability"] (pré-calculé),
    ou calcule 100 - neuroticism si ES absent.
    Retourne None si aucune source n'est disponible.
    """
    val = snapshot.get("emotional_stability")
    if val is not None:
        return float(val)

    n_score = _get_big_five_score(snapshot, "neuroticism")
    if n_score is not None:
        return 100.0 - n_score

    return None


def _get_resilience(snapshot: Dict, *, allow_es_proxy: bool) -> Optional[float]:
    """
    Extrait la résilience depuis snapshot["resilience"] (dédié).
    Si absent et allow_es_proxy=True, retourne l'ES comme proxy.
    Si absent et allow_es_proxy=False, retourne None (veto non applicable).
    """
    val = snapshot.get("resilience")
    if val is not None:
        return float(val)

    if allow_es_proxy:
        return _get_emotional_stability(snapshot)

    return None


def _get_leadership_pref(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait une préférence leadership depuis snapshot["leadership_preferences"][trait] × 100.
    Si absent, dérive depuis Big Five :
        structure_preference  ← conscientiousness
        autonomy_preference   ← openness
        feedback_preference   ← openness
    Retourne None si aucune source n'est disponible.
    """
    lp = snapshot.get("leadership_preferences") or {}
    val = lp.get(trait)
    if val is not None:
        return float(val) * 100.0

    # Dérivation depuis Big Five
    if trait == "structure_preference":
        return _get_big_five_score(snapshot, "conscientiousness")
    if trait in ("autonomy_preference", "feedback_preference"):
        return _get_big_five_score(snapshot, "openness")

    return None


# ── Routeur commun ────────────────────────────────────────────────────────────

def _resolve(snapshot: Dict, trait: str, *, allow_es_proxy_for_resilience: bool) -> Optional[float]:
    """
    Résout le score d'un trait depuis le snapshot sans appliquer de fallback.
    Retourne None si toutes les sources sont absentes.
    """
    if trait == "gca":
        return _get_gca(snapshot)

    if trait == "emotional_stability":
        return _get_emotional_stability(snapshot)

    if trait == "resilience":
        return _get_resilience(snapshot, allow_es_proxy=allow_es_proxy_for_resilience)

    if trait in _LEADERSHIP_PREFS:
        return _get_leadership_pref(snapshot, trait)

    if trait in _BIG_FIVE_TRAITS:
        return _get_big_five_score(snapshot, trait)

    # Trait inconnu
    return None


# ── API publique ──────────────────────────────────────────────────────────────

def extract_with_fallback(snapshot: Dict, trait: str) -> float:
    """
    Retourne le score du trait depuis le snapshot.
    Retourne 50.0 (médiane) si toutes les sources sont absentes.

    Usage : calculs de score pondéré où une valeur neutre est préférable à
    l'absence de donnée (ex: DNRE/sme_score — S_{i,c}).

    Particularités :
        - resilience : si absent, utilise emotional_stability comme proxy
          avant de tomber sur le fallback 50.0
        - gca : si gca_score absent, utilise la moyenne des sous-scores cognitifs

    Args:
        snapshot : psychometric_snapshot du CrewProfile (dict)
        trait    : clé du trait (ex: "gca", "agreeableness", "autonomy_preference")

    Returns:
        float ∈ [0, 100] — score résolu, ou 50.0 si absent
    """
    val = _resolve(snapshot, trait, allow_es_proxy_for_resilience=True)
    return val if val is not None else _FALLBACK


def extract_strict(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Retourne le score du trait depuis le snapshot.
    Retourne None si toutes les sources sont absentes — ne retourne JAMAIS 50.0.

    Usage : évaluations non-compensatoires où un trait non mesuré signifie
    que la règle ne s'applique pas (ex: DNRE/safety_barrier — veto non applicable
    si le trait n'a pas été mesuré sur ce candidat).

    Particularités :
        - resilience : si absent, retourne None directement (pas de proxy ES)
          — un veto sur résilience ne s'applique que si la résilience est mesurée
        - gca : si gca_score absent, tente quand même la moyenne des sous-scores

    Args:
        snapshot : psychometric_snapshot du CrewProfile (dict)
        trait    : clé du trait (ex: "gca", "agreeableness", "autonomy_preference")

    Returns:
        float ∈ [0, 100] si le trait est disponible, None sinon
    """
    return _resolve(snapshot, trait, allow_es_proxy_for_resilience=False)
