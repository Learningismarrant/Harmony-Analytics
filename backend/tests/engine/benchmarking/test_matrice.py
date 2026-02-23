# tests/engine/benchmarking/test_matrice.py
"""
Tests unitaires pour engine.benchmarking.matrice

Couverture :
    compute_sociogram() :
        - Équipage vide → SociogramData avec nodes/edges vides
        - N membres → N nœuds, N*(N-1)/2 liens pairwise
        - Chaque nœud a position_hint (x, y, z)
        - Chaque lien a source, target, weight [0-1], color, label
        - team_state.f_team_score ≥ 0
        - Avec weather → tvi/hcd calculés
        - Sans weather → tvi/hcd = None

    compute_candidate_preview() :
        - Retourne CandidatePreview
        - candidate_node est présent
        - candidate_edges = N (un par membre existant)
        - nodes_delta = N (un par membre)
        - new_team_state.crew_size = base_crew_size + 1

    _pairwise_compatibility() :
        - Snapshots identiques → score proche de 1
        - Snapshots opposés → score faible
        - Score dans [0, 1]

    Encodage visuel :
        - Edge color SYNERGY si weight > 0.7
        - Edge color FRICTION si weight < 0.3
        - Node color ES_HIGH si ES ≥ 65
"""
import math
import pytest

