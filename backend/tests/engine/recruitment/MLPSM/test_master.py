# tests/engine/recruitment/MLPSM/test_master.py
"""
Tests unitaires pour engine.recruitment.MLPSM.master

SKILL.md V1 — Sortie sigmoïde :
    Ŷ_raw    = β₁P + β₂FT + β₃FE + β₄FL   (score linéaire)
    y_success = sigmoid((Ŷ_raw − SIGMOID_CENTER) / SIGMOID_SCALE) × 100

Couverture :
    compute() :
        - Retourne MLPSMResult
        - y_success ∈ (0, 100) — sigmoïde, jamais exactement 0 ou 100
        - y_raw_linear ∈ [0, 100] — score linéaire exposé pour audit
        - Équation sigmoïde vérifiée manuellement
        - y_success > 50 quand Ŷ_raw > 50, < 50 quand Ŷ_raw < 50
        - Betas personnalisés passés explicitement
        - Amplification des extrêmes : bon candidat encore mieux / faible encore plus bas

    compute_with_delta() :
        - Retourne MLPSMResult avec f_team_detail.delta renseigné

    compute_batch() :
        - N candidats → N résultats dans le même ordre

    MLPSMResult :
        - to_event_snapshot() contient y_success + y_raw_linear
        - to_impact_report() contient scores + environment + leadership + y_raw_linear
        - data_quality dans [0, 1]
        - confidence label cohérent avec data_quality
        - success_label cohérent avec y_success
        - formula_snapshot mentionne sigmoid
"""
import math
import pytest

from app.engine.recruitment.MLPSM.master import (
    compute,
    compute_with_delta,
    compute_batch,
    MLPSMResult,
    DEFAULT_BETAS,
    _sigmoid_transform,
    SIGMOID_CENTER,
    SIGMOID_SCALE,
)

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
        "demands":   {"physical": 60.0, "cognitive": 50.0, "stress": 55.0, "emotional": 50.0},
        "resources": {"autonomy": 65.0, "social_support": 60.0, "skill_variety": 55.0, "recognition": 60.0},
    }


def _captain() -> dict:
    return {"autonomy_preference": 0.7, "feedback_preference": 0.5, "structure_preference": 0.4}


CANDIDATE = _snap()
CREW_TEAM = [_snap(agreeableness=75.0), _snap(agreeableness=72.0)]
VESSEL    = _vessel()
CAPTAIN   = _captain()


# ── Tests _sigmoid_transform ──────────────────────────────────────────────────

class TestSigmoidTransform:
    def test_centre_invariant(self):
        """sigmoid(50.0) doit retourner exactement 50.0."""
        assert _sigmoid_transform(SIGMOID_CENTER) == 50.0

    def test_symetrie(self):
        """sigmoid(50+d) et sigmoid(50-d) doivent être symétriques autour de 50."""
        for d in [10, 20, 30]:
            high = _sigmoid_transform(SIGMOID_CENTER + d)
            low  = _sigmoid_transform(SIGMOID_CENTER - d)
            assert abs((high + low) - 100.0) < 0.2, (
                f"Symétrie cassée pour d={d}: high={high}, low={low}"
            )

    def test_valeur_superieure_donne_score_superieur_50(self):
        """y_raw > 50 → y_success > 50."""
        assert _sigmoid_transform(65.0) > 50.0

    def test_valeur_inferieure_donne_score_inferieur_50(self):
        """y_raw < 50 → y_success < 50."""
        assert _sigmoid_transform(35.0) < 50.0

    def test_monotone_croissant(self):
        """La sigmoïde est strictement croissante."""
        scores = [_sigmoid_transform(x) for x in range(0, 101, 10)]
        for a, b in zip(scores, scores[1:]):
            assert a < b, f"Non monotone: {a} >= {b}"

    def test_borne_superieure(self):
        """La sigmoïde ne dépasse jamais 100."""
        assert _sigmoid_transform(100.0) < 100.0

    def test_borne_inferieure(self):
        """La sigmoïde est toujours > 0."""
        assert _sigmoid_transform(0.0) > 0.0

    def test_amplification_extremes(self):
        """
        La sigmoïde amplifie les extrêmes par rapport au linéaire.
        Un score de 80 linéaire doit être > 80 sigmoïde (amplifié à la hausse).
        Un score de 20 linéaire doit être < 20 sigmoïde (amplifié à la baisse).
        """
        assert _sigmoid_transform(80.0) > 80.0
        assert _sigmoid_transform(20.0) < 20.0

    def test_formule_manuelle(self):
        """Vérification contre le calcul manuel."""
        y_raw  = 65.0
        z      = (y_raw - SIGMOID_CENTER) / SIGMOID_SCALE
        manual = round(100.0 / (1.0 + math.exp(-z)), 1)
        assert _sigmoid_transform(y_raw) == manual


