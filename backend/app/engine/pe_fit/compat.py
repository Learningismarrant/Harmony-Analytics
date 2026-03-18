# engine/recruitment/pe_fit/compat.py
"""
Rétrocompatibilité — aliases vers les dataclasses DNRE/MLPSM d'origine.
Ces types sont exposés pour que pipeline.py et les modules en aval ne cassent pas.
Les anciens modules DNRE/ et MLPSM/ ont été supprimés — tout est dans pe_fit/.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SafetyLevel(str, Enum):
    CLEAR        = "CLEAR"
    ADVISORY     = "ADVISORY"
    HIGH_RISK    = "HIGH_RISK"
    DISQUALIFIED = "DISQUALIFIED"


@dataclass
class DNREResult:
    g_fit:            float
    fit_label:        str

    # Centiles
    centile_ranks:    Dict = field(default_factory=dict)
    overall_centile:  float = 0.0

    # Détails
    sme_scores:       Dict = field(default_factory=dict)
    global_fit_detail: Optional[Any] = None
    safety:           Optional[Any] = None

    # Impact équipe (optionnel)
    f_team_detail:    Optional[Any] = None

    # Meta
    crew_profile_id:  Optional[str] = None
    data_quality:     float = 1.0
    confidence:       str = "HIGH"
    all_flags:        List[str] = field(default_factory=list)


@dataclass
class MLPSMResult:
    # Scores principaux
    y_success:     float
    y_raw_linear:  float
    p_ind_score:   float
    f_team_score:  float
    f_env_score:   float
    f_lmx_score:   float

    # Détails complets (duck-compatible avec pe_fit sub-results)
    p_ind_detail:  Any = None
    f_team_detail: Any = None
    f_env_detail:  Any = None
    f_lmx_detail:  Any = None

    # Meta
    betas_used:       Dict[str, float] = field(default_factory=dict)
    data_quality:     float = 1.0
    confidence:       str = "HIGH"
    success_label:    str = "GOOD_FIT"
    all_flags:        List[str] = field(default_factory=list)
    formula_snapshot: str = ""

    def to_event_snapshot(self) -> Dict:
        return {
            "y_success_predicted":   self.y_success,
            "y_raw_linear":          self.y_raw_linear,
            "p_ind_score":           self.p_ind_score,
            "f_team_score":          self.f_team_score,
            "f_env_score":           self.f_env_score,
            "f_lmx_score":           self.f_lmx_score,
            "beta_weights_snapshot": self.betas_used,
            "data_quality":          self.data_quality,
            "confidence":            self.confidence,
            "flags_summary":         self.all_flags[:10],
        }

    def to_impact_report(self) -> Dict:
        delta = self.f_team_detail.delta if self.f_team_detail else None

        return {
            "y_success_predicted": self.y_success,
            "y_raw_linear":        self.y_raw_linear,
            "success_label":       self.success_label,
            "confidence":          self.confidence,
            "data_quality":        round(self.data_quality * 100),

            "scores": {
                "p_ind":  {"value": self.p_ind_score,  "weight": self.betas_used.get("b1_p_ind",  0.25)},
                "f_team": {"value": self.f_team_score, "weight": self.betas_used.get("b2_f_team", 0.35)},
                "f_env":  {"value": self.f_env_score,  "weight": self.betas_used.get("b3_f_env",  0.20)},
                "f_lmx":  {"value": self.f_lmx_score,  "weight": self.betas_used.get("b4_f_lmx",  0.20)},
            },

            "team_impact": {
                "f_team_before":          delta.f_team_before if delta else None,
                "f_team_after":           delta.f_team_after if delta else None,
                "delta":                  delta.delta if delta else None,
                "net_impact":             delta.net_impact if delta else None,
                "jerk_filter_delta":      delta.jerk_filter_delta if delta else None,
                "faultline_risk_delta":   delta.faultline_risk_delta if delta else None,
                "emotional_buffer_delta": delta.emotional_buffer_delta if delta else None,
            },

            "environment": {
                "jdr_ratio":  self.f_env_detail.jdr_ratio.raw_ratio if self.f_env_detail else None,
                "jdr_status": self.f_env_detail.jdr_ratio.equilibrium_status if self.f_env_detail else None,
                "resilience": self.f_env_detail.resilience.resilience_raw if self.f_env_detail else None,
            },

            "leadership": {
                "compatibility_label": (
                    self.f_lmx_detail.distance.compatibility_label if self.f_lmx_detail else None
                ),
                "normalized_distance": (
                    self.f_lmx_detail.distance.normalized_distance if self.f_lmx_detail else None
                ),
                "dimension_gaps": [
                    {
                        "dimension": d.dimension,
                        "gap":       d.gap,
                        "direction": d.gap_direction,
                        "label":     d.gap_label,
                    }
                    for d in (self.f_lmx_detail.dimensions if self.f_lmx_detail else [])
                ],
            },

            "flags":   self.all_flags,
            "formula": self.formula_snapshot,
        }


DEFAULT_BETAS: Dict[str, float] = {
    "b1_p_ind":  0.25,
    "b2_f_team": 0.35,
    "b3_f_env":  0.20,
    "b4_f_lmx":  0.20,
}

__all__ = [
    "DNREResult",
    "MLPSMResult",
    "SafetyLevel",
    "DEFAULT_BETAS",
]
