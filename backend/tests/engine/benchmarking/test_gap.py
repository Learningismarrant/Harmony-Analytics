# tests/engine/benchmarking/test_gap.py
"""
Tests unitaires pour engine.benchmarking.gap

Couverture :
    compute_gap_profile() :
        - Snapshot Captain complet → structure + cohérence des gap_bands
        - Position inconnue → retourne []
        - Snapshot vide → retourne []
        - Polarité "high" — logique de banding
        - Polarité "low" — neuroticism

    Advice :
        - Trait absent de CANDIDATE_GAP_ADVICE → fallback "default"

    get_gap_summary() :
        - Compteurs et completeness corrects
"""
import pytest

from app.engine.benchmarking.gap import (
    GapTrait,
    compute_gap_profile,
    get_gap_summary,
    _gap_band,
)
from app.content.advice.advice_candidate import CANDIDATE_GAP_ADVICE

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _captain_snapshot() -> dict:
    """Snapshot réaliste pour un Captain — couvre Big Five + motivation + cognitif."""
    return {
        "big_five": {
            "conscientiousness": 72.0,    # sous la cible Captain (95) → gap
            "agreeableness":     68.0,    # sous la cible (70) → borderline strength
            "neuroticism":       25.0,    # cible (15) → developing (25-15=+10, pol low)
            "openness":          78.0,    # cible (80) → strength (−2)
            "extraversion":      70.0,    # cible (75) → strength (−5)
            "emotional_stability": 75.0,  # doit être EXCLU (dérivé de neuroticism)
        },
        "cognitive": {
            "gca_score": 78.0,            # doit être EXCLU
            "logical":   85.0,            # cible (90) → developing (−5)
            "numerical": 80.0,            # cible (80) → strength (0)
            "verbal":    80.0,            # cible (85) → strength (−5)
        },
        "motivation": {
            "intrinsic":  88.0,           # cible (90) → strength (−2)
            "identified": 82.0,           # cible (85) → strength (−3)
            "amotivation": 5.0,           # cible (0) → developing (+5, pol low)
        },
    }


# ── compute_gap_profile() ─────────────────────────────────────────────────────

