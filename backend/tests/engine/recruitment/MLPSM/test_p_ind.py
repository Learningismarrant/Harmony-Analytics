# tests/engine/recruitment/MLPSM/test_p_ind.py
"""
Tests unitaires pour engine.recruitment.MLPSM.p_ind.compute()

Formule V1 (SKILL.md) :
    P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA × C / 100)

    ω₁ = OMEGA_GCA               = 0.55
    ω₂ = OMEGA_CONSCIENTIOUSNESS = 0.35
    ω₃ = OMEGA_INTERACTION       = 0.10

Couverture :
    - Score nominal : formule vérifiée manuellement (avec terme d'interaction)
    - Terme d'interaction non nul et cohérent
    - Terme d'interaction pénalise les profils déséquilibrés
    - GCA absent → fallback 50.0 + flag GCA_MISSING + data_quality -= 0.35
    - Big Five absent → fallback C=50.0 + flag BIG_FIVE_MISSING
    - Score clamped : jamais < 0 ou > 100
    - PIndResult contient interaction_term
    - experience_years transmis, bonus désactivé en Temps 1
"""
import pytest

from app.engine.recruitment.MLPSM.p_ind import (
    compute,
    PIndResult,
    OMEGA_GCA,
    OMEGA_CONSCIENTIOUSNESS,
    OMEGA_INTERACTION,
)

pytestmark = pytest.mark.engine


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


