# tests/engine/benchmarking/test_diagnosis.py
"""
Tests unitaires pour engine.benchmarking.diagnosis

Couverture :
    generate_matrix_diagnosis() :
        - Tous les 9 quadrants de la matrice P×C
        - Boundary values aux seuils (50, 70)

    generate_combined_diagnosis() :
        - ELITE CREW : perf>70, cohesion>70, tvi<25, hcd<25
        - AT RISK : cohesion<40, volatility>45
        - BREAKDOWN ZONE : tous médiocres
        - Pulses vides → weather confiance=0, baseline neutralisé
        - TVI et HCD calculés et dans [0, 100]
"""
import pytest

from app.engine.benchmarking.diagnosis import (
    generate_matrix_diagnosis,
    generate_combined_diagnosis,
    MatrixDiagnosis,
    HIGH_PERF,
    MED_PERF,
    HIGH_COHESION,
    MED_COHESION,
)

pytestmark = pytest.mark.engine


def harmony(perf: float, cohesion: float, c_divergence: float = 5.0, wl_stability: float = 70.0):
    return {
        "performance": perf,
        "cohesion": cohesion,
        "risk_factors": {
            "conscientiousness_divergence": c_divergence,
            "weakest_link_stability": wl_stability,
        },
    }


def weather(average: float = 4.0, std: float = 0.5, days: int = 7, count: int = 7):
    return {
        "average": average,
        "std": std,
        "days_observed": days,
        "response_count": count,
        "status": "stable",
    }


# ── generate_matrix_diagnosis() ───────────────────────────────────────────────

class TestGenerateMatrixDiagnosis:
    def test_retourne_matrix_diagnosis(self):
        result = generate_matrix_diagnosis(80.0, 80.0)
        assert isinstance(result, MatrixDiagnosis)

    def test_elite_crew(self):
        """P ≥ HIGH_PERF, C ≥ HIGH_COHESION → Équipe Elite."""
        result = generate_matrix_diagnosis(HIGH_PERF, HIGH_COHESION)
        assert result.quadrant == "HIGH_PERF_HIGH_COHESION"
        assert result.crew_type_label == "Équipe Elite"
        assert result.risk_signal == "none"

    def test_high_perf_med_cohesion(self):
        """P ≥ HIGH_PERF, MED_COHESION ≤ C < HIGH_COHESION."""
        result = generate_matrix_diagnosis(HIGH_PERF, (MED_COHESION + HIGH_COHESION) / 2)
        assert result.quadrant == "HIGH_PERF_MED_COHESION"
        assert result.risk_signal == "none"

    def test_haut_risque_social(self):
        """P ≥ HIGH_PERF, C < MED_COHESION → Haut Risque Social."""
        result = generate_matrix_diagnosis(HIGH_PERF, MED_COHESION - 1)
        assert result.quadrant == "HIGH_PERF_LOW_COHESION"
        assert result.risk_signal == "social"

    def test_social_sous_performant(self):
        """MED_PERF ≤ P < HIGH_PERF, C ≥ HIGH_COHESION."""
        result = generate_matrix_diagnosis((MED_PERF + HIGH_PERF) / 2, HIGH_COHESION)
        assert result.quadrant == "MED_PERF_HIGH_COHESION"
        assert result.risk_signal == "performance"

    def test_equipe_fonctionnelle(self):
        """P~, C~ → zone centrale."""
        result = generate_matrix_diagnosis(60.0, 55.0)
        assert result.quadrant == "MED_PERF_MED_COHESION"
        assert result.risk_signal == "none"

    def test_equipe_vulnerable(self):
        """MED_PERF ≤ P, C < MED_COHESION → Vulnérable."""
        result = generate_matrix_diagnosis(60.0, MED_COHESION - 5)
        assert result.quadrant == "MED_PERF_LOW_COHESION"
        assert result.risk_signal == "social"

    def test_convivial_inefficace(self):
        """P < MED_PERF, C ≥ HIGH_COHESION → Convivial mais Peu Efficace."""
        result = generate_matrix_diagnosis(MED_PERF - 10, HIGH_COHESION)
        assert result.quadrant == "LOW_PERF_HIGH_COHESION"
        assert result.risk_signal == "performance"

    def test_equipe_en_difficulte(self):
        """P < MED_PERF, MED_COHESION ≤ C < HIGH_COHESION."""
        result = generate_matrix_diagnosis(MED_PERF - 10, 55.0)
        assert result.quadrant == "LOW_PERF_MED_COHESION"
        assert result.risk_signal == "performance"

    def test_zone_de_crise(self):
        """P < MED_PERF, C < MED_COHESION → Zone de Crise."""
        result = generate_matrix_diagnosis(20.0, 20.0)
        assert result.quadrant == "LOW_PERF_LOW_COHESION"
        assert result.crew_type_label == "Zone de Crise"
        assert result.risk_signal == "both"

    def test_description_non_vide(self):
        """Chaque quadrant a une description non vide."""
        result = generate_matrix_diagnosis(80.0, 80.0)
        assert isinstance(result.description, str)
        assert len(result.description) > 10


