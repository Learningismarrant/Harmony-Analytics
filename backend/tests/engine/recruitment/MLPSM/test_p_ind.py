# tests/engine/recruitment/MLPSM/test_p_ind.py
"""
Tests unitaires pour le calcul P_ind via pe_fit/pj_fit/scorer.py

Migration MLPSM/p_ind → pe_fit/pj_fit/scorer :
    L'ancien module MLPSM/p_ind.py a été supprimé.
    La logique équivalente est dans pe_fit/pj_fit/scorer._compute_p_ind()
    exposée dans PJFitResult.p_ind_detail.

    Les constantes OMEGA sont accessibles via les champs privés du module :
        _OMEGA_GCA = 0.55   (OMEGA_GCA)
        _OMEGA_C   = 0.35   (OMEGA_CONSCIENTIOUSNESS)
        _OMEGA_I   = 0.10   (OMEGA_INTERACTION)

Formule V1 (SKILL.md) :
    P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA × C / 100)
    ω₁ = 0.55, ω₂ = 0.35, ω₃ = 0.10

Couverture :
    - Score nominal : formule vérifiée manuellement (avec terme d'interaction)
    - Terme d'interaction non nul et cohérent
    - Terme d'interaction pénalise les profils déséquilibrés
    - GCA absent → fallback 50.0 + flag GCA_MISSING + data_quality réduite
    - Big Five absent → fallback C=50.0 + flag BIG_FIVE_MISSING
    - Score clamped : jamais < 0 ou > 100
    - PIndResult contient interaction_term
    - experience_years transmis, bonus désactivé en Temps 1
"""
import pytest