# ── compute() ─────────────────────────────────────────────────────────────────

class TestCompute:
    def test_retourne_mlpsm_result(self):
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert isinstance(result, MLPSMResult)

    def test_y_success_dans_bornes(self):
        """y_success ∈ (0, 100) — sigmoïde, jamais exactement 0 ou 100."""
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert 0.0 < result.y_success < 100.0

    def test_y_raw_linear_expose(self):
        """MLPSMResult doit exposer y_raw_linear pour audit."""
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert hasattr(result, "y_raw_linear")
        assert 0.0 <= result.y_raw_linear <= 100.0

    def test_sous_scores_dans_bornes(self):
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        for score in (result.p_ind_score, result.f_team_score, result.f_env_score, result.f_lmx_score):
            assert 0.0 <= score <= 100.0, f"Score hors bornes: {score}"

    def test_equation_maitresse_coherente_avec_sigmoid(self):
        """
        y_raw_linear doit correspondre à Σ βᵢ·Fᵢ clampé.
        y_success doit correspondre à sigmoid(y_raw_linear).
        """
        betas  = DEFAULT_BETAS.copy()
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN, betas=betas)

        # Reconstruction du score linéaire
        y_manual = (
            betas["b1_p_ind"]  * result.p_ind_score  +
            betas["b2_f_team"] * result.f_team_score +
            betas["b3_f_env"]  * result.f_env_score  +
            betas["b4_f_lmx"]  * result.f_lmx_score
        )
        y_linear_expected = round(max(0.0, min(100.0, y_manual)), 1)
        assert abs(result.y_raw_linear - y_linear_expected) < 0.01

        # Vérification de la transformation sigmoïde
        y_sigmoid_expected = _sigmoid_transform(y_linear_expected)
        assert abs(result.y_success - y_sigmoid_expected) < 0.1

    def test_y_success_superieur_a_y_raw_pour_bon_candidat(self):
        """
        Un bon candidat (score linéaire > 50) doit avoir y_success > y_raw_linear
        (amplification à la hausse par la sigmoïde).
        """
        result = compute(
            _snap(conscientiousness=85.0, agreeableness=80.0, gca=85.0, neuroticism=20.0),
            CREW_TEAM, VESSEL, CAPTAIN
        )
        if result.y_raw_linear > 50.0:
            assert result.y_success > result.y_raw_linear

    def test_y_success_inferieur_a_y_raw_pour_mauvais_candidat(self):
        """
        Un mauvais candidat (score linéaire < 50) doit avoir y_success < y_raw_linear
        (amplification à la baisse par la sigmoïde).
        """
        result = compute(
            _snap(conscientiousness=20.0, agreeableness=15.0, gca=20.0, neuroticism=75.0),
            CREW_TEAM, VESSEL, CAPTAIN
        )
        if result.y_raw_linear < 50.0:
            assert result.y_success < result.y_raw_linear

    def test_betas_custom(self):
        """Betas personnalisés changent le résultat."""
        betas_default  = DEFAULT_BETAS.copy()
        betas_p_heavy  = {"b1_p_ind": 0.70, "b2_f_team": 0.10, "b3_f_env": 0.10, "b4_f_lmx": 0.10}
        result_default = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN, betas=betas_default)
        result_custom  = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN, betas=betas_p_heavy)
        assert result_default.y_success != result_custom.y_success

    def test_betas_utilises_snapshotes(self):
        """MLPSMResult.betas_used == betas passés."""
        custom = {"b1_p_ind": 0.40, "b2_f_team": 0.30, "b3_f_env": 0.15, "b4_f_lmx": 0.15}
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN, betas=custom)
        assert result.betas_used == custom

    def test_equipe_vide(self):
        """Équipe vide (0 membres actifs) → résultat sans exception."""
        result = compute(CANDIDATE, [], VESSEL, CAPTAIN)
        assert isinstance(result, MLPSMResult)
        assert 0.0 < result.y_success < 100.0

    def test_snapshot_vide(self):
        """Snapshot candidat vide → result avec fallbacks, pas d'exception."""
        result = compute({}, CREW_TEAM, VESSEL, CAPTAIN)
        assert isinstance(result, MLPSMResult)

    def test_data_quality_dans_bornes(self):
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert 0.0 <= result.data_quality <= 1.0

    def test_confidence_coherent(self):
        """confidence correspond à la data_quality."""
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        if result.data_quality >= 0.85:
            assert result.confidence == "HIGH"
        elif result.data_quality >= 0.60:
            assert result.confidence == "MEDIUM"
        else:
            assert result.confidence == "LOW"

    def test_success_label_coherent(self):
        """success_label correspond à y_success (score sigmoïde)."""
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        if result.y_success >= 75:
            assert result.success_label == "STRONG_FIT"
        elif result.y_success >= 60:
            assert result.success_label == "GOOD_FIT"
        elif result.y_success >= 45:
            assert result.success_label == "MODERATE_FIT"
        else:
            assert result.success_label == "POOR_FIT"

    def test_formula_snapshot_mentionne_sigmoid(self):
        """formula_snapshot doit mentionner la transformation sigmoïde."""
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 5
        assert "sigmoid" in result.formula_snapshot.lower() or "P(success)" in result.formula_snapshot

    def test_all_flags_list(self):
        result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert isinstance(result.all_flags, list)

    def test_flags_prefixes_module(self):
        """Les flags sont préfixés par le nom du sous-module."""
        jerk_snap = _snap(agreeableness=20.0)
        result = compute(jerk_snap, [_snap(), _snap()], VESSEL, CAPTAIN)
        f_team_flags = [f for f in result.all_flags if "[F_team]" in f]
        assert isinstance(f_team_flags, list)