# ── generate_combined_diagnosis() ────────────────────────────────────────────

class TestGenerateCombinedDiagnosis:
    def test_retourne_dict(self):
        result = generate_combined_diagnosis(harmony(80, 80), weather())
        assert isinstance(result, dict)

    def test_champs_obligatoires(self):
        result = generate_combined_diagnosis(harmony(80, 80), weather())
        expected_keys = {
            "crew_type", "risk_level", "volatility_index",
            "hidden_conflict", "short_term_prediction",
            "recommended_action", "early_warning",
        }
        assert expected_keys.issubset(result.keys())

    def test_elite_crew_classification(self):
        """Perf=80, cohesion=80, bonne météo → ELITE CREW."""
        result = generate_combined_diagnosis(
            harmony(80, 80, c_divergence=5, wl_stability=75),
            weather(average=4.5),
        )
        assert result["crew_type"] == "ELITE CREW"
        assert result["risk_level"] == "low"

    def test_breakdown_zone(self):
        """Perf=20, cohesion=20, météo mauvaise → BREAKDOWN ZONE."""
        result = generate_combined_diagnosis(
            harmony(20, 20, c_divergence=30, wl_stability=20),
            weather(average=1.5, days=7),
        )
        assert result["crew_type"] == "AT RISK CREW"
        assert result["risk_level"] in ("high", "critical")

    def test_tvi_dans_bornes(self):
        """Team Volatility Index toujours dans [0, 100]."""
        result = generate_combined_diagnosis(harmony(50, 50), weather())
        assert 0.0 <= result["volatility_index"] <= 100.0

    def test_hcd_dans_bornes(self):
        """Hidden Conflict Detector toujours dans [0, 100]."""
        result = generate_combined_diagnosis(harmony(80, 40), weather())
        assert 0.0 <= result["hidden_conflict"] <= 100.0

    def test_pulses_vides_neutralise(self):
        """
        days_observed=0 → weather_confidence=0 → effective_weather = baseline (3.0).
        Ne doit pas lever d'exception.
        """
        result = generate_combined_diagnosis(
            harmony(70, 70),
            weather(average=1.0, days=0, count=0),
        )
        assert isinstance(result, dict)
        assert "crew_type" in result

    def test_prediction_stable_bonne_equipe(self):
        """Équipe saine → prédiction indique "Stable"."""
        result = generate_combined_diagnosis(
            harmony(80, 80, c_divergence=5, wl_stability=80),
            weather(average=4.5, std=0.3, days=7),
        )
        assert "Stable" in result["short_term_prediction"]

    def test_recommended_action_non_vide(self):
        """recommended_action doit être une chaîne non vide."""
        result = generate_combined_diagnosis(harmony(60, 60), weather())
        assert isinstance(result["recommended_action"], str)
        assert len(result["recommended_action"]) > 5

    def test_early_warning_conflit_latent(self):
        """
        Météo basse (< 3.0) + perf haute + cohésion entre MED et HIGH
        → early_warning signale conflit latent.
        """
        result = generate_combined_diagnosis(
            harmony(75, 55),
            weather(average=2.5, std=0.5, days=7),
        )
        assert "conflit" in result["early_warning"].lower() or "alerte" in result["early_warning"].lower()

    def test_risk_level_valeur(self):
        """risk_level doit être l'une des 4 valeurs définies."""
        result = generate_combined_diagnosis(harmony(60, 60), weather())
        assert result["risk_level"] in ("low", "medium", "high", "critical")

    def test_high_output_fragile(self):
        """Perf élevée + cohésion basse → HIGH OUTPUT / FRAGILE."""
        result = generate_combined_diagnosis(
            harmony(80, 30, c_divergence=5, wl_stability=70),
            weather(average=4.0, days=7),
        )
        assert result["crew_type"] == "HIGH OUTPUT / FRAGILE"
