"""Types partagés entre tous les use cases."""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class UseCase(str, Enum):
    RECRUITMENT = "recruitment"
    MANAGEMENT  = "management"
    TRAINING    = "training"
    TALENT      = "talent"
    RPS         = "rps"


class ConfidenceLevel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"


@dataclass
class UseCaseAlert:
    code: str           # ex: "JERK_RISK", "BURNOUT_RISK", "LMX_CRITICAL"
    severity: str       # "INFO" | "WARNING" | "CRITICAL"
    message: str
    dimension: str      # "pj" | "pt" | "ps" | "ns" | "motivation"


@dataclass
class DataAvailability:
    """Résumé des données disponibles pour ce calcul."""
    has_psychometric: bool
    has_cognitive: bool
    has_motivation: bool
    has_vessel_params: bool
    has_captain_vector: bool
    has_crew_snapshots: bool
    completeness: float   # 0-1


def _build_data_availability(
    candidate_snapshot: Dict,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    crew_snapshots: Optional[List[Dict]] = None,
) -> DataAvailability:
    """Construit le résumé de disponibilité des données depuis un snapshot candidat."""
    has_psychometric = bool(
        candidate_snapshot.get("big_five") or candidate_snapshot.get("emotional_stability")
    )
    has_cognitive = bool(
        (candidate_snapshot.get("cognitive") or {}).get("gca_score")
        or (candidate_snapshot.get("cognitive") or {}).get("logical")
    )
    has_motivation = bool(candidate_snapshot.get("motivation"))
    has_vessel = bool(vessel_params)
    has_captain = bool(captain_vector)
    has_crew = bool(crew_snapshots)

    # Compter les sources disponibles sur 6 dimensions
    available = sum([
        has_psychometric,
        has_cognitive,
        has_motivation,
        has_vessel,
        has_captain,
        has_crew,
    ])
    completeness = round(available / 6.0, 3)

    return DataAvailability(
        has_psychometric=has_psychometric,
        has_cognitive=has_cognitive,
        has_motivation=has_motivation,
        has_vessel_params=has_vessel,
        has_captain_vector=has_captain,
        has_crew_snapshots=has_crew,
        completeness=completeness,
    )


def _confidence_from_quality(data_quality: float) -> ConfidenceLevel:
    """Convertit une data_quality [0-1] en ConfidenceLevel."""
    if data_quality >= 0.75:
        return ConfidenceLevel.HIGH
    if data_quality >= 0.45:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
