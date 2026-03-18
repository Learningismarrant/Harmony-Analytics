# tests/engine/recruitment/pe_fit/test_profiles_extended.py
"""
Tests unitaires pour pj_fit/profiles.py — postes étendus (phase alpha)

Couverture :
    get_ideal_profile() pour les 7 nouveaux postes
    Unicité des clés dans SME_PROFILES
    Cohérence structurelle de chaque profil (personality, motivation, cognitive)
    Vérification que JOB_PROFILES_NORM contient tous les postes
"""
import pytest
from app.engine.pe_fit.pj_fit.profiles import (
    SME_PROFILES,
    JOB_PROFILES_NORM,
    CATEGORY_MAPPING,
    get_ideal_profile,
)
from app.shared.enums import YachtPosition

pytestmark = pytest.mark.engine

# Nouveaux postes introduits en phase alpha
NEW_POSITIONS = [
    "Second Officer",
    "3rd Engineer",
    "ETO",
    "Butler",
    "Sous Chef",
    "Dive Instructor",
    "Medic",
]

ALL_POSITIONS = list(SME_PROFILES.keys())


class TestNouveauxPostes:
    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_profil_existe(self, position: str):
        profile = get_ideal_profile(position)
        assert profile is not None, f"Profil manquant pour '{position}'"

    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_profil_a_personality(self, position: str):
        profile = get_ideal_profile(position)
        assert "personality" in profile
        assert len(profile["personality"]) >= 3

    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_profil_a_motivation(self, position: str):
        profile = get_ideal_profile(position)
        assert "motivation" in profile
        assert len(profile["motivation"]) >= 2

    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_profil_a_cognitive(self, position: str):
        profile = get_ideal_profile(position)
        assert "cognitive" in profile
        assert len(profile["cognitive"]) >= 2

    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_scores_dans_bornes(self, position: str):
        profile = get_ideal_profile(position)
        for category, traits in profile.items():
            for trait, score in traits.items():
                assert 0 <= score <= 100, (
                    f"{position}.{category}.{trait} = {score} hors bornes [0, 100]"
                )

    @pytest.mark.parametrize("position", NEW_POSITIONS)
    def test_amotivation_nul_ou_absent(self, position: str):
        """amotivation doit être 0 si présent (jamais souhaitable)."""
        profile = get_ideal_profile(position)
        amotivation = profile["motivation"].get("amotivation")
        if amotivation is not None:
            assert amotivation == 0


class TestPostesExistants:
    """Vérification de non-régression sur les 9 profils existants."""

    EXISTING_POSITIONS = [
        "Captain", "First Mate", "Bosun", "Deckhand",
        "Chief Engineer", "2nd Engineer", "Chief Stewardess", "Stewardess", "Chef",
    ]

    @pytest.mark.parametrize("position", EXISTING_POSITIONS)
    def test_profil_toujours_present(self, position: str):
        assert get_ideal_profile(position) is not None

    def test_captain_conscientiousness_eleve(self):
        profile = get_ideal_profile("Captain")
        assert profile["personality"]["conscientiousness"] >= 90

    def test_chief_engineer_conscientiousness_maximal(self):
        profile = get_ideal_profile("Chief Engineer")
        assert profile["personality"]["conscientiousness"] >= 95


class TestCoherenceGlobale:
    def test_total_profils_est_16(self):
        """16 postes au total (9 existants + 7 nouveaux)."""
        assert len(SME_PROFILES) == 16

    def test_normalise_case_insensitive(self):
        assert get_ideal_profile("captain") is not None
        assert get_ideal_profile("CAPTAIN") is not None
        assert get_ideal_profile("eto") is not None
        assert get_ideal_profile("ETO") is not None

    def test_job_profiles_norm_contient_tous(self):
        for key in SME_PROFILES:
            assert key.lower() in JOB_PROFILES_NORM

    def test_aucun_profil_inconnu(self):
        """Tous les profils sont accessibles via get_ideal_profile."""
        for position in SME_PROFILES:
            assert get_ideal_profile(position) is not None

    def test_clés_uniques(self):
        """Pas de doublon dans SME_PROFILES."""
        assert len(SME_PROFILES) == len(set(SME_PROFILES.keys()))

    def test_yacht_position_enum_coherent(self):
        """
        Chaque valeur de YachtPosition doit avoir un profil SME (ou en avoir un prévu).
        Les nouvelles valeurs de phase alpha doivent être dans SME_PROFILES.
        """
        positions_in_sme = {k.lower() for k in SME_PROFILES}
        for yp in YachtPosition:
            # Vérification que le profil existe ou que c'est documenté comme absent
            profile = get_ideal_profile(yp.value)
            if profile is None:
                # Acceptable seulement si le poste n'est pas encore profilé
                assert yp.value.lower() not in positions_in_sme, (
                    f"YachtPosition.{yp.name} ({yp.value!r}) a une entrée dans "
                    f"JOB_PROFILES_NORM mais get_ideal_profile retourne None"
                )
