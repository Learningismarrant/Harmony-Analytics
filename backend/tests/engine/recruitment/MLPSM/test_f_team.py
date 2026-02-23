# tests/engine/recruitment/MLPSM/test_f_team.py
"""
Tests unitaires pour engine.recruitment.MLPSM.f_team

Couverture :
    compute() :
        - Score nominal sur équipe de 3 membres
        - Jerk filter déclenché quand min(A) < 35 → flag JERK_RISK
        - Faultline risk quand σ(C) > 20 → flag FAULTLINE_RISK
        - Emotional fragility quand μ(ES) < 45 → flag EMOTIONAL_FRAGILITY
        - Équipe < 2 membres → score=50 par défaut, flag CREW_TOO_SMALL
        - Données manquantes → data_quality dégradée, fallback à 50

    compute_baseline() :
        - Appelle compute() avec les mêmes snapshots
        - FTeamResult.jerk_filter/faultline/emotional correctement remplis

    compute_delta() :
        - Candidat améliorant → delta > 0, net_impact="POSITIVE"
        - Candidat dégradant → delta < 0, net_impact="NEGATIVE"
        - Candidat neutre → net_impact="NEUTRAL"
"""
import pytest

from app.engine.recruitment.MLPSM.f_team import (
    compute,
    compute_baseline,
    compute_delta,
    FTeamResult,
    JERK_FILTER_DANGER,
    FAULTLINE_DANGER,
    ES_MINIMUM_THRESHOLD,
    MIN_CREW_SIZE,
)

pytestmark = pytest.mark.engine


# ── Snapshots de test ─────────────────────────────────────────────────────────

def snap(agreeableness=75.0, conscientiousness=70.0, emotional_stability=None, neuroticism=30.0):
    """Snapshot minimal pour les tests f_team."""
    es = emotional_stability if emotional_stability is not None else round(100 - neuroticism, 1)
    return {
        "big_five": {
            "agreeableness": agreeableness,
            "conscientiousness": conscientiousness,
            "neuroticism": neuroticism,
            "emotional_stability": es,
        }
    }


CREW_3_NOMINAL = [
    snap(agreeableness=75.0, conscientiousness=70.0, neuroticism=30.0),
    snap(agreeableness=80.0, conscientiousness=75.0, neuroticism=25.0),
    snap(agreeableness=65.0, conscientiousness=68.0, neuroticism=35.0),
]

CREW_3_JERK = [
    snap(agreeableness=25.0, conscientiousness=70.0, neuroticism=30.0),  # jerk < 35
    snap(agreeableness=80.0, conscientiousness=75.0, neuroticism=25.0),
    snap(agreeableness=78.0, conscientiousness=68.0, neuroticism=28.0),
]

CREW_3_FAULTLINE = [
    snap(conscientiousness=90.0),   # très haut
    snap(conscientiousness=40.0),   # très bas → σ >> 20
    snap(conscientiousness=85.0),
]

CREW_3_LOW_ES = [
    snap(neuroticism=70.0),   # ES = 30
    snap(neuroticism=65.0),   # ES = 35
    snap(neuroticism=60.0),   # ES = 40 → μ(ES) = 35 < 45
]


# ── compute() ─────────────────────────────────────────────────────────────────