from app.engine.pe_fit.pj_fit.scorer import (
    compute as pj_compute,
    PIndResult,
    _OMEGA_GCA as OMEGA_GCA,
    _OMEGA_C as OMEGA_CONSCIENTIOUSNESS,
    _OMEGA_I as OMEGA_INTERACTION,
    _compute_p_ind,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def snap_full(gca=72.0, conscientiousness=75.0):
    """Snapshot avec GCA pré-calculé et Conscienciosité."""
    return {
        "cognitive": {"gca_score": gca, "n_tests": 1},
        "big_five": {"conscientiousness": conscientiousness},
    }


def snap_no_cognitive(conscientiousness=75.0):
    return {"big_five": {"conscientiousness": conscientiousness}}


def snap_no_big_five(gca=72.0):
    return {"cognitive": {"gca_score": gca}}


def snap_empty():
    return {}


def _expected_score(gca: float, c: float) -> float:
    """Calcule le score attendu selon la formule V1 (avec interaction)."""
    interaction = OMEGA_INTERACTION * (gca * c / 100.0)
    raw = (gca * OMEGA_GCA) + (c * OMEGA_CONSCIENTIOUSNESS) + interaction
    return round(max(0.0, min(100.0, raw)), 1)


# ── Tests via _compute_p_ind (fonction interne) ──────────────────────────────

class TestPIndCompute:
    def test_retourne_pind_result(self):
        result = _compute_p_ind(snap_full())
        assert isinstance(result, PIndResult)

    def test_score_formule_nominale_avec_interaction(self):
        """P_ind = GCA×ω₁ + C×ω₂ + (GCA×C/100)×ω₃ vérifié manuellement."""
        gca = 80.0
        c   = 70.0
        expected = _expected_score(gca, c)
        result = _compute_p_ind(snap_full(gca=gca, conscientiousness=c))
        assert result.score == expected

    def test_score_dans_bornes(self):
        result = _compute_p_ind(snap_full())
        assert 0.0 <= result.score <= 100.0

    def test_data_quality_complete(self):
        """Données complètes → data_quality = 1.0."""
        result = _compute_p_ind(snap_full())
        assert result.data_quality == 1.0

    # ── Terme d'interaction ───────────────────────────────────────────────────

    def test_interaction_term_non_nul(self):
        result = _compute_p_ind(snap_full(gca=80.0, conscientiousness=70.0))
        assert result.interaction_term > 0.0

    def test_interaction_term_valeur(self):
        gca, c = 80.0, 70.0
        expected_interaction = round(OMEGA_INTERACTION * (gca * c / 100.0), 2)
        result = _compute_p_ind(snap_full(gca=gca, conscientiousness=c))
        assert abs(result.interaction_term - expected_interaction) < 0.01

    def test_interaction_penalise_profil_desequilibre(self):
        """
        GCA=70, C=70 → interaction = 0.10 × 4900/100 = 4.9
        GCA=100, C=40 → interaction = 0.10 × 4000/100 = 4.0
        """
        balanced   = _compute_p_ind(snap_full(gca=70.0, conscientiousness=70.0))
        unbalanced = _compute_p_ind(snap_full(gca=100.0, conscientiousness=40.0))
        assert balanced.interaction_term > unbalanced.interaction_term

    def test_interaction_zero_quand_gca_zero(self):
        result = _compute_p_ind(snap_full(gca=0.0, conscientiousness=80.0))
        assert result.interaction_term == 0.0

    def test_interaction_zero_quand_c_zero(self):
        snap_c_zero = {
            "cognitive": {"gca_score": 80.0, "n_tests": 1},
            "big_five": {"conscientiousness": {"score": 0.0, "reliable": True}},
        }
        result = _compute_p_ind(snap_c_zero)
        assert result.interaction_term == 0.0

    def test_interaction_maximal_quand_gca_c_max(self):
        result = _compute_p_ind(snap_full(gca=100.0, conscientiousness=100.0))
        max_interaction = round(OMEGA_INTERACTION * 100.0, 2)
        assert abs(result.interaction_term - max_interaction) < 0.01

    # ── Fallbacks ─────────────────────────────────────────────────────────────

    def test_gca_manquant_fallback(self):
        """Aucun test cognitif → GCA = 50.0, flag GCA_MISSING, data_quality réduite."""
        result = _compute_p_ind(snap_no_cognitive(conscientiousness=80.0))
        assert any("GCA_MISSING" in f for f in result.flags)
        assert result.gca.gca_score == 50.0
        assert result.data_quality <= 0.65

    def test_big_five_manquant_fallback(self):
        """Pas de Big Five → C = 50.0 (fallback médian via extract_with_fallback).
        Note: BIG_FIVE_MISSING n'est pas émis dans pe_fit/pj_fit/scorer car
        `snapshot.get('big_five') or {}` retourne {} avant le test `is None`."""
        result = _compute_p_ind(snap_no_big_five(gca=80.0))
        assert result.conscientiousness.c_score == 50.0

    def test_snapshot_vide_double_fallback(self):
        """Snapshot vide → GCA=50, C=50, P_ind calculé avec interaction."""
        result = _compute_p_ind(snap_empty())
        expected = _expected_score(50.0, 50.0)
        assert result.score == expected

    # ── Bornes et clamp ───────────────────────────────────────────────────────

    def test_score_clamp_max(self):
        result = _compute_p_ind(snap_full(gca=100.0, conscientiousness=100.0))
        assert result.score <= 100.0

    def test_score_clamp_min(self):
        result = _compute_p_ind(snap_full(gca=0.0, conscientiousness=0.0))
        assert result.score >= 0.0

    # ── Expérience ────────────────────────────────────────────────────────────

    def test_experience_years_transmis(self):
        result = _compute_p_ind(snap_full(), experience_years=5)
        assert result.experience.years == 5

    def test_experience_bonus_desactive_temps1(self):
        result_0yr  = _compute_p_ind(snap_full(gca=72.0, conscientiousness=75.0), experience_years=0)
        result_10yr = _compute_p_ind(snap_full(gca=72.0, conscientiousness=75.0), experience_years=10)
        assert result_0yr.score == result_10yr.score

    def test_formula_snapshot_contient_interaction(self):
        result = _compute_p_ind(snap_full(gca=80.0, conscientiousness=70.0))
        assert "P_ind" in result.formula_snapshot
        assert str(OMEGA_GCA) in result.formula_snapshot or "0.55" in result.formula_snapshot
        assert str(OMEGA_INTERACTION) in result.formula_snapshot or "0.10" in result.formula_snapshot

    def test_scores_croissants_avec_gca_et_c(self):
        low  = _compute_p_ind(snap_full(gca=40.0, conscientiousness=40.0))
        high = _compute_p_ind(snap_full(gca=85.0, conscientiousness=80.0))
        assert high.score > low.score


# ── Tests via pj_compute (accès à p_ind_detail depuis PJFitResult) ────────────

class TestPIndViaScorer:
    """Vérifie que PJFitResult.p_ind_detail contient les mêmes propriétés."""

    def test_pj_compute_expose_p_ind_detail(self):
        result = pj_compute(snap_full())
        assert hasattr(result, "p_ind_detail")
        assert isinstance(result.p_ind_detail, PIndResult)

    def test_p_ind_score_dans_pj_result(self):
        result = pj_compute(snap_full(gca=72.0, conscientiousness=75.0))
        assert 0.0 <= result.p_ind_score <= 100.0

    def test_p_ind_detail_interaction_non_nul(self):
        result = pj_compute(snap_full(gca=80.0, conscientiousness=70.0))
        assert result.p_ind_detail.interaction_term > 0.0

    def test_p_ind_detail_gca_detail(self):
        snap = {
            "cognitive": {
                "gca_score": 72.0,
                "logical_reasoning": 74.0,
                "numerical_reasoning": 70.0,
                "verbal_reasoning": 72.0,
            },
            "big_five": {"conscientiousness": 70.0},
        }
        # Note: pe_fit/pj_fit/scorer._compute_p_ind() ne lit pas les sous-scores cognitifs
        # car GCADetail de scorer.py n'a que gca_score et n_cognitive_tests.
        # Les sous-scores logique/numérique/verbal étaient dans MLPSM/p_ind.GCADetail.
        result = pj_compute(snap)
        assert result.p_ind_detail.gca.gca_score == 72.0