from app.engine.benchmarking.matrice import (
    compute_sociogram,
    compute_candidate_preview,
    SociogramData,
    SociogramNode,
    SociogramEdge,
    CandidatePreview,
    TeamState,
    _pairwise_compatibility,
    _edge_color,
    EDGE_COLOR_SYNERGY,
    EDGE_COLOR_NEUTRAL,
    EDGE_COLOR_FRICTION,
    NODE_COLOR_ES_HIGH,
    NODE_COLOR_ES_MEDIUM,
    NODE_COLOR_ES_LOW,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snap(
    agreeableness: float = 70.0,
    conscientiousness: float = 70.0,
    neuroticism: float = 35.0,
) -> dict:
    return {
        "big_five": {
            "agreeableness":      agreeableness,
            "conscientiousness":  conscientiousness,
            "neuroticism":        neuroticism,
            "emotional_stability": round(100.0 - neuroticism, 1),
        },
        "cognitive": {"gca_score": 70.0},
    }


def _member(crew_id: str, name: str = "Marin", role: str = "Deckhand", snap: dict | None = None) -> dict:
    return {
        "crew_profile_id": crew_id,
        "name":            name,
        "role":            role,
        "snapshot":        snap or _snap(),
    }


def _weather(average: float = 4.0, std: float = 0.5, days: int = 7, count: int = 7) -> dict:
    return {
        "average":         average,
        "std":             std,
        "days_observed":   days,
        "response_count":  count,
        "status":          "stable",
    }


THREE_MEMBERS = [
    _member("1", "Alice",   "Captain",  _snap(agreeableness=80)),
    _member("2", "Bob",     "Deckhand", _snap(agreeableness=75)),
    _member("3", "Charlie", "Bosun",    _snap(agreeableness=70)),
]


# ── compute_sociogram() ───────────────────────────────────────────────────────

class TestComputeSociogram:
    def test_retourne_sociogram_data(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert isinstance(result, SociogramData)

    def test_equipe_vide(self):
        result = compute_sociogram(yacht_id=1, crew_members=[])
        assert result.nodes == []
        assert result.edges == []
        assert result.team_state.crew_size == 0

    def test_n_membres_n_noeuds(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert len(result.nodes) == 3

    def test_n_liens_pairwise(self):
        """N membres → N*(N-1)/2 liens."""
        n = len(THREE_MEMBERS)
        expected_edges = n * (n - 1) // 2
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert len(result.edges) == expected_edges

    def test_noeuds_ont_position_hint(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        for node in result.nodes:
            assert "x" in node.position_hint
            assert "y" in node.position_hint
            assert "z" in node.position_hint

    def test_liens_ont_champs_obligatoires(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        for edge in result.edges:
            assert isinstance(edge.source, str)
            assert isinstance(edge.target, str)
            assert 0.0 <= edge.weight <= 1.0
            assert isinstance(edge.color, str)
            assert isinstance(edge.label, str)

    def test_liens_sources_targets_valides(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        node_ids = {n.id for n in result.nodes}
        for edge in result.edges:
            assert edge.source in node_ids
            assert edge.target in node_ids

    def test_team_state_f_team_score_borne(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert 0.0 <= result.team_state.f_team_score <= 100.0

    def test_team_state_crew_size_correct(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert result.team_state.crew_size == 3

    def test_sans_weather_tvi_hcd_none(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS, weather=None)
        assert result.team_state.tvi is None
        assert result.team_state.hcd is None

    def test_avec_weather_tvi_hcd_calcules(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS, weather=_weather())
        assert result.team_state.tvi is not None
        assert result.team_state.hcd is not None
        assert 0.0 <= result.team_state.tvi <= 100.0
        assert 0.0 <= result.team_state.hcd <= 100.0

    def test_matrix_diagnosis_present(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert result.team_state.matrix_diagnosis is not None

    def test_risk_flags_liste(self):
        result = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        assert isinstance(result.team_state.risk_flags, list)

    def test_un_seul_membre(self):
        """Avec 1 seul membre → 0 lien (pas de paire possible)."""
        result = compute_sociogram(yacht_id=1, crew_members=[THREE_MEMBERS[0]])
        assert len(result.nodes) == 1
        assert len(result.edges) == 0

    def test_yacht_id_transmis(self):
        result = compute_sociogram(yacht_id=42, crew_members=THREE_MEMBERS)
        assert result.yacht_id == 42


# ── compute_candidate_preview() ───────────────────────────────────────────────

class TestComputeCandidatePreview:
    def setup_method(self):
        self.base_sociogram = compute_sociogram(yacht_id=1, crew_members=THREE_MEMBERS)
        self.crew_snaps     = [m["snapshot"] for m in THREE_MEMBERS]
        self.candidate = {
            "crew_profile_id":   "cand_99",
            "name":              "Nouveau Marin",
            "role":              "Deckhand",
            "snapshot":          _snap(agreeableness=75),
            "dnre_fit_label":    "GOOD_FIT",
            "dnre_safety_level": "CLEAR",
        }
        self.preview = compute_candidate_preview(
            base_sociogram=self.base_sociogram,
            crew_snapshots=self.crew_snaps,
            candidate=self.candidate,
        )

    def test_retourne_candidate_preview(self):
        assert isinstance(self.preview, CandidatePreview)

    def test_candidate_node_present(self):
        assert self.preview.candidate_node is not None
        assert isinstance(self.preview.candidate_node, SociogramNode)

    def test_candidate_node_id(self):
        assert self.preview.candidate_node.id == "cand_99"

    def test_candidate_edges_un_par_membre(self):
        """Un lien candidat ↔ chaque membre existant."""
        assert len(self.preview.candidate_edges) == len(THREE_MEMBERS)

    def test_candidate_edges_is_candidate_edge(self):
        for edge in self.preview.candidate_edges:
            assert edge.is_candidate_edge is True

    def test_nodes_delta_un_par_membre(self):
        assert len(self.preview.nodes_delta) == len(THREE_MEMBERS)

    def test_new_team_state_crew_size(self):
        """Après intégration candidat → crew_size + 1."""
        assert self.preview.new_team_state.crew_size == len(THREE_MEMBERS) + 1

    def test_all_flags_liste(self):
        assert isinstance(self.preview.all_flags, list)

    def test_delta_present(self):
        """FTeamDelta doit être renseigné."""
        assert self.preview.delta is not None


# ── _pairwise_compatibility() ─────────────────────────────────────────────────

class TestPairwiseCompatibility:
    def test_score_dans_bornes(self):
        score, _ = _pairwise_compatibility(_snap(), _snap())
        assert 0.0 <= score <= 1.0

    def test_snapshots_identiques_score_eleve(self):
        """Deux profils identiques → compatibilité maximale."""
        snap = _snap(agreeableness=70, conscientiousness=70, neuroticism=35)
        score, _ = _pairwise_compatibility(snap, snap)
        assert score > 0.7

    def test_snapshots_opposes_score_bas(self):
        """Agréabilité max vs min → friction élevée."""
        snap_high = _snap(agreeableness=100, conscientiousness=100)
        snap_low  = _snap(agreeableness=0,   conscientiousness=0)
        score, _ = _pairwise_compatibility(snap_high, snap_low)
        assert score < 0.5

    def test_retourne_tuple_score_factor(self):
        result = _pairwise_compatibility(_snap(), _snap())
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_dominant_factor_valide(self):
        _, dominant = _pairwise_compatibility(_snap(), _snap())
        assert dominant in ("agreeableness", "conscientiousness", "emotional_stability")


# ── Encodage visuel ───────────────────────────────────────────────────────────

class TestEncodageVisuel:
    def test_edge_color_synergy(self):
        assert _edge_color(0.8) == EDGE_COLOR_SYNERGY

    def test_edge_color_neutral(self):
        assert _edge_color(0.5) == EDGE_COLOR_NEUTRAL

    def test_edge_color_friction(self):
        assert _edge_color(0.2) == EDGE_COLOR_FRICTION

    def test_edge_color_boundary_synergy(self):
        """Exactement 0.7 → pas synergy (> 0.7 requis)."""
        assert _edge_color(0.7) == EDGE_COLOR_NEUTRAL

    def test_edge_color_boundary_friction(self):
        """Exactement 0.3 → pas friction (< 0.3 requis)."""
        assert _edge_color(0.3) == EDGE_COLOR_NEUTRAL
