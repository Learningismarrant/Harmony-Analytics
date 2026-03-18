# tests/engine/recruitment/MLPSM/test_master.py
"""
Tests unitaires pour le moteur MLPSM via pe_fit.master.

Migration MLPSM → PE Fit :
    Les anciens modules MLPSM/master.py ont été supprimés.
    La logique équivalente est dans pe_fit/master.py qui expose :
        - _sigmoid_transform, SIGMOID_CENTER, SIGMOID_SCALE (aliases)
        - PEFitResult avec pj_fit, po_fit, pt_fit, ps_fit, global_score

Correspondances :
    MLPSMResult.y_success     → PEFitResult.global_score
    MLPSMResult.p_ind_score   → PEFitResult.pj_fit.p_ind_score
    MLPSMResult.f_team_score  → PEFitResult.pt_fit.score (None → 50.0)
    MLPSMResult.f_env_score   → PEFitResult.po_fit.score (None → 50.0)
    MLPSMResult.f_lmx_score   → PEFitResult.ps_fit.score (None → 50.0)
    _sigmoid_transform        → pe_fit.master._sigmoid_transform (alias exposé)

SKILL.md V1 — Sortie sigmoïde :
    Ŷ_raw    = β₁P + β₂FT + β₃FE + β₄FL   (score linéaire)
    y_success = sigmoid((Ŷ_raw − SIGMOID_CENTER) / SIGMOID_SCALE) × 100
"""
import math
import pytest

from app.engine.pe_fit.master import (
    compute,
    PEFitResult,
    _sigmoid_transform,
    SIGMOID_CENTER,
    SIGMOID_SCALE,
)
from app.engine.pe_fit.pt_fit.f_team import compute as f_team_compute
from app.engine.pe_fit.po_fit.f_env import compute as f_env_compute
from app.engine.pe_fit.ps_fit.f_lmx import compute as f_lmx_compute

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snap(
    conscientiousness: float = 70.0,
    agreeableness: float = 70.0,
    neuroticism: float = 35.0,
    gca: float = 72.0,
    autonomy: float = 0.6,
    feedback: float = 0.5,
    structure: float = 0.4,
    resilience: float = 65.0,
) -> dict:
    """Snapshot psychométrique minimal valide."""
    return {
        "big_five": {
            "conscientiousness": conscientiousness,
            "agreeableness":     agreeableness,
            "neuroticism":       neuroticism,
            "emotional_stability": round(100 - neuroticism, 1),
            "openness": 60.0,
            "extraversion": 55.0,
        },
        "cognitive": {"gca_score": gca},
        "leadership_preferences": {
            "autonomy_preference":   autonomy,
            "feedback_preference":   feedback,
            "structure_preference":  structure,
        },
        "resilience": resilience,
    }


def _vessel() -> dict:
    return {
        "salary_index":        0.65,
        "rest_days_ratio":     0.60,
        "private_cabin_ratio": 0.50,
        "charter_intensity":   0.55,
        "management_pressure": 0.50,
    }


def _captain() -> dict:
    return {
        "autonomy_given":    0.7,
        "feedback_style":    0.5,
        "structure_imposed": 0.4,
    }


CANDIDATE    = _snap()
CREW_TEAM    = [_snap(agreeableness=75.0), _snap(agreeableness=72.0)]
VESSEL       = _vessel()
CAPTAIN      = _captain()


# ── Tests _sigmoid_transform ──────────────────────────────────────────────────

class TestSigmoidTransform:
    def test_centre_invariant(self):
        """sigmoid(50.0) doit retourner exactement 50.0."""
        assert _sigmoid_transform(SIGMOID_CENTER) == 50.0

    def test_symetrie(self):
        for d in [10, 20, 30]:
            high = _sigmoid_transform(SIGMOID_CENTER + d)
            low  = _sigmoid_transform(SIGMOID_CENTER - d)
            assert abs((high + low) - 100.0) < 0.2, (
                f"Symétrie cassée pour d={d}: high={high}, low={low}"
            )

    def test_valeur_superieure_donne_score_superieur_50(self):
        assert _sigmoid_transform(65.0) > 50.0

    def test_valeur_inferieure_donne_score_inferieur_50(self):
        assert _sigmoid_transform(35.0) < 50.0

    def test_monotone_croissant(self):
        scores = [_sigmoid_transform(x) for x in range(0, 101, 10)]
        for a, b in zip(scores, scores[1:]):
            assert a < b, f"Non monotone: {a} >= {b}"

    def test_borne_superieure(self):
        assert _sigmoid_transform(100.0) < 100.0

    def test_borne_inferieure(self):
        assert _sigmoid_transform(0.0) > 0.0

    def test_amplification_extremes(self):
        assert _sigmoid_transform(80.0) > 80.0
        assert _sigmoid_transform(20.0) < 20.0

    def test_formule_manuelle(self):
        y_raw  = 65.0
        z      = (y_raw - SIGMOID_CENTER) / SIGMOID_SCALE
        manual = round(100.0 / (1.0 + math.exp(-z)), 1)
        assert _sigmoid_transform(y_raw) == manual


