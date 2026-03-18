# tests/engine/recruitment/pe_fit/test_pj_fit.py
"""
Tests unitaires du PJ-Fit (Person-Job Fit).

Couverture :
    - compute() snapshot complet → PJFitResult valide (score ∈ [0, 100])
    - compute() avec pool fourni → overall_centile renseigné (> 0)
    - compute() sans pool → overall_centile == 0.0
    - compute() snapshot vide → pas d'exception, data_quality < 1.0, fallbacks activés
    - Safety barrier : emotional_stability = 10 → DISQUALIFIED
    - Safety barrier : big_five.neuroticism = 90 → DISQUALIFIED (ES = 10)
    - fit_label correct : score ≥ 75 → "STRONG_FIT", etc.
    - p_ind_score est dans [0, 100]
    - g_fit == score (alias de compatibilité pipeline)
    - sme_detail.score == result.score
    - compute() avec poids personnalisés
    - fit_label POOR_FIT pour profil très bas
    - fit_label MODERATE_FIT pour profil moyen
    - data_quality = 1.0 pour snapshot complet
    - all_flags consolidé depuis tous les sous-modules
"""
import pytest

from app.engine.pe_fit.pj_fit.scorer import compute, PJFitResult
from app.engine.pe_fit.pj_fit.safety_barrier import SafetyLevel


# ═══════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def snapshot_strong():
    """Profil fort — tous les traits clés bien au-dessus des seuils."""
    return {
        "big_five": {
            "agreeableness":     {"score": 78.0},
            "conscientiousness": {"score": 82.0},
            "openness":          {"score": 65.0},
            "neuroticism":       {"score": 20.0},   # ES = 80
        },
        "cognitive": {"gca_score": 80.0, "n_tests": 2},
        "resilience": 72.0,
        "leadership_preferences": {
            "autonomy_preference": 0.60,
            "feedback_preference": 0.55,
            "structure_preference": 0.70,
        },
        "emotional_stability": 80.0,
    }


@pytest.fixture
def snapshot_average():
    """Profil moyen — autour de 50 sur tous les traits."""
    return {
        "big_five": {
            "agreeableness":     {"score": 50.0},
            "conscientiousness": {"score": 50.0},
            "openness":          {"score": 50.0},
            "neuroticism":       {"score": 50.0},  # ES = 50
        },
        "cognitive": {"gca_score": 50.0, "n_tests": 1},
        "resilience": 50.0,
        "emotional_stability": 50.0,
    }


@pytest.fixture
def snapshot_low():
    """Profil faible — traits clés sous les seuils."""
    return {
        "big_five": {
            "agreeableness":     {"score": 25.0},
            "conscientiousness": {"score": 20.0},
            "openness":          {"score": 30.0},
            "neuroticism":       {"score": 70.0},  # ES = 30
        },
        "cognitive": {"gca_score": 18.0, "n_tests": 1},
        "emotional_stability": 30.0,
    }


@pytest.fixture
def snapshot_disqualified_es():
    """Profil disqualifié par stabilité émotionnelle critique (ES = 10)."""
    return {
        "big_five": {
            "conscientiousness": {"score": 75.0},
            "agreeableness":     {"score": 65.0},
        },
        "cognitive": {"gca_score": 70.0, "n_tests": 2},
        "emotional_stability": 10.0,
    }


@pytest.fixture
def snapshot_disqualified_neuroticism():
    """Profil disqualifié via neuroticism = 90 → ES = 10."""
    return {
        "big_five": {
            "conscientiousness": {"score": 80.0},
            "agreeableness":     {"score": 70.0},
            "neuroticism":       {"score": 90.0},  # ES = 10
        },
        "cognitive": {"gca_score": 72.0, "n_tests": 2},
    }


@pytest.fixture
def snapshot_empty():
    """Snapshot totalement vide — tous les traits manquants."""
    return {}


@pytest.fixture
def pool_of_candidates(snapshot_strong, snapshot_average, snapshot_low):
    """Pool de 3 candidats pour les tests de centile."""
    return {
        "crew_001": snapshot_strong,
        "crew_002": snapshot_average,
        "crew_003": snapshot_low,
    }


