from __future__ import annotations
"""
Tests purs pour app.engine.pe_fit.trait_extractor.

Couvre :
    - Snapshot complet → score réel (pas de fallback)
    - Snapshot vide {} → extract_with_fallback retourne 50.0, extract_strict retourne None
    - Format Big Five dict {"score": x} vs float direct
    - emotional_stability calculée depuis neuroticism si emotional_stability absent
    - resilience proxiée depuis emotional_stability (extract_with_fallback uniquement)
    - resilience absente → None pour extract_strict (pas de proxy)
    - Préférences leadership depuis leadership_preferences direct
    - Préférences leadership dérivées depuis Big Five si leadership_preferences absent
    - gca calculée depuis sous-scores si gca_score absent
    - Trait inconnu → extract_with_fallback retourne 50.0, extract_strict retourne None
"""
import pytest
from app.engine.pe_fit.trait_extractor import (
    extract_with_fallback,
    extract_strict,
)

# ── Fixtures de snapshots ──────────────────────────────────────────────────────

FULL_SNAPSHOT = {
    "cognitive": {
        "gca_score": 72.0,
        "logical": 70.0,
        "numerical": 68.0,
        "verbal": 75.0,
    },
    "emotional_stability": 65.0,
    "resilience": 58.0,
    "big_five": {
        "agreeableness":     {"score": 80.0},
        "conscientiousness": {"score": 70.0},
        "openness":          {"score": 60.0},
        "extraversion":      {"score": 55.0},
        "neuroticism":       {"score": 35.0},
    },
    "leadership_preferences": {
        "autonomy_preference":  0.75,
        "feedback_preference":  0.60,
        "structure_preference": 0.50,
    },
}


# ── Tests : extract_with_fallback ─────────────────────────────────────────────

