# tests/engine/recruitment/pe_fit/test_motivation_fit.py
"""
Tests unitaires pour engine.pe_fit.pj_fit.motivation_fit.scorer

Couverture :
    compute() sans position et sans profil idéal   → None
    test_perfect_match                              → score ≈ 100
    test_inverted_profile                           → score bas
    test_cosine_vs_euclidean_invariance             → même pattern, niveaux différents → même score
    test_fallback_all_missing                       → data_quality=0, score calculé quand même
    test_known_positions                            → Captain, Chef → score > 50 avec profil raisonnable
"""
import pytest
import math

from app.engine.pe_fit.pj_fit.motivation_fit.scorer import (
    compute,
    MotivationFitResult,
    SDT_DIMENSIONS,
    MOTIVATION_PROFILES_NORM,
    SDT_FALLBACK,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def snap_with_motivation(intrinsic=80, identified=80, introjected=30,
                          extrinsic_social=60, extrinsic_material=50, amotivation=10):
    return {
        "motivation": {
            "intrinsic": intrinsic,
            "identified": identified,
            "introjected": introjected,
            "extrinsic_social": extrinsic_social,
            "extrinsic_material": extrinsic_material,
            "amotivation": amotivation,
        }
    }


def snap_empty():
    return {}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestComputeReturnsNone:
    def test_returns_none_without_position_and_profile(self):
        result = compute(snap_empty(), position=None, ideal_profile=None)
        assert result is None

    def test_returns_none_without_position(self):
        result = compute(snap_with_motivation(), position=None)
        assert result is None

    def test_returns_none_with_unknown_position(self):
        result = compute(snap_with_motivation(), position="UnknownPosition123")
        assert result is None

    def test_returns_result_with_ideal_profile_override(self):
        """ideal_profile override permet le calcul même sans position."""
        profile = {dim: 50.0 for dim in SDT_DIMENSIONS}
        result = compute(snap_with_motivation(), position=None, ideal_profile=profile)
        assert result is not None
        assert isinstance(result, MotivationFitResult)


class TestPerfectMatch:
    def test_perfect_match_score_proche_de_100(self):
        """Vecteur candidat identique à idéal → score ≈ 100."""
        captain_profile = MOTIVATION_PROFILES_NORM["captain"]
        snap = {"motivation": {k: v for k, v in captain_profile.items()}}
        result = compute(snap, position="Captain")
        assert result is not None
        # Distance cosinus entre vecteurs identiques = 0 → score = 100
        assert result.score > 99.0

    def test_perfect_match_cosine_similarity_proche_de_un(self):
        captain_profile = MOTIVATION_PROFILES_NORM["captain"]
        snap = {"motivation": {k: v for k, v in captain_profile.items()}}
        result = compute(snap, position="Captain")
        assert result is not None
        assert result.cosine_similarity > 0.99

    def test_perfect_match_cosine_distance_proche_de_zero(self):
        captain_profile = MOTIVATION_PROFILES_NORM["captain"]
        snap = {"motivation": {k: v for k, v in captain_profile.items()}}
        result = compute(snap, position="Captain")
        assert result is not None
        assert result.cosine_distance < 0.01


class TestInvertedProfile:
    def test_inverted_profile_score_bas(self):
        """
        Profil opposé à l'idéal Captain :
        - intrinsic/identified bas, amotivation haut → pattern très différent.
        """
        inverted = snap_with_motivation(
            intrinsic=5,
            identified=5,
            introjected=90,
            extrinsic_social=90,
            extrinsic_material=95,
            amotivation=95,
        )
        result = compute(inverted, position="Captain")
        assert result is not None
        # Le profil Captain est (90,88,30,55,45,5) — très différent du profil inversé
        # On s'attend à un score nettement inférieur à 50
        assert result.score < 80.0

    def test_inverted_lower_than_perfect(self):
        """Le profil inversé doit avoir un score inférieur au profil parfait."""
        captain_profile = MOTIVATION_PROFILES_NORM["captain"]
        snap_perfect = {"motivation": {k: v for k, v in captain_profile.items()}}
        snap_inverted = snap_with_motivation(
            intrinsic=5, identified=5, introjected=90,
            extrinsic_social=90, extrinsic_material=95, amotivation=95,
        )
        result_perfect  = compute(snap_perfect,  position="Captain")
        result_inverted = compute(snap_inverted, position="Captain")
        assert result_perfect  is not None
        assert result_inverted is not None
        assert result_perfect.score > result_inverted.score


class TestCosineVsEuclideanInvariance:
    def test_meme_pattern_niveaux_differents_meme_score(self):
        """
        La distance cosinus ne dépend que du pattern relatif, pas des niveaux absolus.
        (80,80,30,60,50,10) vs (40,40,15,30,25,5) — pattern identique (ratio 2:1)
        → scores cosinus identiques ou très proches.
        """
        snap_high = snap_with_motivation(80, 80, 30, 60, 50, 10)
        snap_low  = snap_with_motivation(40, 40, 15, 30, 25, 5)

        result_high = compute(snap_high, position="Captain")
        result_low  = compute(snap_low,  position="Captain")

        assert result_high is not None
        assert result_low  is not None
        # Les deux scores doivent être très proches (différence < 1 point)
        assert abs(result_high.score - result_low.score) < 1.0

    def test_cosine_similarity_invariant_au_scaling(self):
        """La similarité cosinus est invariante au scaling scalaire."""
        base_dims = {"intrinsic": 70, "identified": 80, "introjected": 20,
                     "extrinsic_social": 50, "extrinsic_material": 40, "amotivation": 5}
        scaled_dims = {k: v * 2 for k, v in base_dims.items()}

        result_base   = compute({"motivation": base_dims},   position="Captain")
        result_scaled = compute({"motivation": scaled_dims}, position="Captain")

        assert result_base   is not None
        assert result_scaled is not None
        assert abs(result_base.cosine_similarity - result_scaled.cosine_similarity) < 0.001


class TestFallbackAllMissing:
    def test_fallback_all_missing_data_quality_zero(self):
        """Snapshot sans données motivation → data_quality = 0."""
        result = compute(snap_empty(), position="Captain")
        assert result is not None
        assert result.data_quality == 0.0

    def test_fallback_all_missing_score_calcule_quand_meme(self):
        """Même sans données, un score est calculé (fallback médian)."""
        result = compute(snap_empty(), position="Captain")
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_fallback_all_missing_flag_present(self):
        """Flag NO_SDT_DATA présent si aucune donnée SDT."""
        result = compute(snap_empty(), position="Captain")
        assert result is not None
        assert any("NO_SDT_DATA" in f for f in result.flags)

    def test_fallback_partiel_flag_fallback_sdt(self):
        """Données partielles → flag FALLBACK_SDT."""
        snap = {"motivation": {"intrinsic": 80}}  # seulement 1 dimension sur 6
        result = compute(snap, position="Captain")
        assert result is not None
        assert any("FALLBACK_SDT" in f for f in result.flags)
        assert result.fallback_count == 5  # 5 dimensions manquantes sur 6

    def test_fallback_count_correct(self):
        result = compute(snap_empty(), position="Captain")
        assert result is not None
        assert result.fallback_count == len(SDT_DIMENSIONS)


class TestKnownPositions:
    def test_captain_profil_raisonnable_score_eleve(self):
        """
        Candidat avec profil raisonnable pour Captain
        (intrinsic élevé, amotivation bas) → score > 50.
        """
        snap = snap_with_motivation(
            intrinsic=85, identified=82, introjected=28,
            extrinsic_social=50, extrinsic_material=45, amotivation=8,
        )
        result = compute(snap, position="Captain")
        assert result is not None
        assert result.score > 50.0

    def test_chef_profil_raisonnable_score_eleve(self):
        """
        Candidat avec profil raisonnable pour Chef
        (intrinsic très élevé, identified modéré) → score > 50.
        """
        snap = snap_with_motivation(
            intrinsic=90, identified=70, introjected=28,
            extrinsic_social=45, extrinsic_material=52, amotivation=6,
        )
        result = compute(snap, position="Chef")
        assert result is not None
        assert result.score > 50.0

    def test_position_case_insensitive(self):
        """La recherche de profil est case-insensitive."""
        snap = snap_with_motivation(80, 80, 30, 60, 50, 10)
        result_upper = compute(snap, position="Captain")
        result_lower = compute(snap, position="captain")
        assert result_upper is not None
        assert result_lower is not None
        assert result_upper.score == result_lower.score

    def test_dimension_gaps_tous_presents(self):
        """dimension_gaps contient une entrée par dimension SDT."""
        result = compute(snap_with_motivation(), position="Captain")
        assert result is not None
        assert len(result.dimension_gaps) == len(SDT_DIMENSIONS)

    def test_formula_snapshot_non_vide(self):
        result = compute(snap_with_motivation(), position="Captain")
        assert result is not None
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 0

    def test_result_score_dans_bornes(self):
        for pos in ["Captain", "Chef", "Bosun", "Deckhand", "Stewardess"]:
            result = compute(snap_with_motivation(), position=pos)
            assert result is not None
            assert 0.0 <= result.score <= 100.0, f"Score hors bornes pour {pos}"