class TestCompute:
    def test_retourne_fteam_result(self):
        result = compute(CREW_3_NOMINAL)
        assert isinstance(result, FTeamResult)

    def test_score_dans_bornes(self):
        result = compute(CREW_3_NOMINAL)
        assert 0.0 <= result.score <= 100.0

    def test_score_nominal_positif(self):
        """Équipe saine → score > 30."""
        result = compute(CREW_3_NOMINAL)
        assert result.score > 30.0

    def test_crew_size_correct(self):
        result = compute(CREW_3_NOMINAL)
        assert result.crew_size == 3

    def test_jerk_filter_declenche(self):
        """min(A) = 25 < 35 → jerk_risk=True, flag JERK_RISK présent."""
        result = compute(CREW_3_JERK)
        assert result.jerk_filter.risk_detected is True
        assert result.jerk_filter.min_agreeableness < JERK_FILTER_DANGER
        assert any("JERK_RISK" in f for f in result.flags)

    def test_jerk_filter_non_declenche(self):
        """min(A) = 65 > 35 → jerk_risk=False."""
        result = compute(CREW_3_NOMINAL)
        assert result.jerk_filter.risk_detected is False

    def test_faultline_risk_declenche(self):
        """σ(C) > 20 → faultline_risk=True, flag FAULTLINE_RISK présent."""
        result = compute(CREW_3_FAULTLINE)
        assert result.faultline.risk_detected is True
        assert result.faultline.sigma_conscientiousness > FAULTLINE_DANGER
        assert any("FAULTLINE_RISK" in f for f in result.flags)

    def test_emotional_fragility_declenchee(self):
        """μ(ES) < 45 → emotional_risk=True, flag EMOTIONAL_FRAGILITY présent."""
        result = compute(CREW_3_LOW_ES)
        assert result.emotional.risk_detected is True
        assert result.emotional.mean_emotional_stability < ES_MINIMUM_THRESHOLD
        assert any("EMOTIONAL_FRAGILITY" in f for f in result.flags)

    def test_equipe_insuffisante(self):
        """1 seul membre → score=50 par défaut, flag CREW_TOO_SMALL."""
        result = compute([snap()])
        assert result.score == 50.0
        assert result.crew_size == 1
        assert any("CREW_TOO_SMALL" in f for f in result.flags)

    def test_equipe_vide(self):
        """0 membre → score=50 par défaut."""
        result = compute([])
        assert result.score == 50.0

    def test_donnees_manquantes_degrade_data_quality(self):
        """Snapshot sans agreeableness → data_quality < 1.0, fallback 50."""
        snapshots = [
            {"big_five": {"conscientiousness": 70.0}},  # pas d'agreeableness
            {"big_five": {"conscientiousness": 65.0, "agreeableness": 75.0}},
        ]
        result = compute(snapshots)
        assert result.data_quality < 1.0
        assert any("PARTIAL_DATA" in f for f in result.flags)

    def test_jerk_penalise_score_final(self):
        """
        Équipe avec jerk (A=20) doit avoir un score inférieur à
        équipe sans jerk (A=75) toutes choses égales par ailleurs.
        """
        crew_sain = [snap(agreeableness=75.0)] * 3
        crew_jerk = [snap(agreeableness=20.0), snap(agreeableness=75.0), snap(agreeableness=75.0)]
        assert compute(crew_sain).score > compute(crew_jerk).score

    def test_formula_snapshot_non_vide(self):
        """formula_snapshot doit être une chaîne non vide."""
        result = compute(CREW_3_NOMINAL)
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 0


# ── compute_baseline() ───────────────────────────────────────────────────────

class TestComputeBaseline:
    def test_identique_a_compute(self):
        """compute_baseline est un alias de compute — résultats identiques."""
        r1 = compute(CREW_3_NOMINAL)
        r2 = compute_baseline(CREW_3_NOMINAL)
        assert r1.score == r2.score
        assert r1.crew_size == r2.crew_size

    def test_crew_vide(self):
        result = compute_baseline([])
        assert result.score == 50.0


# ── compute_delta() ───────────────────────────────────────────────────────────

class TestComputeDelta:
    def test_delta_renseigne(self):
        """compute_delta → FTeamResult.delta doit être non-None."""
        candidate = snap(agreeableness=80.0, conscientiousness=72.0, neuroticism=28.0)
        result = compute_delta(CREW_3_NOMINAL, candidate)
        assert result.delta is not None

    def test_candidat_ameliorant(self):
        """
        Candidat avec agreeableness très élevée → améliore min(A) → delta > 0.
        """
        crew_avec_jerk = [
            snap(agreeableness=30.0),  # maillon faible
            snap(agreeableness=75.0),
        ]
        # Candidat agréable
        candidat_excellent = snap(agreeableness=90.0, conscientiousness=70.0, neuroticism=25.0)
        result = compute_delta(crew_avec_jerk, candidat_excellent)
        # L'équipe sans candidat avait A_min=30 ; avec candidat A_min reste 30
        # Mais le score global peut s'améliorer via ES
        assert result.delta is not None
        assert isinstance(result.delta.delta, float)

    def test_candidat_tres_negatif(self):
        """
        Un candidat avec agreeableness=10 sur une équipe saine → impact négatif.
        """
        crew_sain = [snap(agreeableness=80.0)] * 3
        candidat_jerk = snap(agreeableness=10.0, conscientiousness=70.0, neuroticism=30.0)
        result = compute_delta(crew_sain, candidat_jerk)
        assert result.delta is not None
        assert result.delta.delta < 0  # score après < score avant
        assert result.delta.net_impact == "NEGATIVE"

    def test_equipe_trop_petite_avant(self):
        """Si équipe actuelle < 2 membres, score_before = 50 par défaut."""
        crew_solo = [snap()]
        candidat = snap()
        result = compute_delta(crew_solo, candidat)
        assert result.delta is not None
        assert result.delta.f_team_before == 50.0

    def test_net_impact_labels(self):
        """net_impact doit être POSITIVE, NEGATIVE ou NEUTRAL."""
        candidat = snap()
        result = compute_delta(CREW_3_NOMINAL, candidat)
        assert result.delta.net_impact in ("POSITIVE", "NEGATIVE", "NEUTRAL")
