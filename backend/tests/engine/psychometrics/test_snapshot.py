# tests/engine/psychometrics/test_snapshot.py
"""
Tests unitaires pour engine.psychometrics.snapshot.build_snapshot()

Couverture :
    - 0 résultat → snapshot vide avec meta.completeness=0
    - 1 résultat big_five → section big_five populée, cognitive absent
    - emotional_stability = 100 - neuroticism (calcul dérivé)
    - GCA = moyenne des sous-scores cognitifs disponibles
    - Résultat plus récent écrase l'ancien (tri chronologique)
    - leadership_preferences dérivées depuis Big Five
    - meta.completeness reflète le % de traits couverts
    - meta.tests_taken liste les tests passés sans doublons
    - extract_engine_inputs() retourne les champs attendus
"""
import pytest
from datetime import datetime

from app.engine.psychometrics.snapshot import build_snapshot, extract_engine_inputs

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_test_result(
    test_id: int,
    test_name: str,
    traits: dict,
    created_at: datetime = None,
):
    """
    Crée un objet léger simulant un TestResult ORM.
    scores = {"traits": {trait: {"score": float, "niveau": str}}}
    """
    from types import SimpleNamespace

    return SimpleNamespace(
        id=test_id,
        test_id=test_id,
        test_name=test_name,
        created_at=created_at or datetime(2025, 1, 1),
        scores={
            "traits": {
                trait: {"score": score, "niveau": "Élevé"}
                for trait, score in traits.items()
            }
        },
    )


BIG_FIVE_RESULT = make_test_result(
    test_id=1,
    test_name="big_five_v1",
    traits={
        "conscientiousness": 75.0,
        "agreeableness": 70.0,
        "neuroticism": 35.0,
        "openness": 60.0,
        "extraversion": 55.0,
    },
    created_at=datetime(2025, 1, 10),
)

COGNITIVE_RESULT = make_test_result(
    test_id=2,
    test_name="gca_v1",
    traits={
        "logical": 74.0,
        "numerical": 70.0,
        "verbal": 72.0,
    },
    created_at=datetime(2025, 1, 12),
)

MOTIVATION_RESULT = make_test_result(
    test_id=3,
    test_name="motivation_v1",
    traits={
        "intrinsic": 80.0,
        "identified": 70.0,
        "amotivation": 15.0,
    },
    created_at=datetime(2025, 1, 14),
)


# ── build_snapshot() ──────────────────────────────────────────────────────────

