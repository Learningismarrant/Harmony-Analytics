# tests/engine/recruitment/pe_fit/test_profiles_matrix.py
"""
Tests unitaires pour pj_fit/profiles.py — lookup matriciel (position × yacht_type)

Couverture :
    Fallback vers profil générique quand yacht_type=None
    Fallback quand (position, yacht_type) absent de la matrice
    Patch appliqué correctement (traits patchés overrident la base)
    Traits non patchés conservent la valeur base
    Scores dans [0, 100] pour chaque profil matriciel
    amotivation = 0 dans les profils patchés
    _deep_merge() ne mute pas le profil base
    Cas limites : position inconnue + yacht_type, case-insensitive
    Non-régression : get_ideal_profile(position) sans yacht_type inchangé
"""
import copy
import pytest

from app.engine.pe_fit.pj_fit.profiles import (
    SME_MATRIX_PATCHES,
    _MATRIX_NORM,
    _deep_merge,
    get_ideal_profile,
    JOB_PROFILES_NORM,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

MATRIX_ENTRIES = list(SME_MATRIX_PATCHES.items())


# ── Tests _deep_merge ─────────────────────────────────────────────────────────

class TestDeepMerge:
    def test_patch_overrides_trait(self):
        base = {"personality": {"extraversion": 75, "conscientiousness": 95}}
        patch = {"personality": {"extraversion": 55}}
        result = _deep_merge(base, patch)
        assert result["personality"]["extraversion"] == 55
        assert result["personality"]["conscientiousness"] == 95

    def test_base_unchanged(self):
        base = {"personality": {"extraversion": 75}}
        original = copy.deepcopy(base)
        _deep_merge(base, {"personality": {"extraversion": 55}})
        assert base == original

    def test_patch_adds_new_category(self):
        base = {"personality": {"conscientiousness": 90}}
        patch = {"cognitive": {"logical": 80}}
        result = _deep_merge(base, patch)
        assert "cognitive" in result
        assert result["personality"]["conscientiousness"] == 90

    def test_empty_patch_returns_copy(self):
        base = {"personality": {"extraversion": 70}}
        result = _deep_merge(base, {})
        assert result == base

    def test_empty_base_returns_patch(self):
        patch = {"personality": {"extraversion": 70}}
        result = _deep_merge({}, patch)
        assert result == patch


# ── Tests fallback ────────────────────────────────────────────────────────────

class TestFallback:
    def test_sans_yacht_type_retourne_generique(self):
        generic = get_ideal_profile("Captain")
        assert generic is not None
        assert generic["personality"]["conscientiousness"] == 95  # valeur base

    def test_yacht_type_none_explicite(self):
        result = get_ideal_profile("Captain", yacht_type=None)
        generic = JOB_PROFILES_NORM["captain"]
        assert result is generic  # même objet, pas de merge

    def test_yacht_type_absent_de_matrice_retourne_generique(self):
        """sailing_cruiser n'a pas de patch Captain → fallback."""
        result = get_ideal_profile("Captain", yacht_type="sailing_cruiser")
        generic = JOB_PROFILES_NORM["captain"]
        assert result is generic

    def test_position_inconnue_retourne_none(self):
        assert get_ideal_profile("UnknownPosition") is None

    def test_position_inconnue_avec_yacht_type_retourne_none(self):
        assert get_ideal_profile("UnknownPosition", yacht_type="megayacht") is None


# ── Tests patches individuels ─────────────────────────────────────────────────

class TestCaptainSailingRacing:
    def test_profil_existe(self):
        result = get_ideal_profile("Captain", yacht_type="sailing_racing")
        assert result is not None

    def test_extraversion_reduite(self):
        """Course → moins d'interface client → extraversion ↓"""
        generic = get_ideal_profile("Captain")
        specific = get_ideal_profile("Captain", yacht_type="sailing_racing")
        assert specific["personality"]["extraversion"] < generic["personality"]["extraversion"]
        assert specific["personality"]["extraversion"] == 55

    def test_intrinsic_augmente(self):
        specific = get_ideal_profile("Captain", yacht_type="sailing_racing")
        assert specific["motivation"]["intrinsic"] == 98

    def test_logical_augmente(self):
        specific = get_ideal_profile("Captain", yacht_type="sailing_racing")
        assert specific["cognitive"]["logical"] == 95

    def test_traits_non_patches_conserves(self):
        """agreeableness n'est pas dans le patch → valeur base conservée."""
        generic = get_ideal_profile("Captain")
        specific = get_ideal_profile("Captain", yacht_type="sailing_racing")
        assert specific["personality"]["agreeableness"] == generic["personality"]["agreeableness"]


class TestCaptainExpedition:
    def test_openness_eleve(self):
        specific = get_ideal_profile("Captain", yacht_type="expedition")
        assert specific["personality"]["openness"] == 92

    def test_neuroticism_tres_bas(self):
        specific = get_ideal_profile("Captain", yacht_type="expedition")
        assert specific["personality"]["neuroticism"] == 12

    def test_identified_eleve(self):
        specific = get_ideal_profile("Captain", yacht_type="expedition")
        assert specific["motivation"]["identified"] == 92


class TestCaptainMegayacht:
    def test_extraversion_augmente(self):
        """Mégayacht → interaction UHNWI → extraversion ↑"""
        generic = get_ideal_profile("Captain")
        specific = get_ideal_profile("Captain", yacht_type="megayacht")
        assert specific["personality"]["extraversion"] > generic["personality"]["extraversion"]
        assert specific["personality"]["extraversion"] == 82

    def test_verbal_eleve(self):
        specific = get_ideal_profile("Captain", yacht_type="megayacht")
        assert specific["cognitive"]["verbal"] == 92

    def test_extrinsic_material_augmente(self):
        specific = get_ideal_profile("Captain", yacht_type="megayacht")
        assert specific["motivation"]["extrinsic_material"] == 70


class TestChefCharter:
    def test_neuroticism_augmente(self):
        """Charter → rotation constante → tolérance au stress sollicitée."""
        generic = get_ideal_profile("Chef")
        specific = get_ideal_profile("Chef", yacht_type="charter")
        assert specific["personality"]["neuroticism"] > generic["personality"]["neuroticism"]
        assert specific["personality"]["neuroticism"] == 45

    def test_extraversion_augmente(self):
        specific = get_ideal_profile("Chef", yacht_type="charter")
        assert specific["personality"]["extraversion"] == 62

    def test_extrinsic_material_augmente(self):
        specific = get_ideal_profile("Chef", yacht_type="charter")
        assert specific["motivation"]["extrinsic_material"] == 72


class TestChefMegayacht:
    def test_conscientiousness_augmente(self):
        generic = get_ideal_profile("Chef")
        specific = get_ideal_profile("Chef", yacht_type="megayacht")
        assert specific["personality"]["conscientiousness"] > generic["personality"]["conscientiousness"]

    def test_openness_maximal(self):
        specific = get_ideal_profile("Chef", yacht_type="megayacht")
        assert specific["personality"]["openness"] == 98


class TestChiefStewardessCharter:
    def test_extraversion_augmente(self):
        generic = get_ideal_profile("Chief Stewardess")
        specific = get_ideal_profile("Chief Stewardess", yacht_type="charter")
        assert specific["personality"]["extraversion"] > generic["personality"]["extraversion"]

    def test_neuroticism_augmente_mais_reste_bas(self):
        specific = get_ideal_profile("Chief Stewardess", yacht_type="charter")
        assert specific["personality"]["neuroticism"] == 28
        assert specific["personality"]["neuroticism"] < 40  # reste acceptable


class TestChiefStewardesssMegayacht:
    def test_conscientiousness_quasi_maximal(self):
        specific = get_ideal_profile("Chief Stewardess", yacht_type="megayacht")
        assert specific["personality"]["conscientiousness"] == 98

    def test_extrinsic_social_augmente(self):
        specific = get_ideal_profile("Chief Stewardess", yacht_type="megayacht")
        assert specific["motivation"]["extrinsic_social"] == 95


class TestChiefEngineerExpedition:
    def test_conscientiousness_maximal(self):
        specific = get_ideal_profile("Chief Engineer", yacht_type="expedition")
        assert specific["personality"]["conscientiousness"] == 99

    def test_numerical_augmente(self):
        specific = get_ideal_profile("Chief Engineer", yacht_type="expedition")
        assert specific["cognitive"]["numerical"] == 98


# ── Tests de cohérence globale ────────────────────────────────────────────────

class TestCoherenceGlobale:
    @pytest.mark.parametrize("key,patch", MATRIX_ENTRIES)
    def test_scores_dans_bornes(self, key, patch):
        pos, yt = key
        result = get_ideal_profile(pos, yacht_type=yt)
        assert result is not None
        for category, traits in result.items():
            for trait, score in traits.items():
                assert 0 <= score <= 100, (
                    f"({pos}, {yt}).{category}.{trait} = {score} hors bornes [0, 100]"
                )

    @pytest.mark.parametrize("key,patch", MATRIX_ENTRIES)
    def test_amotivation_nulle_ou_absente(self, key, patch):
        pos, yt = key
        result = get_ideal_profile(pos, yacht_type=yt)
        amot = result.get("motivation", {}).get("amotivation")
        if amot is not None:
            assert amot == 0, f"({pos}, {yt}) amotivation doit être 0, got {amot}"

    def test_case_insensitive_position(self):
        a = get_ideal_profile("captain", yacht_type="megayacht")
        b = get_ideal_profile("CAPTAIN", yacht_type="megayacht")
        assert a == b

    def test_case_insensitive_yacht_type(self):
        a = get_ideal_profile("Captain", yacht_type="megayacht")
        b = get_ideal_profile("Captain", yacht_type="MEGAYACHT")
        assert a == b

    def test_matrix_norm_contient_toutes_les_cles(self):
        for (pos, yt) in SME_MATRIX_PATCHES:
            assert (pos, yt) in _MATRIX_NORM

    def test_non_regression_sans_yacht_type(self):
        """get_ideal_profile(pos) sans yacht_type doit rester identique."""
        for position in ["Captain", "Chef", "Chief Stewardess", "Chief Engineer"]:
            base = JOB_PROFILES_NORM[position.lower()]
            result = get_ideal_profile(position)
            assert result is base, (
                f"get_ideal_profile('{position}') sans yacht_type "
                f"doit retourner l'objet base — pas un merge"
            )