# ── Tests PE Fit compute() — correspondance avec MLPSM.compute() ─────────────

class TestPEFitCompute:
    """Équivalent de TestCompute (MLPSM/master) via pe_fit.master.compute()."""

    def test_retourne_pe_fit_result(self):
        result = compute(CANDIDATE)
        assert isinstance(result, PEFitResult)

    def test_global_score_dans_bornes(self):
        """global_score ∈ [0, 100] — équivalent y_success."""
        result = compute(CANDIDATE)
        assert 0.0 <= result.global_score <= 100.0

    def test_pj_fit_score_dans_bornes(self):
        result = compute(CANDIDATE)
        assert 0.0 <= result.pj_fit.score <= 100.0

    def test_p_ind_score_dans_bornes(self):
        result = compute(CANDIDATE)
        assert 0.0 <= result.pj_fit.p_ind_score <= 100.0

    def test_pt_fit_avec_equipe(self):
        result = compute(CANDIDATE, current_crew_snapshots=CREW_TEAM)
        assert result.pt_fit is not None
        assert 0.0 <= result.pt_fit.score <= 100.0

    def test_po_fit_avec_vessel(self):
        result = compute(CANDIDATE, vessel_params=VESSEL)
        assert result.po_fit is not None
        assert 0.0 <= result.po_fit.score <= 100.0

    def test_ps_fit_avec_captain(self):
        result = compute(CANDIDATE, captain_vector=CAPTAIN)
        assert result.ps_fit is not None
        assert 0.0 <= result.ps_fit.score <= 100.0

    def test_global_score_average_all_dimensions(self):
        """global_score = moyenne des dimensions disponibles."""
        result = compute(
            CANDIDATE,
            vessel_params=VESSEL,
            current_crew_snapshots=CREW_TEAM,
            captain_vector=CAPTAIN,
        )
        # Toutes les dimensions disponibles
        scores = [
            result.pj_fit.score,
            result.pt_fit.score,
            result.po_fit.score,
            result.ps_fit.score,
        ]
        expected = round(sum(scores) / len(scores), 1)
        assert abs(result.global_score - expected) < 0.2

    def test_sans_equipe_pt_fit_none(self):
        result = compute(CANDIDATE)
        assert result.pt_fit is None

    def test_sans_vessel_po_fit_none(self):
        result = compute(CANDIDATE)
        assert result.po_fit is None

    def test_sans_captain_ps_fit_none(self):
        result = compute(CANDIDATE)
        assert result.ps_fit is None

    def test_snapshot_vide_pas_exception(self):
        result = compute({})
        assert isinstance(result, PEFitResult)

    def test_data_quality_dans_bornes(self):
        result = compute(CANDIDATE)
        assert 0.0 <= result.data_quality <= 1.0

    def test_confidence_coherent(self):
        result = compute(CANDIDATE)
        if result.data_quality >= 0.85:
            assert result.confidence == "HIGH"
        elif result.data_quality >= 0.60:
            assert result.confidence == "MEDIUM"
        else:
            assert result.confidence == "LOW"

    def test_all_flags_list(self):
        result = compute(CANDIDATE)
        assert isinstance(result.all_flags, list)

    def test_safety_level_string(self):
        result = compute(CANDIDATE)
        assert result.safety_level in ("CLEAR", "ADVISORY", "HIGH_RISK", "DISQUALIFIED")

    def test_to_matching_row(self):
        result = compute(CANDIDATE)
        row = result.to_matching_row()
        assert "pj_fit_score" in row
        assert "global_score" in row
        assert "safety_level" in row
        assert "is_disqualified" in row

    def test_to_impact_report(self):
        result = compute(
            CANDIDATE,
            vessel_params=VESSEL,
            current_crew_snapshots=CREW_TEAM,
            captain_vector=CAPTAIN,
        )
        report = result.to_impact_report()
        assert "global_score" in report
        assert "pj_fit" in report
        assert "po_fit" in report
        assert "pt_fit" in report
        assert "ps_fit" in report