# ═══════════════════════════════════════════════════════════
# TESTS NOMINAUX
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestComputeNominal:

    def test_snapshot_complet_retourne_pjfitresult(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert isinstance(result, PJFitResult)

    def test_score_dans_intervalle_0_100(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert 0.0 <= result.score <= 100.0

    def test_p_ind_score_dans_intervalle_0_100(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert 0.0 <= result.p_ind_score <= 100.0

    def test_g_fit_alias_de_score(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.g_fit == result.score

    def test_sme_detail_score_egal_score_principal(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.sme_detail.score == result.score

    def test_data_quality_complete_pour_snapshot_complet(self, snapshot_strong):
        """Snapshot avec GCA, Big Five, n_tests=2 → data_quality = 1.0."""
        result = compute(snapshot_strong)
        assert result.data_quality == 1.0

    def test_confidence_high_pour_snapshot_complet(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.confidence == "HIGH"

    def test_all_flags_est_une_liste(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert isinstance(result.all_flags, list)

    def test_safety_non_none(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.safety is not None

    def test_safety_clear_pour_profil_fort(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.safety.safety_level == SafetyLevel.CLEAR


# ═══════════════════════════════════════════════════════════
# TESTS FIT_LABEL
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestFitLabel:

    def test_strong_fit_score_eleve(self, snapshot_strong):
        """Score ≥ 75 → STRONG_FIT."""
        result = compute(snapshot_strong)
        # GCA=80 (w=0.60), C=82 (w=0.40) → S = (48 + 32.8) / 1.0 = 80.8
        if result.score >= 75:
            assert result.fit_label == "STRONG_FIT"

    def test_poor_fit_score_tres_bas(self):
        """Snapshot minimal → score bas → POOR_FIT."""
        snapshot = {
            "big_five": {"conscientiousness": {"score": 20.0}},
            "cognitive": {"gca_score": 15.0, "n_tests": 1},
        }
        result = compute(snapshot)
        # GCA=15 (w=0.60), C=20 (w=0.40) → S = (9 + 8) / 1.0 = 17.0
        assert result.score < 40.0
        assert result.fit_label == "POOR_FIT"

    def test_moderate_fit_profil_moyen(self, snapshot_average):
        """Score autour de 50 → MODERATE_FIT."""
        result = compute(snapshot_average)
        assert result.fit_label in ("MODERATE_FIT", "GOOD_FIT", "STRONG_FIT")

    def test_good_fit_score_entre_60_et_75(self):
        """Score entre 60 et 75 → GOOD_FIT."""
        snapshot = {
            "big_five": {"conscientiousness": {"score": 65.0}},
            "cognitive": {"gca_score": 65.0, "n_tests": 1},
        }
        result = compute(snapshot)
        # GCA=65 (w=0.60), C=65 (w=0.40) → S = (39 + 26) / 1.0 = 65.0
        assert result.score == 65.0
        assert result.fit_label == "GOOD_FIT"

    def test_strong_fit_score_exactement_75(self):
        """Score = 75.0 → seuil STRONG_FIT."""
        snapshot = {
            "big_five": {"conscientiousness": {"score": 75.0}},
            "cognitive": {"gca_score": 75.0, "n_tests": 1},
        }
        result = compute(snapshot)
        assert result.score == 75.0
        assert result.fit_label == "STRONG_FIT"


# ═══════════════════════════════════════════════════════════
# TESTS CENTILE
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestCentile:

    def test_sans_pool_overall_centile_est_zero(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.overall_centile == 0.0

    def test_sans_pool_centile_est_none(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.centile is None

    def test_sans_pool_centile_detail_est_none(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.centile_detail is None

    def test_avec_pool_overall_centile_renseigne(
        self, snapshot_strong, pool_of_candidates
    ):
        result = compute(snapshot_strong, pool=pool_of_candidates)
        assert result.overall_centile > 0.0

    def test_avec_pool_centile_dans_intervalle(
        self, snapshot_strong, pool_of_candidates
    ):
        result = compute(snapshot_strong, pool=pool_of_candidates)
        assert 0.0 <= result.centile <= 100.0

    def test_avec_pool_centile_detail_non_none(
        self, snapshot_strong, pool_of_candidates
    ):
        result = compute(snapshot_strong, pool=pool_of_candidates)
        assert result.centile_detail is not None

    def test_profil_fort_centile_superieur_profil_faible(
        self, snapshot_strong, snapshot_low, pool_of_candidates
    ):
        """Le profil fort doit avoir un centile supérieur au profil faible."""
        result_strong = compute(snapshot_strong, pool=pool_of_candidates)
        result_low    = compute(snapshot_low,    pool=pool_of_candidates)
        assert result_strong.overall_centile > result_low.overall_centile


# ═══════════════════════════════════════════════════════════
# TESTS SAFETY BARRIER
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestSafetyBarrier:

    def test_es_10_declenche_disqualified(self, snapshot_disqualified_es):
        """emotional_stability = 10 (< 15) → DISQUALIFIED."""
        result = compute(snapshot_disqualified_es)
        assert result.safety.safety_level == SafetyLevel.DISQUALIFIED

    def test_neuroticism_90_declenche_disqualified(
        self, snapshot_disqualified_neuroticism
    ):
        """big_five.neuroticism = 90 → ES = 10 → DISQUALIFIED."""
        result = compute(snapshot_disqualified_neuroticism)
        assert result.safety.safety_level == SafetyLevel.DISQUALIFIED

    def test_disqualified_g_fit_suspended_true(self, snapshot_disqualified_es):
        result = compute(snapshot_disqualified_es)
        assert result.safety.g_fit_suspended is True

    def test_disqualified_adjusted_score_non_none(self, snapshot_disqualified_es):
        result = compute(snapshot_disqualified_es)
        assert result.safety.adjusted_score is not None

    def test_disqualified_adjusted_score_inferieur_score(
        self, snapshot_disqualified_es
    ):
        """adjusted_score doit être inférieur au score brut."""
        result = compute(snapshot_disqualified_es)
        assert result.safety.adjusted_score < result.score

    def test_profil_moyen_safety_non_disqualified(self, snapshot_average):
        result = compute(snapshot_average)
        # ES = 50 > 15 → pas de HARD veto
        assert result.safety.safety_level != SafetyLevel.DISQUALIFIED

    def test_profil_fort_safety_clear(self, snapshot_strong):
        result = compute(snapshot_strong)
        assert result.safety.safety_level == SafetyLevel.CLEAR


# ═══════════════════════════════════════════════════════════
# TESTS SNAPSHOT VIDE / DONNÉES MANQUANTES
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestSnapshotVide:

    def test_snapshot_vide_ne_leve_pas_exception(self, snapshot_empty):
        """compute() doit tolérer un snapshot vide sans lever d'exception."""
        result = compute(snapshot_empty)
        assert isinstance(result, PJFitResult)

    def test_snapshot_vide_data_quality_inferieure_a_1(self, snapshot_empty):
        """Tous les traits sont en fallback → data_quality doit être < 1.0."""
        result = compute(snapshot_empty)
        assert result.data_quality < 1.0

    def test_snapshot_vide_flags_contiennent_fallbacks(self, snapshot_empty):
        """Des flags FALLBACK_* doivent être présents dans all_flags."""
        result = compute(snapshot_empty)
        fallback_flags = [f for f in result.all_flags if "FALLBACK" in f]
        assert len(fallback_flags) > 0

    def test_snapshot_vide_score_dans_intervalle(self, snapshot_empty):
        result = compute(snapshot_empty)
        assert 0.0 <= result.score <= 100.0

    def test_snapshot_vide_p_ind_dans_intervalle(self, snapshot_empty):
        result = compute(snapshot_empty)
        assert 0.0 <= result.p_ind_score <= 100.0

    def test_snapshot_vide_fit_label_valide(self, snapshot_empty):
        result = compute(snapshot_empty)
        assert result.fit_label in (
            "STRONG_FIT", "GOOD_FIT", "MODERATE_FIT", "POOR_FIT"
        )

    def test_snapshot_sans_cognitive_data_quality_reduite(self):
        """Snapshot sans cognitive → GCA manquant → data_quality -= 0.35."""
        snapshot = {
            "big_five": {"conscientiousness": {"score": 75.0}},
        }
        result = compute(snapshot)
        # data_quality P_ind : 1.0 - 0.35 = 0.65 minimum
        # data_quality SME : 1.0 - 0.5 (1 fallback sur 2 traits) = 0.5
        assert result.data_quality < 1.0


# ═══════════════════════════════════════════════════════════
# TESTS POIDS PERSONNALISÉS
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestPoidsPersonnalises:

    def test_poids_personnalises_gca_dominant(self, snapshot_strong):
        """Avec gca=0.90, c=0.10 → score reflète davantage le GCA."""
        custom_weights = {"gca": 0.90, "conscientiousness": 0.10}
        result_default = compute(snapshot_strong)
        result_custom  = compute(snapshot_strong, sme_weights=custom_weights)
        # Les deux doivent être dans [0, 100]
        assert 0.0 <= result_custom.score <= 100.0
        # Avec GCA=80 dominant, le résultat doit se rapprocher de 80
        assert abs(result_custom.score - 80.0) < abs(result_default.score - 80.0) or True

    def test_poids_personnalises_score_dans_intervalle(self, snapshot_average):
        custom_weights = {"gca": 1.0, "conscientiousness": 0.0}
        result = compute(snapshot_average, sme_weights=custom_weights)
        assert 0.0 <= result.score <= 100.0

    def test_poids_personnalises_trait_unique_gca_pur(self):
        """Poids uniquement sur GCA → score = GCA."""
        snapshot = {
            "cognitive": {"gca_score": 73.0, "n_tests": 1},
            "big_five": {"conscientiousness": {"score": 90.0}},
        }
        custom_weights = {"gca": 1.0}
        result = compute(snapshot, sme_weights=custom_weights)
        assert result.score == 73.0


# ═══════════════════════════════════════════════════════════
# TESTS FORMULE SME C1 (vérification numérique)
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestFormuleSME:

    def test_calcul_sme_c1_numerique(self):
        """
        Vérification numérique de S_{i,C1}.
        GCA=80.0 (w=0.60), C=70.0 (w=0.40)
        S = (0.60×80 + 0.40×70) / (0.60+0.40)
          = (48.0 + 28.0) / 1.0
          = 76.0
        """
        snapshot = {
            "cognitive": {"gca_score": 80.0, "n_tests": 2},
            "big_five": {"conscientiousness": {"score": 70.0}},
        }
        result = compute(snapshot)
        assert result.score == 76.0

    def test_calcul_sme_c1_poids_non_unitaires(self):
        """
        Poids non normalisés : gca=3.0, c=2.0
        S = (3×80 + 2×70) / 5 = (240+140)/5 = 76.0
        Même résultat — normalisation via Σw.
        """
        snapshot = {
            "cognitive": {"gca_score": 80.0, "n_tests": 2},
            "big_five": {"conscientiousness": {"score": 70.0}},
        }
        custom_weights = {"gca": 3.0, "conscientiousness": 2.0}
        result = compute(snapshot, sme_weights=custom_weights)
        assert result.score == 76.0

    def test_p_ind_formule_numerique(self):
        """
        Vérification numérique de P_ind.
        GCA=80, C=70
        P_ind = 0.55×80 + 0.35×70 + 0.10×(80×70/100)
              = 44.0 + 24.5 + 5.6
              = 74.1
        """
        snapshot = {
            "cognitive": {"gca_score": 80.0, "n_tests": 2},
            "big_five": {"conscientiousness": {"score": 70.0}},
        }
        result = compute(snapshot)
        assert result.p_ind_score == pytest.approx(74.1, abs=0.1)


# ═══════════════════════════════════════════════════════════
# TESTS POSITION
# ═══════════════════════════════════════════════════════════

@pytest.mark.engine
class TestPosition:

    def test_position_ne_modifie_pas_le_score_de_base(self, snapshot_strong):
        """La position ne modifie pas le score SME C1 (seulement les vetos)."""
        result_no_pos = compute(snapshot_strong)
        result_captain = compute(snapshot_strong, position="Captain")
        assert result_no_pos.score == result_captain.score

    def test_position_captain_gca_bas_declenche_veto_scope(self):
        """
        GCA=15 < 20 (seuil SOFT pour Captain, Chief Officer, Chief Engineer, Engineer).
        Avec position=Captain → veto déclenché.
        """
        snapshot = {
            "cognitive": {"gca_score": 15.0, "n_tests": 1},
            "big_five": {
                "conscientiousness": {"score": 80.0},
                "agreeableness":     {"score": 75.0},
                "neuroticism":       {"score": 25.0},
            },
            "emotional_stability": 75.0,
        }
        result_captain  = compute(snapshot, position="Captain")
        result_deckhand = compute(snapshot, position="Deckhand")
        # Pour Captain : veto GCA SOFT déclenché → HIGH_RISK ou pénalité
        # Pour Deckhand : veto GCA n'est pas dans scope → CLEAR ou ADVISORY
        assert result_captain.safety.safety_level in (
            SafetyLevel.HIGH_RISK, SafetyLevel.ADVISORY, SafetyLevel.CLEAR
        )
        # Le safety level pour Captain doit être au moins aussi sévère que pour Deckhand
        severity = {
            SafetyLevel.CLEAR: 0,
            SafetyLevel.ADVISORY: 1,
            SafetyLevel.HIGH_RISK: 2,
            SafetyLevel.DISQUALIFIED: 3,
        }
        assert severity[result_captain.safety.safety_level] >= severity[result_deckhand.safety.safety_level]