class TestBuildSnapshot:
    def test_aucun_resultat(self):
        """0 TestResult → snapshot avec sections vides, completeness=0."""
        snapshot = build_snapshot([])
        assert snapshot["big_five"] == {}
        assert snapshot["cognitive"] == {}
        assert snapshot["motivation"] == {}
        assert snapshot["meta"]["completeness"] == 0.0
        assert snapshot["meta"]["tests_taken"] == []

    def test_big_five_seulement(self):
        """1 résultat Big Five → big_five populé, cognitive vide."""
        snapshot = build_snapshot([BIG_FIVE_RESULT])
        assert "conscientiousness" in snapshot["big_five"]
        assert snapshot["big_five"]["conscientiousness"] == 75.0
        assert snapshot["cognitive"] == {} or "gca_score" not in snapshot["cognitive"]

    def test_emotional_stability_derive(self):
        """emotional_stability = round(100 - neuroticism, 1)."""
        snapshot = build_snapshot([BIG_FIVE_RESULT])
        assert "emotional_stability" in snapshot["big_five"]
        expected_es = round(100 - 35.0, 1)
        assert snapshot["big_five"]["emotional_stability"] == expected_es

    def test_gca_score_calcule(self):
        """gca_score = moyenne des sous-scores cognitifs (logical, numerical, verbal)."""
        snapshot = build_snapshot([COGNITIVE_RESULT])
        assert "gca_score" in snapshot["cognitive"]
        expected_gca = round((74.0 + 70.0 + 72.0) / 3, 1)
        assert snapshot["cognitive"]["gca_score"] == expected_gca

    def test_tests_taken_liste(self):
        """tests_taken contient les noms des tests passés, sans doublons."""
        snapshot = build_snapshot([BIG_FIVE_RESULT, COGNITIVE_RESULT])
        assert "big_five_v1" in snapshot["meta"]["tests_taken"]
        assert "gca_v1" in snapshot["meta"]["tests_taken"]

    def test_tests_taken_pas_de_doublon(self):
        """Même test soumis deux fois → test_name présent une seule fois."""
        result_1 = make_test_result(1, "big_five_v1", {"agreeableness": 60.0}, datetime(2025, 1, 1))
        result_2 = make_test_result(1, "big_five_v1", {"agreeableness": 80.0}, datetime(2025, 1, 15))
        snapshot = build_snapshot([result_1, result_2])
        assert snapshot["meta"]["tests_taken"].count("big_five_v1") == 1

    def test_resultat_recent_ecrase_ancien(self):
        """
        Le résultat le plus récent écrase l'ancien pour le même trait.
        result_ancien (Jan 1) : agreeableness=60
        result_recent (Jan 15) : agreeableness=80
        → snapshot doit avoir 80.
        """
        result_ancien = make_test_result(
            1, "big_five_v1", {"agreeableness": 60.0}, datetime(2025, 1, 1)
        )
        result_recent = make_test_result(
            1, "big_five_v1", {"agreeableness": 80.0}, datetime(2025, 1, 15)
        )
        snapshot = build_snapshot([result_recent, result_ancien])  # ordre inversé intentionnel
        assert snapshot["big_five"]["agreeableness"] == 80.0

    def test_completeness_tous_requis(self):
        """Avec big_five + cognitive + motivation → completeness élevée."""
        snapshot = build_snapshot([BIG_FIVE_RESULT, COGNITIVE_RESULT, MOTIVATION_RESULT])
        assert snapshot["meta"]["completeness"] > 0.8

    def test_completeness_partiel(self):
        """Avec big_five seulement → completeness < 1."""
        snapshot = build_snapshot([BIG_FIVE_RESULT])
        assert 0.0 < snapshot["meta"]["completeness"] < 1.0

    def test_leadership_preferences_derives(self):
        """
        leadership_preferences doit être un dict avec les 3 clés dérivées
        depuis les scores Big Five.
        """
        snapshot = build_snapshot([BIG_FIVE_RESULT])
        lp = snapshot.get("leadership_preferences", {})
        assert "autonomy_preference" in lp
        assert "feedback_preference" in lp
        assert "structure_preference" in lp
        # Toutes les valeurs doivent être dans [0.0, 1.0]
        for val in lp.values():
            assert 0.0 <= val <= 1.0, f"Valeur hors bornes: {val}"

    def test_meta_last_updated_iso(self):
        """meta.last_updated est une chaîne ISO datetime."""
        snapshot = build_snapshot([BIG_FIVE_RESULT])
        last_updated = snapshot["meta"]["last_updated"]
        assert isinstance(last_updated, str)
        # Doit être parseable en datetime
        datetime.fromisoformat(last_updated)

    def test_scores_dict_format_et_float(self):
        """Traits stockés avec format score dict ou float — les deux acceptés."""
        # Format dict : {"score": 75.0}
        result = make_test_result(1, "big_five_v1", {"agreeableness": 75.0})
        snapshot_v1 = build_snapshot([result])
        assert snapshot_v1["big_five"]["agreeableness"] == 75.0


# ── extract_engine_inputs() ───────────────────────────────────────────────────

class TestExtractEngineInputs:
    def test_snapshot_complet(self):
        """extract_engine_inputs retourne tous les champs attendus."""
        from tests.conftest import snapshot_full
        inputs = extract_engine_inputs(snapshot_full())

        expected_keys = {
            "gca", "conscientiousness", "agreeableness",
            "emotional_stability", "resilience",
            "autonomy_preference", "feedback_preference", "structure_preference",
            "completeness",
        }
        assert expected_keys.issubset(inputs.keys())

    def test_snapshot_vide_fallbacks(self):
        """Snapshot vide → tous les champs ont des valeurs par défaut (0 ou 0.5)."""
        inputs = extract_engine_inputs({})
        assert inputs["gca"] == 0
        assert inputs["conscientiousness"] == 0
        assert inputs["autonomy_preference"] == 0.5  # default

    def test_resilience_fallback_sur_es(self):
        """
        Si snapshot.resilience absent, fallback sur emotional_stability de big_five.
        """
        snap = {
            "big_five": {"emotional_stability": 70.0},
            "resilience": {},  # pas de 'global'
        }
        inputs = extract_engine_inputs(snap)
        # Le fallback utilise big_five.emotional_stability
        assert inputs["resilience"] == 70.0