class TestExtractWithFallback:

    # Snapshot complet — scores réels, pas de fallback

    def test_gca_depuis_snapshot_complet(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "gca")
        assert result == 72.0

    def test_emotional_stability_depuis_snapshot_complet(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "emotional_stability")
        assert result == 65.0

    def test_resilience_depuis_snapshot_complet(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "resilience")
        assert result == 58.0

    def test_agreeableness_format_dict(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "agreeableness")
        assert result == 80.0

    def test_conscientiousness_format_dict(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "conscientiousness")
        assert result == 70.0

    def test_openness_format_dict(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "openness")
        assert result == 60.0

    def test_extraversion_format_dict(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "extraversion")
        assert result == 55.0

    def test_neuroticism_format_dict(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "neuroticism")
        assert result == 35.0

    def test_autonomy_preference_depuis_leadership_prefs(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "autonomy_preference")
        assert result == pytest.approx(75.0)

    def test_feedback_preference_depuis_leadership_prefs(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "feedback_preference")
        assert result == pytest.approx(60.0)

    def test_structure_preference_depuis_leadership_prefs(self):
        result = extract_with_fallback(FULL_SNAPSHOT, "structure_preference")
        assert result == pytest.approx(50.0)

    # Snapshot vide — fallback 50.0

    def test_snapshot_vide_gca_retourne_fallback(self):
        result = extract_with_fallback({}, "gca")
        assert result == 50.0

    def test_snapshot_vide_emotional_stability_retourne_fallback(self):
        result = extract_with_fallback({}, "emotional_stability")
        assert result == 50.0

    def test_snapshot_vide_resilience_retourne_fallback(self):
        result = extract_with_fallback({}, "resilience")
        assert result == 50.0

    def test_snapshot_vide_agreeableness_retourne_fallback(self):
        result = extract_with_fallback({}, "agreeableness")
        assert result == 50.0

    def test_snapshot_vide_trait_inconnu_retourne_fallback(self):
        result = extract_with_fallback({}, "trait_inexistant")
        assert result == 50.0

    # Format Big Five — float direct vs dict

    def test_big_five_format_float_direct(self):
        snapshot = {"big_five": {"agreeableness": 77.0}}
        result = extract_with_fallback(snapshot, "agreeableness")
        assert result == 77.0

    def test_big_five_format_dict_score(self):
        snapshot = {"big_five": {"conscientiousness": {"score": 63.0}}}
        result = extract_with_fallback(snapshot, "conscientiousness")
        assert result == 63.0

    # emotional_stability calculée depuis neuroticism

    def test_emotional_stability_depuis_neuroticism(self):
        snapshot = {"big_five": {"neuroticism": {"score": 40.0}}}
        result = extract_with_fallback(snapshot, "emotional_stability")
        assert result == pytest.approx(60.0)

    def test_emotional_stability_depuis_neuroticism_float_direct(self):
        snapshot = {"big_five": {"neuroticism": 30.0}}
        result = extract_with_fallback(snapshot, "emotional_stability")
        assert result == pytest.approx(70.0)

    def test_emotional_stability_directe_prioritaire_sur_neuroticism(self):
        snapshot = {
            "emotional_stability": 80.0,
            "big_five": {"neuroticism": {"score": 10.0}},
        }
        result = extract_with_fallback(snapshot, "emotional_stability")
        assert result == 80.0  # direct, pas 100 - 10 = 90

    # resilience proxiée depuis emotional_stability

    def test_resilience_proxy_depuis_emotional_stability(self):
        snapshot = {"emotional_stability": 62.0}
        result = extract_with_fallback(snapshot, "resilience")
        assert result == 62.0

    def test_resilience_proxy_depuis_neuroticism_quand_es_et_resilience_absents(self):
        snapshot = {"big_five": {"neuroticism": {"score": 25.0}}}
        result = extract_with_fallback(snapshot, "resilience")
        assert result == pytest.approx(75.0)

    def test_resilience_directe_prioritaire_sur_proxy(self):
        snapshot = {
            "resilience": 45.0,
            "emotional_stability": 90.0,
        }
        result = extract_with_fallback(snapshot, "resilience")
        assert result == 45.0

    # Préférences leadership — dérivation depuis Big Five

    def test_structure_preference_depuis_conscientiousness(self):
        snapshot = {"big_five": {"conscientiousness": {"score": 68.0}}}
        result = extract_with_fallback(snapshot, "structure_preference")
        assert result == 68.0

    def test_autonomy_preference_depuis_openness(self):
        snapshot = {"big_five": {"openness": {"score": 55.0}}}
        result = extract_with_fallback(snapshot, "autonomy_preference")
        assert result == 55.0

    def test_feedback_preference_depuis_openness(self):
        snapshot = {"big_five": {"openness": 48.0}}
        result = extract_with_fallback(snapshot, "feedback_preference")
        assert result == 48.0

    def test_leadership_pref_direct_prioritaire_sur_bigfive(self):
        snapshot = {
            "leadership_preferences": {"autonomy_preference": 0.80},
            "big_five": {"openness": {"score": 30.0}},
        }
        result = extract_with_fallback(snapshot, "autonomy_preference")
        assert result == pytest.approx(80.0)

    # gca depuis sous-scores si gca_score absent

    def test_gca_depuis_sous_scores_moyennne(self):
        snapshot = {
            "cognitive": {
                "logical": 60.0,
                "numerical": 70.0,
                "verbal": 80.0,
            }
        }
        result = extract_with_fallback(snapshot, "gca")
        assert result == pytest.approx(70.0)

    def test_gca_depuis_sous_scores_partiels(self):
        snapshot = {
            "cognitive": {
                "logical": 50.0,
                "verbal": 90.0,
            }
        }
        result = extract_with_fallback(snapshot, "gca")
        assert result == pytest.approx(70.0)

    def test_gca_score_prioritaire_sur_sous_scores(self):
        snapshot = {
            "cognitive": {
                "gca_score": 55.0,
                "logical": 80.0,
                "numerical": 90.0,
                "verbal": 85.0,
            }
        }
        result = extract_with_fallback(snapshot, "gca")
        assert result == 55.0


# ── Tests : extract_strict ────────────────────────────────────────────────────

