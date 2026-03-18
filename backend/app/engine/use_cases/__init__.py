"""
P-E Fit Use Cases — couche d'orchestration métier au-dessus du moteur P-E Fit.

Chaque use case orchestre les dimensions P-E Fit selon un contexte métier précis :
    recruitment  → HIRE / CONDITIONAL / DISQUALIFY
    management   → TEAM_HEALTH + alertes équipe existante
    training     → GAP_ANALYSIS + plan développement individuel
    talent       → READINESS_SCORE par échelon de carrière
    rps          → RISK_LEVEL + facteurs psychosociaux

Règles d'architecture :
    - Zéro appel DB — ces modules ne reçoivent que des dicts/snapshots
    - Zéro import depuis modules/router/service
    - Appels uniquement vers engine/pe_fit/* sous-modules
"""
from app.engine.use_cases._base import (
    UseCase,
    ConfidenceLevel,
    UseCaseAlert,
    DataAvailability,
)

__all__ = [
    "UseCase",
    "ConfidenceLevel",
    "UseCaseAlert",
    "DataAvailability",
]