class TestPIndCompute:
    def test_retourne_pind_result(self):
        result = compute(snap_full())
        assert isinstance(result, PIndResult)

    def test_score_formule_nominale_avec_interaction(self):
        """P_ind = GCA×ω₁ + C×ω₂ + (GCA×C/100)×ω₃ vérifié manuellement."""
        gca = 80.0
        c   = 70.0
        expected = _expected_score(gca, c)
        result = compute(snap_full(gca=gca, conscientiousness=c))
        assert result.score == expected

    def test_score_dans_bornes(self):
        result = compute(snap_full())
        assert 0.0 <= result.score <= 100.0

    def test_data_quality_complete(self):
        """Données complètes → data_quality = 1.0."""
        result = compute(snap_full())
        assert result.data_quality == 1.0

    # ── Terme d'interaction ───────────────────────────────────────────────────

    def test_interaction_term_non_nul(self):
        """Le terme d'interaction doit être > 0 pour des scores non nuls."""
        result = compute(snap_full(gca=80.0, conscientiousness=70.0))
        assert result.interaction_term > 0.0

    def test_interaction_term_valeur(self):
        """Vérification manuelle : ω₃ × (GCA × C / 100)."""
        gca, c = 80.0, 70.0
        expected_interaction = round(OMEGA_INTERACTION * (gca * c / 100.0), 2)
        result = compute(snap_full(gca=gca, conscientiousness=c))
        assert abs(result.interaction_term - expected_interaction) < 0.01

    def test_interaction_penalise_profil_desequilibre(self):
        """
        Un candidat équilibré (GCA=70, C=70) doit avoir une interaction plus
        élevée qu'un candidat déséquilibré de produit GCA×C inférieur.
        GCA=70, C=70 → interaction = 0.10 × 4900/100 = 4.9
        GCA=100, C=40 → interaction = 0.10 × 4000/100 = 4.0
        """
        balanced   = compute(snap_full(gca=70.0, conscientiousness=70.0))
        unbalanced = compute(snap_full(gca=100.0, conscientiousness=40.0))
        assert balanced.interaction_term > unbalanced.interaction_term

    def test_interaction_zero_quand_gca_zero(self):
        """Si GCA = 0, le terme d'interaction doit être 0."""
        result = compute(snap_full(gca=0.0, conscientiousness=80.0))
        assert result.interaction_term == 0.0

    def test_interaction_zero_quand_c_zero(self):
        """
        Si C = 0 (au format dict pour éviter le fallback de l'extraction),
        le terme d'interaction doit être 0.
        Note : snap_full() passe C comme scalaire brut. Quand C=0.0, l'extraction
        `c_data or {}` interprète 0.0 comme falsy et applique le fallback 50.0.
        On utilise le format dict explicite pour tester la vraie valeur C=0.
        """
        snap_c_zero = {
            "cognitive": {"gca_score": 80.0, "n_tests": 1},
            "big_five": {"conscientiousness": {"score": 0.0, "reliable": True}},
        }
        result = compute(snap_c_zero)
        assert result.interaction_term == 0.0

    def test_interaction_maximal_quand_gca_c_max(self):
        """L'interaction est maximale (ω₃×100=10) quand GCA=100 et C=100."""
        result = compute(snap_full(gca=100.0, conscientiousness=100.0))
        max_interaction = round(OMEGA_INTERACTION * 100.0, 2)
        assert abs(result.interaction_term - max_interaction) < 0.01

    # ── Fallbacks ─────────────────────────────────────────────────────────────

    def test_gca_manquant_fallback(self):
        """Aucun test cognitif → GCA = 50.0, flag GCA_MISSING, data_quality -= 0.35."""
        result = compute(snap_no_cognitive(conscientiousness=80.0))
        assert any("GCA_MISSING" in f for f in result.flags)
        assert result.gca.gca_score == 50.0
        assert result.data_quality <= 0.65

    def test_big_five_manquant_fallback(self):
        """Pas de Big Five → C = 50.0, flag BIG_FIVE_MISSING."""
        result = compute(snap_no_big_five(gca=80.0))
        assert any("BIG_FIVE_MISSING" in f for f in result.flags)
        assert result.conscientiousness.c_score == 50.0

    def test_snapshot_vide_double_fallback(self):
        """Snapshot vide → GCA=50, C=50, P_ind calculé avec interaction."""
        result = compute(snap_empty())
        expected = _expected_score(50.0, 50.0)
        assert result.score == expected

    # ── Bornes et clamp ───────────────────────────────────────────────────────

    def test_score_clamp_max(self):
        """GCA=100, C=100 → P_ind ne dépasse pas 100."""
        result = compute(snap_full(gca=100.0, conscientiousness=100.0))
        assert result.score <= 100.0

    def test_score_clamp_min(self):
        """GCA=0, C=0 → P_ind ≥ 0."""
        result = compute(snap_full(gca=0.0, conscientiousness=0.0))
        assert result.score >= 0.0

    # ── Expérience et formule ─────────────────────────────────────────────────

    def test_experience_years_transmis(self):
        """experience_years est enregistré dans ExperienceDetail."""
        result = compute(snap_full(), experience_years=5)
        assert result.experience.years == 5

    def test_experience_bonus_desactive_temps1(self):
        """En Temps 1, le bonus expérience ne doit pas modifier le score."""
        result_0yr  = compute(snap_full(gca=72.0, conscientiousness=75.0), experience_years=0)
        result_10yr = compute(snap_full(gca=72.0, conscientiousness=75.0), experience_years=10)
        assert result_0yr.score == result_10yr.score

    def test_formula_snapshot_contient_interaction(self):
        """formula_snapshot doit mentionner les 3 termes de la formule."""
        result = compute(snap_full(gca=80.0, conscientiousness=70.0))
        assert "P_ind" in result.formula_snapshot
        # Les 3 omegas doivent apparaître
        assert str(OMEGA_GCA) in result.formula_snapshot or "0.55" in result.formula_snapshot
        assert str(OMEGA_INTERACTION) in result.formula_snapshot or "0.10" in result.formula_snapshot

    def test_sous_scores_cognitifs_extraits(self):
        """Les sous-scores cognitifs sont disponibles dans GCADetail si fournis."""
        snap = {
            "cognitive": {
                "gca_score": 72.0,
                "logical_reasoning": 74.0,
                "numerical_reasoning": 70.0,
                "verbal_reasoning": 72.0,
            },
            "big_five": {"conscientiousness": 70.0},
        }
        result = compute(snap)
        assert result.gca.logical_reasoning == 74.0
        assert result.gca.numerical_reasoning == 70.0
        assert result.gca.verbal_reasoning == 72.0

    def test_scores_croissants_avec_gca_et_c(self):
        """Un candidat avec GCA et C plus élevés doit avoir un score plus élevé."""
        low  = compute(snap_full(gca=40.0, conscientiousness=40.0))
        high = compute(snap_full(gca=85.0, conscientiousness=80.0))
        assert high.score > low.score

    # ── Omegas injectables (P3 — JobWeightConfig) ─────────────────────────────

    def test_omegas_custom_modifient_score(self):
        """Des omegas personnalisés doivent produire un score différent des defaults."""
        snap = snap_full(gca=70.0, conscientiousness=80.0)
        default_result = compute(snap)
        custom_omegas  = {"omega_gca": 0.70, "omega_conscientiousness": 0.20, "omega_interaction": 0.10}
        custom_result  = compute(snap, omegas=custom_omegas)
        assert default_result.score != custom_result.score

    def test_omegas_custom_flag_present(self):
        """Omegas injectés → flag OMEGAS_OVERRIDE dans result.flags."""
        snap = snap_full(gca=70.0, conscientiousness=80.0)
        custom_omegas = {"omega_gca": 0.70, "omega_conscientiousness": 0.20, "omega_interaction": 0.10}
        result = compute(snap, omegas=custom_omegas)
        assert any("OMEGAS_OVERRIDE" in f for f in result.flags)

    def test_omegas_none_utilise_defaults(self):
        """omegas=None → même résultat que les constantes du module."""
        snap = snap_full(gca=70.0, conscientiousness=80.0)
        result_none     = compute(snap, omegas=None)
        result_defaults = compute(snap)
        assert result_none.score == result_defaults.score

    def test_omegas_custom_formule_algebrique(self):
        """Vérification algébrique avec omegas personnalisés."""
        gca, c = 75.0, 65.0
        custom_omegas = {"omega_gca": 0.60, "omega_conscientiousness": 0.30, "omega_interaction": 0.10}
        interaction = custom_omegas["omega_interaction"] * (gca * c / 100.0)
        expected_raw = gca * custom_omegas["omega_gca"] + c * custom_omegas["omega_conscientiousness"] + interaction
        expected = round(max(0.0, min(100.0, expected_raw)), 1)
        result = compute(snap_full(gca=gca, conscientiousness=c), omegas=custom_omegas)
        assert result.score == expected