# ── Tests F_team (pe_fit/pt_fit/f_team) ──────────────────────────────────────

class TestFTeam:
    """Tests F_team pe_fit — équivalent compute/compute_with_delta MLPSM."""

    def test_compute_retourne_f_team_result(self):
        all_snaps = CREW_TEAM + [CANDIDATE]
        result = f_team_compute(all_snaps)
        assert hasattr(result, "score")
        assert 0.0 <= result.score <= 100.0

    def test_f_team_delta_renseigne(self):
        from app.engine.pe_fit.pt_fit.f_team import compute_delta
        result = compute_delta(CREW_TEAM, CANDIDATE)
        assert result.delta is not None
        assert hasattr(result.delta, "f_team_before")
        assert hasattr(result.delta, "f_team_after")
        assert hasattr(result.delta, "delta")

    def test_equipe_vide_retourne_valeur_par_defaut(self):
        result = f_team_compute([])
        assert result.score == 50.0

    def test_scores_dans_bornes(self):
        result = f_team_compute(CREW_TEAM + [CANDIDATE])
        assert 0.0 <= result.score <= 100.0


# ── Tests F_env (pe_fit/po_fit/f_env) ────────────────────────────────────────

class TestFEnv:
    """Tests F_env pe_fit — équivalent MLPSM F_env."""

    def test_compute_retourne_f_env_result(self):
        result = f_env_compute(CANDIDATE, VESSEL)
        assert hasattr(result, "score")
        assert 0.0 <= result.score <= 100.0

    def test_sans_vessel_params_score_reduit(self):
        result = f_env_compute(CANDIDATE, {})
        # data_quality réduite car pas de params
        assert result.data_quality < 1.0

    def test_jdr_ratio_present(self):
        result = f_env_compute(CANDIDATE, VESSEL)
        assert hasattr(result, "jdr_ratio")
        assert hasattr(result.jdr_ratio, "raw_ratio")
        assert hasattr(result.jdr_ratio, "equilibrium_status")


# ── Tests F_lmx (pe_fit/ps_fit/f_lmx) ───────────────────────────────────────

class TestFLmx:
    """Tests F_lmx pe_fit — équivalent MLPSM F_lmx."""

    def test_compute_retourne_f_lmx_result(self):
        result = f_lmx_compute(CANDIDATE, CAPTAIN)
        assert hasattr(result, "score")
        assert 0.0 <= result.score <= 100.0

    def test_compatibility_label_present(self):
        result = f_lmx_compute(CANDIDATE, CAPTAIN)
        assert result.distance.compatibility_label in (
            "EXCELLENT", "GOOD", "TENSION", "CRITICAL"
        )

    def test_dimension_gaps(self):
        result = f_lmx_compute(CANDIDATE, CAPTAIN)
        assert len(result.dimensions) == 3
        for d in result.dimensions:
            assert d.dimension in ("autonomy", "feedback", "structure")
            assert 0.0 <= d.gap <= 1.0


# ── Tests batch compute ───────────────────────────────────────────────────────

class TestBatchCompute:
    """Équivalent compute_batch MLPSM — via pe_fit.master.compute() sur N candidats."""

    def test_batch_vide(self):
        results = [compute({}) for _ in []]
        assert results == []

    def test_n_candidats_n_resultats(self):
        candidates = [
            _snap(conscientiousness=70),
            _snap(conscientiousness=55),
            _snap(conscientiousness=80),
        ]
        results = [compute(c) for c in candidates]
        assert len(results) == 3

    def test_ordre_preserve(self):
        cand_haut = _snap(conscientiousness=90, gca=90)
        cand_bas  = _snap(conscientiousness=20, gca=20)
        results = [compute(c) for c in [cand_haut, cand_bas]]
        assert results[0].pj_fit.p_ind_score >= results[1].pj_fit.p_ind_score

    def test_retourne_list_pe_fit_result(self):
        candidates = [CANDIDATE, _snap(conscientiousness=55)]
        results = [compute(c) for c in candidates]
        assert all(isinstance(r, PEFitResult) for r in results)