class TestComputeGapProfileCaptain:
    def test_retourne_liste_gap_trait(self):
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        assert isinstance(result, list)
        assert all(isinstance(gt, GapTrait) for gt in result)

    def test_traits_attendus_presents(self):
        """Traits SME Captain couverts dans le snapshot → tous dans le résultat."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        traits_found = {gt.trait for gt in result}
        # Ces traits doivent être présents (couverts dans snapshot ET SME Captain)
        for trait in ("conscientiousness", "agreeableness", "neuroticism",
                      "openness", "extraversion", "logical", "numerical",
                      "verbal", "intrinsic", "identified", "amotivation"):
            assert trait in traits_found, f"Trait '{trait}' manquant dans le résultat"

    def test_emotional_stability_exclu(self):
        """emotional_stability est dans le snapshot mais pas dans le SME → exclu."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        traits = {gt.trait for gt in result}
        assert "emotional_stability" not in traits

    def test_gca_score_exclu(self):
        """gca_score est dans le snapshot cognitif mais pas dans le SME → exclu."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        traits = {gt.trait for gt in result}
        assert "gca_score" not in traits

    def test_conscientiousness_gap_band(self):
        """conscientiousness=72, SME=95 → gap_pts=-23 → 'developing' (pol high, -25<=-23<-10)."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        c = next(gt for gt in result if gt.trait == "conscientiousness")
        assert c.sme_target == 95.0
        assert c.gap_pts == pytest.approx(-23.0)
        assert c.gap_band == "developing"

    def test_neuroticism_gap_band(self):
        """neuroticism=25, SME=15 → gap_pts=+10 → 'developing' (pol low, 10<+10<=25)."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        n = next(gt for gt in result if gt.trait == "neuroticism")
        assert n.sme_target == 15.0
        assert n.gap_pts == pytest.approx(10.0)
        # gap_pts=10 est strictement > 10 ? Non, exactement 10 → strength (≤10)
        assert n.gap_band == "strength"

    def test_openness_strength(self):
        """openness=78, SME=80 → gap_pts=-2 → 'strength' (pol high, >=-10)."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        o = next(gt for gt in result if gt.trait == "openness")
        assert o.gap_band == "strength"

    def test_advice_non_vide(self):
        """Chaque GapTrait doit avoir un conseil non vide."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        for gt in result:
            assert isinstance(gt.advice, str)
            assert len(gt.advice) > 10, f"Conseil vide pour trait '{gt.trait}'"

    def test_gap_pts_calcul(self):
        """gap_pts = candidate_score - sme_target dans tous les cas."""
        result = compute_gap_profile(_captain_snapshot(), "Captain")
        for gt in result:
            assert gt.gap_pts == pytest.approx(
                gt.candidate_score - gt.sme_target, abs=0.01
            ), f"gap_pts incorrect pour '{gt.trait}'"


class TestComputeGapProfileUnknownPosition:
    def test_position_inconnue_retourne_liste_vide(self):
        result = compute_gap_profile(_captain_snapshot(), "UnknownPosition")
        assert result == []

    def test_position_vide_retourne_liste_vide(self):
        result = compute_gap_profile(_captain_snapshot(), "")
        assert result == []


class TestComputeGapProfileEmptySnapshot:
    def test_snapshot_vide_retourne_liste_vide(self):
        result = compute_gap_profile({}, "Captain")
        assert result == []

    def test_snapshot_none_sections_retourne_liste_vide(self):
        """Snapshot sans big_five/cognitive/motivation → résultat vide."""
        result = compute_gap_profile({"meta": {"version": "1.0"}}, "Captain")
        assert result == []


# ── Logique de banding par polarité ──────────────────────────────────────────

class TestGapBandHighPolarity:
    """Tests unitaires sur _gap_band() pour les traits à polarité 'high'."""

    def test_strength_exactement_moins_10(self):
        """gap_pts = -10 → strength (borne inclusive)."""
        assert _gap_band("conscientiousness", -10.0) == "strength"

    def test_strength_positif(self):
        """gap_pts = +5 → strength."""
        assert _gap_band("conscientiousness", 5.0) == "strength"

    def test_developing_moins_11(self):
        """gap_pts = -11 → developing."""
        assert _gap_band("conscientiousness", -11.0) == "developing"

    def test_developing_moins_25(self):
        """gap_pts = -25 → developing (borne inclusive)."""
        assert _gap_band("conscientiousness", -25.0) == "developing"

    def test_gap_moins_26(self):
        """gap_pts = -26 → gap."""
        assert _gap_band("conscientiousness", -26.0) == "gap"

    def test_gap_tres_negatif(self):
        """gap_pts = -50 → gap."""
        assert _gap_band("conscientiousness", -50.0) == "gap"

    def test_too_high_plus_16(self):
        """gap_pts = +16 → too_high."""
        assert _gap_band("conscientiousness", 16.0) == "too_high"

    def test_not_too_high_plus_15(self):
        """gap_pts = +15 est la borne : +15 → strength, +16 → too_high."""
        assert _gap_band("conscientiousness", 15.0) == "strength"
        assert _gap_band("conscientiousness", 15.1) == "too_high"


class TestGapBandLowPolarity:
    """Tests unitaires sur _gap_band() pour les traits à polarité 'low'."""

    def test_strength_zero(self):
        """neuroticism=0 → gap_pts=0 → strength."""
        assert _gap_band("neuroticism", 0.0) == "strength"

    def test_strength_exactement_10(self):
        """gap_pts=10 → strength (borne inclusive ≤10)."""
        assert _gap_band("neuroticism", 10.0) == "strength"

    def test_developing_11(self):
        """gap_pts=11 → developing."""
        assert _gap_band("neuroticism", 11.0) == "developing"

    def test_developing_25(self):
        """gap_pts=25 → developing (borne inclusive ≤25)."""
        assert _gap_band("neuroticism", 25.0) == "developing"

    def test_gap_26(self):
        """gap_pts=26 → gap."""
        assert _gap_band("neuroticism", 26.0) == "gap"

    def test_too_high_moins_16(self):
        """gap_pts=-16 → too_high (candidat trop bas par rapport à la cible low)."""
        assert _gap_band("neuroticism", -16.0) == "too_high"

    def test_not_too_high_moins_15(self):
        """gap_pts=-15 → strength (borne : <-15 pour too_high)."""
        assert _gap_band("neuroticism", -15.0) == "strength"


# ── Fallback advice ──────────────────────────────────────────────────────────

class TestAdviceFallback:
    def test_trait_inconnu_utilise_fallback_default(self):
        """Un trait absent de CANDIDATE_GAP_ADVICE doit utiliser CANDIDATE_GAP_ADVICE['default']."""
        from app.engine.benchmarking.gap import _get_advice

        # "fluid_reasoning" existe dans CANDIDATE_GAP_ADVICE mais peut être ignoré
        # On forge un nom de trait inexistant
        advice = _get_advice("trait_inexistant_xyz", "strength")
        expected = CANDIDATE_GAP_ADVICE["default"]["strength"]
        assert advice == expected

    def test_trait_connu_retourne_conseil_specifique(self):
        """Un trait présent dans CANDIDATE_GAP_ADVICE retourne son conseil propre."""
        from app.engine.benchmarking.gap import _get_advice

        advice = _get_advice("conscientiousness", "strength")
        expected = CANDIDATE_GAP_ADVICE["conscientiousness"]["strength"]
        assert advice == expected
        # Le conseil spécifique ne doit pas être identique au fallback
        assert advice != CANDIDATE_GAP_ADVICE["default"]["strength"]

    def test_fallback_toutes_les_bandes(self):
        """Chaque bande du fallback 'default' est non vide."""
        for band in ("strength", "developing", "gap", "too_high"):
            advice = CANDIDATE_GAP_ADVICE["default"].get(band, "")
            assert len(advice) > 0, f"Fallback vide pour la bande '{band}'"


# ── get_gap_summary() ─────────────────────────────────────────────────────────

class TestGetGapSummary:
    def _make_traits(self, bands: list[str]) -> list[GapTrait]:
        return [
            GapTrait(
                trait=f"trait_{i}",
                candidate_score=60.0,
                sme_target=70.0,
                gap_pts=-10.0,
                gap_band=band,
                advice="conseil test",
            )
            for i, band in enumerate(bands)
        ]

    def test_summary_liste_vide(self):
        summary = get_gap_summary([])
        assert summary["total_traits"] == 0
        assert summary["strengths"] == 0
        assert summary["developing"] == 0
        assert summary["gaps"] == 0
        assert summary["too_high"] == 0
        assert summary["completeness"] == 0.0

    def test_summary_compteurs_corrects(self):
        traits = self._make_traits(["strength", "strength", "developing", "gap", "too_high"])
        summary = get_gap_summary(traits)
        assert summary["total_traits"] == 5
        assert summary["strengths"] == 2
        assert summary["developing"] == 1
        assert summary["gaps"] == 1
        assert summary["too_high"] == 1

    def test_completeness_entre_0_et_1(self):
        """completeness est toujours dans [0, 1]."""
        traits = self._make_traits(["strength"] * 3)
        summary = get_gap_summary(traits)
        assert 0.0 <= summary["completeness"] <= 1.0

    def test_completeness_snapshot_complet(self):
        """Snapshot Captain complet → completeness > 0."""
        gap_traits = compute_gap_profile(_captain_snapshot(), "Captain")
        summary = get_gap_summary(gap_traits)
        assert summary["total_traits"] > 0
        assert summary["completeness"] > 0.0

    def test_champs_obligatoires_presents(self):
        traits = self._make_traits(["strength"])
        summary = get_gap_summary(traits)
        for key in ("total_traits", "strengths", "developing", "gaps", "too_high", "completeness"):
            assert key in summary, f"Clé '{key}' manquante dans le résumé"
