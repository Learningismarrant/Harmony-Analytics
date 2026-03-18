# engine/psychometrics/normalizer.py
"""
Normalisation des scores bruts → pourcentage 0-100.

Appelé par les scorers (scoring_likert, scoring_qcm).
Fonctions pures, sans effet de bord.
"""


def to_percentage(points: float, max_possible: float) -> float:
    """Convertit points/max en pourcentage arrondi à 1 décimale (0-100)."""
    if max_possible <= 0:
        return 0.0
    return round((points / max_possible) * 100, 1)
