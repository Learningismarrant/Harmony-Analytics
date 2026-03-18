# pe_fit/vessel_profile.py
"""
YachtStructuralProfile — profil structurel d'un yacht pour le PE Fit.

Encapsule les caractéristiques invariantes d'un type de yacht et génère
le dict vessel_params utilisé par les modules pe_fit (physical_fit, mobility_fit,
po_fit, ns_fit).

Usage :
    profile = YachtStructuralProfile(
        yacht_type=YachtTypeAlpha.SUPERYACHT,
        length_m=45.0,
        crew_size=12,
    )
    params = profile.to_vessel_params(
        salary_index=0.75,
        charter_intensity=0.6,
        org_values={"honesty": 0.9, ...},
    )

Sources :
    Document de référence Harmony Analytics v0.7, §4 (Profils structurels).
    Kristof-Brown 2005 — P-E Fit framework.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.shared.enums import YachtTypeAlpha


# ── Profils structurels par type ──────────────────────────────────────────────

_STRUCTURAL_DEFAULTS: Dict[str, Dict] = {
    YachtTypeAlpha.SAILING_CRUISER.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.85,
            "isolation_level":        0.70,
            "physical_risk_level":    0.55,
            "schedule_irregularity":  0.75,
            "weather_exposure":       0.80,
        },
        "mobility_requirements": {
            "mobility_level":            0.75,
            "embarkation_weeks":         12.0,
            "schedule_unpredictability": 0.70,
            "contract_permanence":       0.25,
        },
        "management_pressure": 0.30,
        "private_cabin_ratio": 0.30,
        "rest_days_ratio":     0.55,
    },
    YachtTypeAlpha.SAILING_RACING.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.90,
            "isolation_level":        0.65,
            "physical_risk_level":    0.75,
            "schedule_irregularity":  0.85,
            "weather_exposure":       0.85,
        },
        "mobility_requirements": {
            "mobility_level":            0.85,
            "embarkation_weeks":         6.0,
            "schedule_unpredictability": 0.85,
            "contract_permanence":       0.15,
        },
        "management_pressure": 0.60,
        "private_cabin_ratio": 0.20,
        "rest_days_ratio":     0.40,
    },
    YachtTypeAlpha.MOTOR_CRUISER.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.65,
            "isolation_level":        0.55,
            "physical_risk_level":    0.35,
            "schedule_irregularity":  0.55,
            "weather_exposure":       0.45,
        },
        "mobility_requirements": {
            "mobility_level":            0.60,
            "embarkation_weeks":         8.0,
            "schedule_unpredictability": 0.50,
            "contract_permanence":       0.35,
        },
        "management_pressure": 0.35,
        "private_cabin_ratio": 0.50,
        "rest_days_ratio":     0.60,
    },
    YachtTypeAlpha.SUPERYACHT.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.45,
            "isolation_level":        0.50,
            "physical_risk_level":    0.30,
            "schedule_irregularity":  0.55,
            "weather_exposure":       0.40,
        },
        "mobility_requirements": {
            "mobility_level":            0.65,
            "embarkation_weeks":         10.0,
            "schedule_unpredictability": 0.55,
            "contract_permanence":       0.50,
        },
        "management_pressure": 0.50,
        "private_cabin_ratio": 0.70,
        "rest_days_ratio":     0.65,
    },
    YachtTypeAlpha.MEGAYACHT.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.30,
            "isolation_level":        0.45,
            "physical_risk_level":    0.25,
            "schedule_irregularity":  0.50,
            "weather_exposure":       0.35,
        },
        "mobility_requirements": {
            "mobility_level":            0.60,
            "embarkation_weeks":         12.0,
            "schedule_unpredictability": 0.50,
            "contract_permanence":       0.60,
        },
        "management_pressure": 0.60,
        "private_cabin_ratio": 0.85,
        "rest_days_ratio":     0.70,
    },
    YachtTypeAlpha.EXPEDITION.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.55,
            "isolation_level":        0.90,
            "physical_risk_level":    0.65,
            "schedule_irregularity":  0.80,
            "weather_exposure":       0.90,
        },
        "mobility_requirements": {
            "mobility_level":            0.90,
            "embarkation_weeks":         20.0,
            "schedule_unpredictability": 0.80,
            "contract_permanence":       0.30,
        },
        "management_pressure": 0.40,
        "private_cabin_ratio": 0.55,
        "rest_days_ratio":     0.50,
    },
    YachtTypeAlpha.CHARTER.value: {
        "maritime_conditions": {
            "space_constraint_level": 0.50,
            "isolation_level":        0.40,
            "physical_risk_level":    0.35,
            "schedule_irregularity":  0.80,
            "weather_exposure":       0.50,
        },
        "mobility_requirements": {
            "mobility_level":            0.70,
            "embarkation_weeks":         6.0,
            "schedule_unpredictability": 0.80,
            "contract_permanence":       0.20,
        },
        "management_pressure": 0.65,
        "private_cabin_ratio": 0.55,
        "rest_days_ratio":     0.45,
    },
}


# ── Dataclass principale ──────────────────────────────────────────────────────

@dataclass
class YachtStructuralProfile:
    """
    Profil structurel d'un yacht.

    Attributes:
        yacht_type      : type de yacht (YachtTypeAlpha)
        length_m        : longueur hors-tout en mètres (influence space_constraint)
        crew_size       : taille d'équipage (contextuel)
        charter_intensity : 0-1 (override du défaut structurel si fourni)

    Méthode principale : to_vessel_params() → dict compatible pe_fit.compute()
    """
    yacht_type:        YachtTypeAlpha
    length_m:          float = 0.0
    crew_size:         int = 0
    charter_intensity: Optional[float] = None

    # Surcharges optionnelles par rapport aux défauts structurels
    _overrides: Dict = field(default_factory=dict, repr=False)

    def to_vessel_params(
        self,
        *,
        salary_index:    float = 0.5,
        org_values:      Optional[Dict[str, float]] = None,
        captain_vector:  Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Génère le dict vessel_params pour pe_fit.compute().

        Args:
            salary_index   : indice salarial normalisé ∈ [0, 1]
            org_values     : valeurs organisationnelles CES ∈ [0, 1] par dimension
            captain_vector : vecteur capitaine pour PS Fit (autonomy_given, etc.)

        Returns:
            dict vessel_params avec toutes les clés reconnues par pe_fit
        """
        defaults = _STRUCTURAL_DEFAULTS.get(self.yacht_type.value, {})

        params: Dict = {
            "salary_index":        salary_index,
            "rest_days_ratio":     defaults.get("rest_days_ratio", 0.5),
            "private_cabin_ratio": defaults.get("private_cabin_ratio", 0.5),
            "charter_intensity":   (
                self.charter_intensity
                if self.charter_intensity is not None
                else defaults.get("charter_intensity", 0.5)
            ),
            "management_pressure": defaults.get("management_pressure", 0.5),
        }

        # Maritime conditions (physical fit)
        if "maritime_conditions" in defaults:
            mc = dict(defaults["maritime_conditions"])
            # Ajustement espace selon longueur : < 25m → +10% contrainte
            if self.length_m > 0 and self.length_m < 25.0:
                mc["space_constraint_level"] = min(
                    1.0, mc["space_constraint_level"] + 0.10
                )
            params["maritime_conditions"] = mc

        # Mobility requirements (mobility fit)
        if "mobility_requirements" in defaults:
            params["mobility_requirements"] = dict(defaults["mobility_requirements"])

        # Valeurs organisationnelles (PO fit CES)
        if org_values:
            params["org_values"] = org_values

        # Captain vector (PS fit)
        if captain_vector:
            params["captain_vector"] = captain_vector

        # Appliquer les surcharges manuelles
        params.update(self._overrides)

        return params

    def override(self, **kwargs) -> "YachtStructuralProfile":
        """
        Retourne un nouveau profil avec les surcharges spécifiées.
        Permet des overrides ponctuels sans modifier le profil d'origine.
        """
        import copy
        new_profile = copy.copy(self)
        new_profile._overrides = {**self._overrides, **kwargs}
        return new_profile