class TestExtractStrict:

    # Snapshot complet — scores réels

    def test_gca_depuis_snapshot_complet(self):
        result = extract_strict(FULL_SNAPSHOT, "gca")
        assert result == 72.0

    def test_emotional_stability_depuis_snapshot_complet(self):
        result = extract_strict(FULL_SNAPSHOT, "emotional_stability")
        assert result == 65.0

    def test_resilience_depuis_snapshot_complet(self):
        result = extract_strict(FULL_SNAPSHOT, "resilience")
        assert result == 58.0

    def test_agreeableness_format_dict(self):
        result = extract_strict(FULL_SNAPSHOT, "agreeableness")
        assert result == 80.0

    def test_autonomy_preference_depuis_leadership_prefs(self):
        result = extract_strict(FULL_SNAPSHOT, "autonomy_preference")
        assert result == pytest.approx(75.0)

    # Snapshot vide — None (jamais 50.0)

    def test_snapshot_vide_gca_retourne_none(self):
        result = extract_strict({}, "gca")
        assert result is None

    def test_snapshot_vide_emotional_stability_retourne_none(self):
        result = extract_strict({}, "emotional_stability")
        assert result is None

    def test_snapshot_vide_resilience_retourne_none(self):
        result = extract_strict({}, "resilience")
        assert result is None

    def test_snapshot_vide_agreeableness_retourne_none(self):
        result = extract_strict({}, "agreeableness")
        assert result is None

    def test_snapshot_vide_trait_inconnu_retourne_none(self):
        result = extract_strict({}, "trait_inexistant")
        assert result is None

    # Différence critique : resilience sans proxy ES pour extract_strict

    def test_resilience_absent_ne_proxie_pas_es(self):
        """extract_strict retourne None même si emotional_stability est présente."""
        snapshot = {"emotional_stability": 70.0}
        result = extract_strict(snapshot, "resilience")
        assert result is None

    def test_resilience_absent_ne_proxie_pas_neuroticism(self):
        """extract_strict retourne None même si neuroticism est présent."""
        snapshot = {"big_five": {"neuroticism": {"score": 20.0}}}
        result = extract_strict(snapshot, "resilience")
        assert result is None

    # Format Big Five — float direct vs dict

    def test_big_five_format_float_direct(self):
        snapshot = {"big_five": {"extraversion": 44.0}}
        result = extract_strict(snapshot, "extraversion")
        assert result == 44.0

    def test_big_five_format_dict_score(self):
        snapshot = {"big_five": {"openness": {"score": 51.0}}}
        result = extract_strict(snapshot, "openness")
        assert result == 51.0

    # emotional_stability calculée depuis neuroticism

    def test_emotional_stability_depuis_neuroticism(self):
        snapshot = {"big_five": {"neuroticism": {"score": 50.0}}}
        result = extract_strict(snapshot, "emotional_stability")
        assert result == pytest.approx(50.0)

    def test_emotional_stability_directe_prioritaire(self):
        snapshot = {
            "emotional_stability": 42.0,
            "big_five": {"neuroticism": {"score": 5.0}},
        }
        result = extract_strict(snapshot, "emotional_stability")
        assert result == 42.0

    # Préférences leadership — dérivation depuis Big Five

    def test_structure_preference_depuis_conscientiousness(self):
        snapshot = {"big_five": {"conscientiousness": {"score": 72.0}}}
        result = extract_strict(snapshot, "structure_preference")
        assert result == 72.0

    def test_autonomy_preference_depuis_openness(self):
        snapshot = {"big_five": {"openness": 66.0}}
        result = extract_strict(snapshot, "autonomy_preference")
        assert result == 66.0

    def test_leadership_pref_absent_big_five_aussi_absent_retourne_none(self):
        result = extract_strict({}, "structure_preference")
        assert result is None

    # gca depuis sous-scores si gca_score absent

    def test_gca_depuis_sous_scores(self):
        snapshot = {
            "cognitive": {
                "logical": 60.0,
                "numerical": 80.0,
                "verbal": 70.0,
            }
        }
        result = extract_strict(snapshot, "gca")
        assert result == pytest.approx(70.0)

    def test_gca_cognitive_vide_retourne_none(self):
        snapshot = {"cognitive": {}}
        result = extract_strict(snapshot, "gca")
        assert result is None

    # Jamais de valeur 50.0 en mode strict

    def test_extract_strict_ne_retourne_jamais_50_comme_fallback(self):
        """Vérifie que None est retourné et pas la valeur sentinelle 50.0."""
        traits = [
            "gca", "emotional_stability", "resilience", "agreeableness",
            "conscientiousness", "openness", "extraversion", "neuroticism",
            "autonomy_preference", "feedback_preference", "structure_preference",
            "trait_inconnu",
        ]
        for trait in traits:
            result = extract_strict({}, trait)
            assert result is None, (
                f"extract_strict({{}}, '{trait}') a retourné {result!r} au lieu de None"
            )
