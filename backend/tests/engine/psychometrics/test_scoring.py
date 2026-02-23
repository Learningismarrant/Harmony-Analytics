# tests/engine/psychometrics/test_scoring.py
"""
Tests unitaires pour engine.psychometrics.scoring.calculate_scores()

Couverture :
    - Test Likert nominal (score, niveau, global_score)
    - Inversion d'items (reverse=True)
    - Test cognitif (correcte = max_score, incorrecte = 0)
    - Fiabilité : réponses trop rapides → is_reliable=False
    - Fiabilité : biais extrêmes > 70% → is_reliable=False
    - Questions inconnues (question_id absent de la map) → ignorées
    - Réponses vides → global_score=0.0, pas d'exception
    - Valeurs brutes invalides (string) → ignorées en mode likert
"""
import pytest
from types import SimpleNamespace

from app.engine.psychometrics.scoring import (
    calculate_scores,
    _get_level_label,
    THRESHOLD_LIKERT_HIGH,
    THRESHOLD_LIKERT_MEDIUM,
    THRESHOLD_COGNITIVE_EXCELLENT,
    THRESHOLD_COGNITIVE_STANDARD,
    MIN_SECONDS_PER_QUESTION,
    DESIRABILITY_EXTREME_THRESHOLD,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_response(question_id: int, valeur_choisie, seconds_spent: int = 10):
    return SimpleNamespace(
        question_id=question_id,
        valeur_choisie=valeur_choisie,
        seconds_spent=seconds_spent,
    )


def make_question(question_id: int, trait: str, reverse: bool = False, correct_answer=None):
    return SimpleNamespace(
        id=question_id,
        trait=trait,
        reverse=reverse,
        correct_answer=correct_answer,
    )


# ── _get_level_label ──────────────────────────────────────────────────────────

class TestGetLevelLabel:
    def test_likert_eleve(self):
        assert _get_level_label("likert", THRESHOLD_LIKERT_HIGH + 1) == "Élevé"

    def test_likert_moyen(self):
        assert _get_level_label("likert", 50.0) == "Moyen"

    def test_likert_faible(self):
        assert _get_level_label("likert", THRESHOLD_LIKERT_MEDIUM - 1) == "Faible"

    def test_cognitive_excellent(self):
        assert _get_level_label("cognitive", THRESHOLD_COGNITIVE_EXCELLENT) == "Excellent"

    def test_cognitive_standard(self):
        assert _get_level_label("cognitive", THRESHOLD_COGNITIVE_STANDARD) == "Standard"

    def test_cognitive_a_renforcer(self):
        assert _get_level_label("cognitive", 30.0) == "À renforcer"


# ── Test Likert ───────────────────────────────────────────────────────────────

class TestLikertScoring:
    def _make_likert_map(self):
        """5 items agreeableness, scale 1-5."""
        return {
            i: make_question(i, "agreeableness", reverse=False)
            for i in range(1, 6)
        }

    def test_score_maximal(self):
        """Tous 5/5 → score = 100."""
        questions_map = self._make_likert_map()
        responses = [make_response(i, 5) for i in range(1, 6)]
        result = calculate_scores(responses, questions_map, "likert", 5)
        assert result["traits"]["agreeableness"]["score"] == 100.0

    def test_score_minimal(self):
        """Tous 1/5 → score = 20%."""
        questions_map = self._make_likert_map()
        responses = [make_response(i, 1) for i in range(1, 6)]
        result = calculate_scores(responses, questions_map, "likert", 5)
        assert result["traits"]["agreeableness"]["score"] == 20.0

    def test_score_moitie(self):
        """Tous 3/5 → score = 60%."""
        questions_map = self._make_likert_map()
        responses = [make_response(i, 3) for i in range(1, 6)]
        result = calculate_scores(responses, questions_map, "likert", 5)
        assert result["traits"]["agreeableness"]["score"] == 60.0

    def test_reverse_item(self):
        """
        Item reverse : valeur calculée = (min + max) - brute.
        max_score=5, reverse: valeur_brute=1 → calculée = (1+5)-1 = 5.
        """
        q_map = {
            1: make_question(1, "neuroticism", reverse=True),
        }
        responses = [make_response(1, 1)]  # réponse "1" sur item reverse
        result = calculate_scores(responses, q_map, "likert", 5)
        # valeur calculée = 5, max_possible = 5 → score = 100%
        assert result["traits"]["neuroticism"]["score"] == 100.0

    def test_reverse_item_max(self):
        """Item reverse : réponse=5 → calculée = (1+5)-5 = 1 → score = 20%."""
        q_map = {1: make_question(1, "neuroticism", reverse=True)}
        responses = [make_response(1, 5)]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["traits"]["neuroticism"]["score"] == 20.0

    def test_multiple_traits(self):
        """Deux traits : A et C, scores distincts."""
        q_map = {
            1: make_question(1, "agreeableness"),
            2: make_question(2, "conscientiousness"),
        }
        responses = [
            make_response(1, 5),  # agreeableness → 100%
            make_response(2, 1),  # conscientiousness → 20%
        ]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["traits"]["agreeableness"]["score"] == 100.0
        assert result["traits"]["conscientiousness"]["score"] == 20.0

    def test_global_score_est_moyenne_des_traits(self):
        """global_score = moyenne des scores de traits."""
        q_map = {
            1: make_question(1, "agreeableness"),
            2: make_question(2, "conscientiousness"),
        }
        responses = [make_response(1, 5), make_response(2, 1)]
        result = calculate_scores(responses, q_map, "likert", 5)
        expected_global = (100.0 + 20.0) / 2
        assert result["global_score"] == round(expected_global, 1)

    def test_question_inconnue_ignoree(self):
        """Un question_id absent de la map est ignoré sans exception."""
        q_map = {1: make_question(1, "agreeableness")}
        responses = [
            make_response(1, 4),
            make_response(999, 5),  # inconnue
        ]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert "agreeableness" in result["traits"]
        assert result["traits"]["agreeableness"]["score"] == 80.0

    def test_valeur_invalide_ignoree(self):
        """Valeur non-entière ignorée en mode likert, pas d'exception."""
        q_map = {1: make_question(1, "agreeableness")}
        responses = [make_response(1, "abc")]
        result = calculate_scores(responses, q_map, "likert", 5)
        # max_possible = 0 car valeur ignorée → score = 0
        assert result["traits"]["agreeableness"]["score"] == 0.0

    def test_reponses_vides(self):
        """Aucune réponse → global_score = 0, pas d'exception."""
        q_map = {1: make_question(1, "agreeableness")}
        result = calculate_scores([], q_map, "likert", 5)
        assert result["global_score"] == 0
        assert result["reliability"]["is_reliable"] is True


# ── Test Cognitif ─────────────────────────────────────────────────────────────

class TestCognitiveScoring:
    def _make_cognitive_map(self):
        """3 items : logical (A), numerical (B), verbal (C)."""
        return {
            1: make_question(1, "logical", correct_answer="A"),
            2: make_question(2, "numerical", correct_answer="B"),
            3: make_question(3, "verbal", correct_answer="C"),
        }

    def test_toutes_bonnes_reponses(self):
        """3/3 correct → chaque trait = 100%."""
        q_map = self._make_cognitive_map()
        responses = [
            make_response(1, "A"),
            make_response(2, "B"),
            make_response(3, "C"),
        ]
        result = calculate_scores(responses, q_map, "cognitive", 1)
        assert result["traits"]["logical"]["score"] == 100.0
        assert result["traits"]["numerical"]["score"] == 100.0
        assert result["traits"]["verbal"]["score"] == 100.0

    def test_toutes_mauvaises_reponses(self):
        """0/3 correct → score = 0."""
        q_map = self._make_cognitive_map()
        responses = [
            make_response(1, "X"),
            make_response(2, "X"),
            make_response(3, "X"),
        ]
        result = calculate_scores(responses, q_map, "cognitive", 1)
        assert result["traits"]["logical"]["score"] == 0.0

    def test_case_insensitive(self):
        """La comparaison est insensible à la casse."""
        q_map = {1: make_question(1, "logical", correct_answer="A")}
        result = calculate_scores(
            [make_response(1, "a")], q_map, "cognitive", 1
        )
        assert result["traits"]["logical"]["score"] == 100.0

    def test_espaces_trim(self):
        """Les espaces autour de la valeur sont ignorés."""
        q_map = {1: make_question(1, "logical", correct_answer="B")}
        result = calculate_scores(
            [make_response(1, " B ")], q_map, "cognitive", 1
        )
        assert result["traits"]["logical"]["score"] == 100.0

    def test_global_score_cognitif(self):
        """2/3 bonnes → global_score = moyenne traits = ~66.7."""
        q_map = self._make_cognitive_map()
        responses = [
            make_response(1, "A"),   # correct
            make_response(2, "X"),   # incorrect
            make_response(3, "C"),   # correct
        ]
        result = calculate_scores(responses, q_map, "cognitive", 1)
        assert result["traits"]["logical"]["score"] == 100.0
        assert result["traits"]["numerical"]["score"] == 0.0
        assert result["traits"]["verbal"]["score"] == 100.0


# ── Fiabilité ─────────────────────────────────────────────────────────────────

class TestReliability:
    def test_fiabilite_nominale(self):
        """Réponses normales → is_reliable=True."""
        q_map = {i: make_question(i, "agreeableness") for i in range(1, 11)}
        responses = [make_response(i, 3, seconds_spent=8) for i in range(1, 11)]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["reliability"]["is_reliable"] is True
        assert result["reliability"]["reasons"] == []

    def test_reponses_trop_rapides(self):
        """
        avg_seconds_per_question < MIN_SECONDS_PER_QUESTION (2.0)
        → is_reliable=False avec raison "trop rapide".
        """
        q_map = {i: make_question(i, "agreeableness") for i in range(1, 6)}
        # 0.5s par question → suspect
        responses = [make_response(i, 3, seconds_spent=1) for i in range(1, 6)]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["reliability"]["is_reliable"] is False
        assert any("rapide" in r for r in result["reliability"]["reasons"])

    def test_biais_extremes(self):
        """
        Plus de 70% des réponses à l'extrême (1 ou 5 sur échelle 1-5)
        → is_reliable=False avec raison "désirabilité".
        """
        q_map = {i: make_question(i, "agreeableness") for i in range(1, 11)}
        # 8/10 réponses extrêmes = 80% > DESIRABILITY_EXTREME_THRESHOLD (70%)
        responses = (
            [make_response(i, 5, seconds_spent=10) for i in range(1, 9)]  # 8 extrêmes
            + [make_response(i, 3, seconds_spent=10) for i in range(9, 11)]  # 2 neutres
        )
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["reliability"]["is_reliable"] is False
        assert any("désirabilité" in r.lower() for r in result["reliability"]["reasons"])

    def test_biais_sous_seuil(self):
        """60% de réponses extrêmes → en-dessous du seuil de 70%, fiable."""
        q_map = {i: make_question(i, "agreeableness") for i in range(1, 11)}
        responses = (
            [make_response(i, 5, seconds_spent=10) for i in range(1, 7)]  # 6 extrêmes
            + [make_response(i, 3, seconds_spent=10) for i in range(7, 11)]  # 4 neutres
        )
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["reliability"]["is_reliable"] is True

    def test_meta_temps(self):
        """Les champs meta (total_time, avg) sont correctement calculés."""
        q_map = {i: make_question(i, "agreeableness") for i in range(1, 6)}
        responses = [make_response(i, 3, seconds_spent=10) for i in range(1, 6)]
        result = calculate_scores(responses, q_map, "likert", 5)
        assert result["meta"]["total_time_seconds"] == 50
        assert result["meta"]["avg_seconds_per_question"] == 10.0
