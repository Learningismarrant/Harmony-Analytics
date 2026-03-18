# pe_fit/mobility_fit/weights.py
"""
Pondérations du fit mobilité-temporel (Famille 7).

Famille 7 — Fit mobilité-temporel (document de référence §2.2)
    7.1  Mobilité requise vs. situation personnelle    ÉLEVÉE  0.35
    7.2  Durée embarquement vs. besoins de rupture     ÉLEVÉE  0.35
    7.3  Tolérance à l'incertitude de programme        MOYENNE 0.20
    7.4  Rapport au contrat non-permanent              FAIBLE  0.10

Sources :
    Document de référence Harmony Analytics v0.7, §2.2 (Famille 7)
"""

# Pondérations intra-famille 7 (somme = 1.0)
W_MOBILITY: float = 0.35
"""7.1 — Mobilité requise vs. situation personnelle."""

W_EMBARKATION: float = 0.35
"""7.2 — Durée embarquement vs. besoins de rupture."""

W_UNCERTAINTY: float = 0.20
"""7.3 — Tolérance à l'incertitude de programme."""

W_CONTRACT: float = 0.10
"""7.4 — Rapport au contrat non-permanent."""

# Seuils
LOW_FLEXIBILITY_THRESHOLD: float = 35.0
"""Seuil sous lequel la flexibilité/tolérance candidate est signalée faible (sur 100)."""

# Conversion durée embarquement (semaines) → niveau normalisé [0, 1]
# Poste court : 1-4 sem → 0.25 | Moyen : 4-12 → 0.50 | Long : 12-26 → 0.75 | Très long : 26+ → 1.0
EMBARKATION_DURATION_BREAKPOINTS: list = [4, 12, 26]
"""
Points de rupture (semaines) pour normaliser la durée d'embarquement E en niveau [0,1].
< 4 sem → 0.25 | 4-12 → 0.50 | 12-26 → 0.75 | ≥ 26 → 1.0
"""