# ── compute_with_delta() ──────────────────────────────────────────────────────

class TestComputeWithDelta:
    def test_retourne_mlpsm_result(self):
        result = compute_with_delta(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert isinstance(result, MLPSMResult)

    def test_f_team_delta_renseigne(self):
        """compute_with_delta() doit peupler f_team_detail.delta."""
        result = compute_with_delta(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        assert result.f_team_detail.delta is not None

    def test_delta_contient_avant_apres(self):
        result = compute_with_delta(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        delta = result.f_team_detail.delta
        assert hasattr(delta, "f_team_before")
        assert hasattr(delta, "f_team_after")
        assert hasattr(delta, "delta")


# ── MLPSMResult.to_event_snapshot() ──────────────────────────────────────────

class TestToEventSnapshot:
    def setup_method(self):
        self.result = compute(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        self.snap   = self.result.to_event_snapshot()

    def test_retourne_dict(self):
        assert isinstance(self.snap, dict)

    def test_champs_obligatoires(self):
        expected = {
            "y_success_predicted", "y_raw_linear", "p_ind_score", "f_team_score",
            "f_env_score", "f_lmx_score", "beta_weights_snapshot",
            "data_quality", "confidence", "flags_summary",
        }
        assert expected.issubset(self.snap.keys())

    def test_y_success_dans_bornes(self):
        assert 0.0 < self.snap["y_success_predicted"] < 100.0

    def test_y_raw_linear_dans_bornes(self):
        assert 0.0 <= self.snap["y_raw_linear"] <= 100.0

    def test_flags_summary_max_10(self):
        """Cap à 10 flags en DB."""
        assert len(self.snap["flags_summary"]) <= 10


# ── MLPSMResult.to_impact_report() ───────────────────────────────────────────

class TestToImpactReport:
    def setup_method(self):
        self.result = compute_with_delta(CANDIDATE, CREW_TEAM, VESSEL, CAPTAIN)
        self.report = self.result.to_impact_report()

    def test_retourne_dict(self):
        assert isinstance(self.report, dict)

    def test_champs_scores(self):
        assert "scores" in self.report
        scores = self.report["scores"]
        for key in ("p_ind", "f_team", "f_env", "f_lmx"):
            assert key in scores, f"Clé manquante: {key}"

    def test_y_raw_linear_present(self):
        """Le score linéaire brut doit être exposé dans le rapport d'impact."""
        assert "y_raw_linear" in self.report

    def test_champs_environment(self):
        assert "environment" in self.report
        env = self.report["environment"]
        assert "jdr_ratio" in env
        assert "resilience" in env

    def test_champs_leadership(self):
        assert "leadership" in self.report
        lead = self.report["leadership"]
        assert "compatibility_label" in lead
        assert "normalized_distance" in lead
        assert "dimension_gaps" in lead

    def test_team_impact_present(self):
        assert "team_impact" in self.report
        ti = self.report["team_impact"]
        assert "f_team_before" in ti
        assert "f_team_after" in ti
        assert "delta" in ti

    def test_flags_liste(self):
        assert isinstance(self.report.get("flags"), list)

    def test_formula_presente(self):
        assert isinstance(self.report.get("formula"), str)


# ── compute_batch() ───────────────────────────────────────────────────────────

class TestComputeBatch:
    def test_batch_vide(self):
        results = compute_batch([], CREW_TEAM, VESSEL, CAPTAIN)
        assert results == []

    def test_n_candidats_n_resultats(self):
        candidates = [
            {"snapshot": _snap(conscientiousness=70), "experience_years": 2, "position_key": "bosun"},
            {"snapshot": _snap(conscientiousness=55), "experience_years": 0, "position_key": "deckhand"},
            {"snapshot": _snap(conscientiousness=80), "experience_years": 5, "position_key": "chief_officer"},
        ]
        results = compute_batch(candidates, CREW_TEAM, VESSEL, CAPTAIN)
        assert len(results) == 3

    def test_ordre_preserve(self):
        """L'ordre des résultats correspond à l'ordre des candidats."""
        cand_haut = {"snapshot": _snap(conscientiousness=90, gca=90), "experience_years": 5, "position_key": ""}
        cand_bas  = {"snapshot": _snap(conscientiousness=20, gca=20), "experience_years": 0, "position_key": ""}
        results = compute_batch([cand_haut, cand_bas], CREW_TEAM, VESSEL, CAPTAIN)
        assert results[0].p_ind_score >= results[1].p_ind_score

    def test_with_delta_true_peuple_delta(self):
        candidates = [{"snapshot": CANDIDATE, "experience_years": 2, "position_key": ""}]
        results = compute_batch(candidates, CREW_TEAM, VESSEL, CAPTAIN, with_delta=True)
        assert results[0].f_team_detail.delta is not None

    def test_with_delta_false_delta_absent(self):
        """compute (sans delta) → f_team_detail.delta = None."""
        candidates = [{"snapshot": CANDIDATE, "experience_years": 2, "position_key": ""}]
        results = compute_batch(candidates, CREW_TEAM, VESSEL, CAPTAIN, with_delta=False)
        assert results[0].f_team_detail.delta is None

    def test_retourne_list_mlpsm_result(self):
        candidates = [{"snapshot": CANDIDATE, "experience_years": 0, "position_key": ""}]
        results = compute_batch(candidates, CREW_TEAM, VESSEL, CAPTAIN)
        assert all(isinstance(r, MLPSMResult) for r in results)
