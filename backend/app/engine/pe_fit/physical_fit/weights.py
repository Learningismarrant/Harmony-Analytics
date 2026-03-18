# pe_fit/physical_fit/weights.py
"""
Pondérations du fit physique-environnemental (Famille 6).

Famille 6 — Fit physique-environnemental (document de référence §2.2)
    6.1  Tolérance espace restreint / promiscuité    ÉLEVÉE  0.25
    6.2  Tolérance à l'isolement géographique        ÉLEVÉE  0.25
    6.3  Rapport au risque physique                  ÉLEVÉE  0.25
    6.4  Tolérance aux rythmes atypiques             ÉLEVÉE  0.20
    6.5  Sensibilité aux conditions météo            MOYENNE 0.05

Sources :
    Document de référence Harmony Analytics v0.7, §2.2 (Famille 6)
"""

# Pondérations intra-famille 6 (somme = 1.0)
W_CONFINED_SPACE: float = 0.25
"""6.1 — Tolérance à l'espace restreint / promiscuité."""

W_ISOLATION: float = 0.25
"""6.2 — Tolérance à l'isolement géographique."""

W_PHYSICAL_RISK: float = 0.25
"""6.3 — Rapport au risque physique (sur-fit ET sous-fit pénalisés)."""

W_SCHEDULE: float = 0.20
"""6.4 — Tolérance aux rythmes atypiques."""

W_WEATHER: float = 0.05
"""6.5 — Sensibilité aux conditions météo."""

# Seuils d'alerte
LOW_TOLERANCE_THRESHOLD: float = 35.0
"""Seuil sous lequel une tolérance candidate est signalée faible (sur 100)."""

RISK_OVERFIT_MARGIN: float = 30.0
"""
Marge au-delà de laquelle le rapport au risque candidat dépasse
le niveau E du poste — signal d'insouciance potentiellement dangereuse.
Sur-fit physique risk = score candidat_norm > E_level + RISK_OVERFIT_MARGIN/100.
"""
