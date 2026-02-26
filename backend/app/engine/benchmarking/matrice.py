# engine/benchmarking/matrice.py
"""
Matrice de compatibilité psychologique pour le sociogramme frontend.

Concept UI :
    Le sociogramme affiche l'équipage comme une molécule 3D interactive.
    Chaque membre est un nœud — la distance, la couleur du lien, la taille
    et la couleur du nœud encodent les données MLPSM de façon visuelle.

    L'employeur peut drag & droper un candidat issu du DNRE dans la molécule
    pour voir en temps réel comment la dynamique évolue — avant d'embaucher.

Architecture des données produite ici :

    SociogramData
    ├── nodes[]          → un nœud par membre actif (+ candidat si drag)
    │   ├── id, label, role
    │   ├── size         ← influence sur l'équipe (rôle × ES score)
    │   ├── color        ← quadrant DNRE ou état ES (vert/orange/rouge)
    │   └── metrics      ← scores bruts pour le tooltip
    │
    ├── edges[]          → un lien par paire de membres
    │   ├── source, target
    │   ├── weight       ← compatibilité pairwise [0-1] (distance inverse)
    │   ├── color        ← nature du lien (synergie/neutre/friction)
    │   └── label        ← description de la relation dominant
    │
    ├── team_state       → métriques globales de l'équipe actuelle
    │   ├── f_team_score
    │   ├── cohesion, performance
    │   ├── matrix_diagnosis
    │   └── risk_flags[]
    │
    └── candidate_preview  → présent uniquement lors d'un drag & drop
        ├── dnre_result    ← G_fit, centile, safety
        ├── delta          ← FTeamDelta (avant/après)
        ├── nodes_delta[]  ← comment chaque nœud existant est affecté
        └── new_team_state ← métriques après intégration du candidat

Compatibilité pairwise :
    La distance entre deux nœuds est l'inverse de leur compatibilité.
    Deux membres très compatibles sont proches dans l'espace 3D.

    Compatibilité(i, j) = f(
        Δ_agreeableness  (similarité cohésive — valeurs proches = moins de friction),
        Δ_conscientiousness (faultline risk — divergence = friction),
        Δ_ES             (résilience collective — hauts profils rapprochent),
    )

    Note : on n'utilise pas la similarité complète Big Five — seulement les traits
    qui ont un effet prouvé sur la dynamique d'équipe (F_team, Hackman 2002).

Encodage visuel :
    Nœud size    : base 10 + bonus rôle (Captain > Officer > Crew)
                   + bonus ES (membres stables = plus influents visuellement)
    Nœud color   : GOOD_FIT (vert), HIGH_RISK (orange), DISQUALIFIED (rouge)
                   pour les candidats ; ES bucket pour les membres actifs
    Edge weight  : 1 - distance_pairwise (0 = friction max, 1 = synergie max)
    Edge color   : "#4CAF50" synergie (w>0.7), "#FFC107" neutre, "#F44336" friction (w<0.3)
    Edge width   : proportionnel au weight (plus épais = plus fort)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math

from app.engine.recruitment.MLPSM.f_team import (
    compute_baseline,
    compute_delta as f_team_compute_delta,
    FTeamResult,
    FTeamDelta,
)
from app.engine.benchmarking.diagnosis import (
    generate_matrix_diagnosis,
    generate_combined_diagnosis,
    MatrixDiagnosis,
)


# ── Constantes encodage visuel ────────────────────────────────────────────────

# Taille des nœuds par rôle (influence organisationnelle)
NODE_SIZE_BY_ROLE: Dict[str, float] = {
    "Captain":        28.0,
    "Chief Officer":  22.0,
    "Chief Engineer": 22.0,
    "First Officer":  18.0,
    "Engineer":       18.0,
    "Chef":           16.0,
    "Bosun":          15.0,
    "Deckhand":       12.0,
    "Steward":        12.0,
    "Stewardess":     12.0,
}
NODE_SIZE_DEFAULT = 12.0

# Couleur nœud membre actif selon bucket ES
NODE_COLOR_ES_HIGH    = "#4CAF50"   # ES >= 65 : vert — profil stable
NODE_COLOR_ES_MEDIUM  = "#FFC107"   # ES 40-65 : orange — vigilance
NODE_COLOR_ES_LOW     = "#F44336"   # ES < 40  : rouge — risque

# Couleur nœud candidat selon safety_level DNRE
NODE_COLOR_CANDIDATE_CLEAR      = "#2196F3"   # bleu — candidat qualifié
NODE_COLOR_CANDIDATE_HIGH_RISK  = "#FF9800"   # orange — HIGH_RISK
NODE_COLOR_CANDIDATE_DISQUALIFIED = "#9E9E9E"  # gris — DISQUALIFIED (fantôme)

# Couleur des liens selon compatibilité pairwise
EDGE_COLOR_SYNERGY  = "#4CAF50"    # weight > 0.7
EDGE_COLOR_NEUTRAL  = "#90CAF9"    # weight 0.3-0.7
EDGE_COLOR_FRICTION = "#EF9A9A"    # weight < 0.3

# Poids des dimensions dans la compatibilité pairwise (SKILL.md V1 : α > β)
# α — Similitude des valeurs (Conscientiousness) : dimension dominante
# β — Complémentarité sociale (Agréabilité additive)
# γ — Résilience collective (Stabilité émotionnelle additive)
W_COMPAT_CONSCIENTIOUSNESS = 0.55   # α : valeurs & standards partagés (dominant)
W_COMPAT_AGREEABLENESS     = 0.25   # β : f(A_i + A_j) — énergie sociale cumulative
W_COMPAT_ES                = 0.20   # γ : f(ES_i + ES_j) — buffer résilience collectif


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class NodeMetrics:
    """Métriques brutes d'un nœud (pour le tooltip frontend)."""
    agreeableness:       Optional[float]
    conscientiousness:   Optional[float]
    emotional_stability: Optional[float]
    gca:                 Optional[float]
    f_team_contribution: Optional[float] = None   # impact de ce membre sur F_team global


@dataclass
class SociogramNode:
    """
    Nœud du sociogramme — un membre actif de l'équipage.

    id             : crew_profile_id (int → string pour le frontend)
    label          : nom affiché (anonymisé si nécessaire)
    role           : YachtPosition string
    is_candidate   : False pour membres actifs, True pour le drag & drop
    size           : rayon du nœud dans l'espace 3D
    color          : couleur hexadécimale
    metrics        : données brutes pour le tooltip
    position_hint  : coordonnées 2D initiales suggérées par l'algorithme
                     (le frontend peut les ignorer et utiliser son propre layout)
    """
    id:            str
    label:         str
    role:          str
    is_candidate:  bool
    size:          float
    color:         str
    metrics:       NodeMetrics
    position_hint: Dict[str, float] = field(default_factory=dict)
    dnre_fit_label: Optional[str] = None  # "STRONG_FIT" etc. — candidats seulement


@dataclass
class SociogramEdge:
    """
    Lien entre deux nœuds — compatibilité pairwise.

    source, target : ids des nœuds
    weight         : compatibilité [0-1] (inverse de la distance psychologique)
    color          : encodage visuel selon weight
    width          : épaisseur du lien (proportionnel au weight, 1-4px)
    label          : description dominante de la relation
    dominant_factor: "agreeableness" | "conscientiousness" | "emotional_stability"
    is_candidate_edge : True si l'un des deux nœuds est un candidat drag & drop
    """
    source:              str
    target:              str
    weight:              float
    color:               str
    width:               float
    label:               str
    dominant_factor:     str
    is_candidate_edge:   bool = False


@dataclass
class TeamState:
    """État global de l'équipe pour l'affichage du panneau de synthèse."""
    f_team_score:     float
    performance:      float
    cohesion:         float
    crew_size:        int
    matrix_diagnosis: MatrixDiagnosis
    risk_flags:       List[str]
    tvi:              Optional[float] = None
    hcd:              Optional[float] = None


@dataclass
class NodeDelta:
    """
    Impact du candidat sur un membre existant spécifique.
    Permet d'animer les nœuds lors du drag & drop.
    """
    node_id:          str
    color_before:     str
    color_after:      str
    size_delta:       float       # 0 si inchangé
    edge_weight_delta: float      # variation de compatibilité sur ce nœud
    impact_label:     str         # "improved", "degraded", "neutral"


@dataclass
class CandidatePreview:
    """
    Données de prévisualisation lors du drag & drop d'un candidat DNRE.
    Calculées en temps réel par l'endpoint /sociogram/preview.
    """
    candidate_node:  SociogramNode
    candidate_edges: List[SociogramEdge]
    delta:           FTeamDelta
    nodes_delta:     List[NodeDelta]
    new_team_state:  TeamState
    all_flags:       List[str]


@dataclass
class SociogramData:
    """
    Données complètes du sociogramme.
    Retournées par GET /crew/{yacht_id}/sociogram.
    """
    yacht_id:          int
    nodes:             List[SociogramNode]
    edges:             List[SociogramEdge]
    team_state:        TeamState
    candidate_preview: Optional[CandidatePreview] = None


# ── Extraction des traits depuis le snapshot ──────────────────────────────────

def _get(snapshot: Dict, trait: str) -> Optional[float]:
    """Extrait un score depuis le snapshot — gère les deux formats."""
    if trait == "emotional_stability":
        val = snapshot.get("emotional_stability")
        if val is not None:
            return float(val)
        bf = snapshot.get("big_five") or {}
        n = bf.get("neuroticism")
        if n is None:
            return None
        n_score = n.get("score", n) if isinstance(n, dict) else n
        return 100.0 - float(n_score)

    if trait == "gca":
        return (snapshot.get("cognitive") or {}).get("gca_score")

    bf = snapshot.get("big_five") or {}
    val = bf.get(trait)
    if val is None:
        return None
    return float(val.get("score", val)) if isinstance(val, dict) else float(val)


# ── Compatibilité pairwise ────────────────────────────────────────────────────

def _pairwise_compatibility(snap_a: Dict, snap_b: Dict) -> tuple[float, str]:
    """
    Calcule la compatibilité [0-1] entre deux membres selon la formule SKILL.md V1 :
        D_ij = α·sim(C) + β·f(A_i+A_j) + γ·f(ES_i+ES_j)

    Logique :
        - Conscienciosité (α) : similarité — divergence des standards = faultline risk.
          Terme dominant (α=0.55) : les valeurs communes comptent le plus.
        - Agréabilité (β) : complémentarité additive f(A_i+A_j) — deux membres
          à haute agréabilité cumulent leur énergie sociale (pas de pénalité si
          l'un est bas et l'autre haut, contrairement à la similarité).
        - Stabilité émotionnelle (γ) : buffer collectif f(ES_i+ES_j) — la moyenne
          est plus réaliste que le produit (un profil fragile ne détruit plus la paire).

    Scores normalisés sur [0, 1] par construction.
    """
    a_a  = _get(snap_a, "agreeableness")       or 50.0
    c_a  = _get(snap_a, "conscientiousness")   or 50.0
    es_a = _get(snap_a, "emotional_stability") or 50.0

    a_b  = _get(snap_b, "agreeableness")       or 50.0
    c_b  = _get(snap_b, "conscientiousness")   or 50.0
    es_b = _get(snap_b, "emotional_stability") or 50.0

    # α — Similarité des valeurs : 1 - distance normalisée
    sim_c = 1.0 - abs(c_a - c_b) / 100.0

    # β — Complémentarité additive agréabilité : f(A_i + A_j) = moyenne normalisée
    #     Deux membres très agréables se renforcent mutuellement (énergie sociale cumulative).
    comp_a = (a_a + a_b) / 200.0

    # γ — Buffer résilience collective : f(ES_i + ES_j) = moyenne normalisée
    #     La moyenne est préférée au produit pour éviter de trop pénaliser une paire
    #     dont un seul membre est fragile.
    es_bond = (es_a + es_b) / 200.0

    score = (
        sim_c   * W_COMPAT_CONSCIENTIOUSNESS +
        comp_a  * W_COMPAT_AGREEABLENESS +
        es_bond * W_COMPAT_ES
    )
    score = round(max(0.0, min(1.0, score)), 3)

    # Facteur dominant — dimension contribuant le plus à la pénalité
    penalties = {
        "agreeableness":       1.0 - comp_a,
        "conscientiousness":   1.0 - sim_c,
        "emotional_stability": 1.0 - es_bond,
    }
    dominant = max(penalties, key=penalties.get)

    return score, dominant


def _edge_color(weight: float) -> str:
    if weight > 0.7:  return EDGE_COLOR_SYNERGY
    if weight < 0.3:  return EDGE_COLOR_FRICTION
    return EDGE_COLOR_NEUTRAL


def _edge_label(weight: float, dominant_factor: str) -> str:
    factor_labels = {
        "agreeableness":       "énergie sociale faible",
        "conscientiousness":   "divergence standards",
        "emotional_stability": "fragilité émotionnelle",
    }
    factor_label = factor_labels.get(dominant_factor, "compatibilité")
    if weight > 0.7:  return f"Synergie forte"
    if weight > 0.5:  return f"Compatibilité correcte"
    if weight > 0.3:  return f"Tension modérée ({factor_label})"
    return f"Friction élevée — {factor_label}"


# ── Construction des nœuds ────────────────────────────────────────────────────

def _build_node(
    crew_profile_id: str,
    name: str,
    role: str,
    snapshot: Dict,
    is_candidate: bool = False,
    dnre_fit_label: Optional[str] = None,
    safety_level: Optional[str] = None,
) -> SociogramNode:
    """Construit un SociogramNode depuis les métadonnées et le snapshot."""
    es = _get(snapshot, "emotional_stability") or 50.0
    a  = _get(snapshot, "agreeableness")
    c  = _get(snapshot, "conscientiousness")
    gca = _get(snapshot, "gca")

    # ── Taille ────────────────────────────────────────────────
    base_size = NODE_SIZE_BY_ROLE.get(role, NODE_SIZE_DEFAULT)
    es_bonus  = (es - 50.0) / 100.0 * 4.0   # ±4 selon ES
    size = round(base_size + es_bonus, 1)

    # ── Couleur ───────────────────────────────────────────────
    if is_candidate:
        level = (safety_level or "CLEAR").upper()
        if level == "DISQUALIFIED":
            color = NODE_COLOR_CANDIDATE_DISQUALIFIED
        elif level == "HIGH_RISK":
            color = NODE_COLOR_CANDIDATE_HIGH_RISK
        else:
            color = NODE_COLOR_CANDIDATE_CLEAR
    else:
        if es >= 65:   color = NODE_COLOR_ES_HIGH
        elif es >= 40: color = NODE_COLOR_ES_MEDIUM
        else:          color = NODE_COLOR_ES_LOW

    return SociogramNode(
        id=crew_profile_id,
        label=name,
        role=role,
        is_candidate=is_candidate,
        size=size,
        color=color,
        metrics=NodeMetrics(
            agreeableness=a,
            conscientiousness=c,
            emotional_stability=round(es, 1),
            gca=gca,
        ),
        dnre_fit_label=dnre_fit_label,
    )


# ── Position hints (layout circulaire initial) ────────────────────────────────

def _compute_position_hints(nodes: List[SociogramNode]) -> None:
    """
    Calcule des positions 2D initiales sur un cercle.
    Le frontend (Three.js / D3) peut les utiliser comme seed
    pour son propre algorithme force-directed.
    """
    n = len(nodes)
    if n == 0:
        return
    for i, node in enumerate(nodes):
        angle = (2 * math.pi * i) / n
        node.position_hint = {
            "x": round(math.cos(angle) * 100, 1),
            "y": round(math.sin(angle) * 100, 1),
            "z": 0.0,
        }


# ── Point d'entrée principal ──────────────────────────────────────────────────

def compute_sociogram(
    yacht_id: int,
    crew_members: List[Dict],
    weather: Optional[Dict] = None,
) -> SociogramData:
    """
    Calcule les données complètes du sociogramme pour un équipage.

    Args:
        yacht_id     : identifiant du yacht
        crew_members : liste de dicts avec :
            {
                "crew_profile_id": str,
                "name":            str,
                "role":            str,       # YachtPosition
                "snapshot":        Dict,      # psychometric_snapshot
            }
        weather      : dict du weather_trend (optionnel — pour TVI/HCD)

    Returns:
        SociogramData avec nodes, edges, team_state.
    """
    if not crew_members:
        return SociogramData(
            yacht_id=yacht_id,
            nodes=[],
            edges=[],
            team_state=TeamState(
                f_team_score=0.0, performance=0.0, cohesion=0.0,
                crew_size=0,
                matrix_diagnosis=generate_matrix_diagnosis(0.0, 0.0),
                risk_flags=["EMPTY_CREW"],
            ),
        )

    snapshots = [m.get("snapshot") or {} for m in crew_members]

    # ── Nœuds ─────────────────────────────────────────────────
    nodes = [
        _build_node(
            crew_profile_id=str(m["crew_profile_id"]),
            name=m.get("name", f"Membre {i+1}"),
            role=m.get("role", "Deckhand"),
            snapshot=m.get("snapshot") or {},
        )
        for i, m in enumerate(crew_members)
    ]
    _compute_position_hints(nodes)

    # ── Liens pairwise ────────────────────────────────────────
    edges: List[SociogramEdge] = []
    for i in range(len(crew_members)):
        for j in range(i + 1, len(crew_members)):
            weight, dominant = _pairwise_compatibility(snapshots[i], snapshots[j])
            edges.append(SociogramEdge(
                source=str(crew_members[i]["crew_profile_id"]),
                target=str(crew_members[j]["crew_profile_id"]),
                weight=weight,
                color=_edge_color(weight),
                width=round(1.0 + weight * 3.0, 1),   # 1px à 4px
                label=_edge_label(weight, dominant),
                dominant_factor=dominant,
            ))

    # ── État global de l'équipe ───────────────────────────────
    f_team = compute_baseline(snapshots)
    perf      = f_team.score
    min_a     = f_team.jerk_filter.min_agreeableness
    mean_es   = f_team.emotional.mean_emotional_stability
    cohesion  = round((min_a + mean_es) / 2.0, 1)

    matrix_dx = generate_matrix_diagnosis(perf, cohesion)

    # TVI/HCD si weather disponible
    tvi = hcd = None
    if weather:
        full_dx = generate_combined_diagnosis(
            harmony_metrics={
                "performance": perf,
                "cohesion": cohesion,
                "risk_factors": {
                    "conscientiousness_divergence": f_team.faultline.sigma_conscientiousness,
                    "weakest_link_stability": f_team.emotional.min_emotional_stability,
                }
            },
            weather=weather,
        )
        tvi = full_dx["volatility_index"]
        hcd = full_dx["hidden_conflict"]

    team_state = TeamState(
        f_team_score=f_team.score,
        performance=perf,
        cohesion=cohesion,
        crew_size=len(crew_members),
        matrix_diagnosis=matrix_dx,
        risk_flags=f_team.flags,
        tvi=tvi,
        hcd=hcd,
    )

    return SociogramData(
        yacht_id=yacht_id,
        nodes=nodes,
        edges=edges,
        team_state=team_state,
    )


# ── Preview candidat (drag & drop) ───────────────────────────────────────────

def compute_candidate_preview(
    base_sociogram: SociogramData,
    crew_snapshots: List[Dict],
    candidate: Dict,
) -> CandidatePreview:
    """
    Calcule l'impact d'un candidat drag & droppé sur le sociogramme existant.

    Appelé en temps réel depuis l'endpoint /sociogram/preview
    chaque fois qu'un candidat du pool DNRE est déplacé sur la molécule.

    Args:
        base_sociogram  : SociogramData déjà calculé (état actuel)
        crew_snapshots  : snapshots de l'équipage actuel (pour f_team_compute_delta)
        candidate : {
            "crew_profile_id": str,
            "name":            str,
            "role":            str,
            "snapshot":        Dict,
            "dnre_fit_label":  str,      # "STRONG_FIT" etc.
            "dnre_safety_level": str,    # "CLEAR" | "HIGH_RISK" | "DISQUALIFIED"
        }

    Returns:
        CandidatePreview avec :
        - candidate_node   : le nœud du candidat (à ajouter à la molécule)
        - candidate_edges  : les liens candidat ↔ chaque membre
        - delta            : FTeamDelta avant/après
        - nodes_delta      : impact sur chaque membre existant (animation)
        - new_team_state   : état après intégration
        - all_flags        : avertissements à afficher
    """
    snap_cand     = candidate.get("snapshot") or {}
    safety_level  = candidate.get("dnre_safety_level", "CLEAR")
    fit_label     = candidate.get("dnre_fit_label", "")
    flags: List[str] = []

    # ── Nœud candidat ─────────────────────────────────────────
    candidate_node = _build_node(
        crew_profile_id=str(candidate["crew_profile_id"]),
        name=candidate.get("name", "Candidat"),
        role=candidate.get("role", "Deckhand"),
        snapshot=snap_cand,
        is_candidate=True,
        dnre_fit_label=fit_label,
        safety_level=safety_level,
    )
    candidate_node.position_hint = {"x": 0.0, "y": 150.0, "z": 0.0}

    if safety_level == "DISQUALIFIED":
        flags.append("DISQUALIFIED: candidat non qualifié — prévisualisation fantôme uniquement")

    # ── Liens candidat ↔ membres ──────────────────────────────
    candidate_edges: List[SociogramEdge] = []
    for node in base_sociogram.nodes:
        member_snap = next(
            (m.get("snapshot") or {} for m in (
                [{"crew_profile_id": n.id, "snapshot": {}} for n in base_sociogram.nodes]
            ) if str(m.get("crew_profile_id")) == node.id),
            {},
        )
        weight, dominant = _pairwise_compatibility(snap_cand, member_snap)
        candidate_edges.append(SociogramEdge(
            source=str(candidate["crew_profile_id"]),
            target=node.id,
            weight=weight,
            color=_edge_color(weight),
            width=round(1.0 + weight * 3.0, 1),
            label=_edge_label(weight, dominant),
            dominant_factor=dominant,
            is_candidate_edge=True,
        ))

    # ── Delta F_team ──────────────────────────────────────────
    f_team_after = f_team_compute_delta(crew_snapshots, snap_cand)
    delta        = f_team_after.delta

    if delta:
        if delta.net_impact == "NEGATIVE":
            flags.append(f"TEAM_NEGATIVE_IMPACT: F_team {delta.delta:+.1f}")
        elif delta.net_impact == "POSITIVE":
            flags.append(f"TEAM_POSITIVE_IMPACT: F_team {delta.delta:+.1f}")

    # ── Nodes delta (animation par membre) ───────────────────
    nodes_delta: List[NodeDelta] = []
    for node in base_sociogram.nodes:
        edge_to_cand = next(
            (e for e in candidate_edges if e.target == node.id), None
        )
        ew_delta = (edge_to_cand.weight - 0.5) if edge_to_cand else 0.0

        # Couleur change si ES du candidat modifie le buffer collectif
        mean_es_after = f_team_after.emotional.mean_emotional_stability
        es_bucket_before = node.color
        # Recolor seulement les nœuds ES marginaux (proche du seuil)
        node_es = node.metrics.emotional_stability or 50.0
        if mean_es_after < 40 and node_es < 55:
            color_after = NODE_COLOR_ES_LOW
        elif mean_es_after < 50 and node_es < 65:
            color_after = NODE_COLOR_ES_MEDIUM
        else:
            color_after = node.color

        impact_label = (
            "improved" if ew_delta > 0.1
            else "degraded" if ew_delta < -0.1
            else "neutral"
        )

        nodes_delta.append(NodeDelta(
            node_id=node.id,
            color_before=es_bucket_before,
            color_after=color_after,
            size_delta=0.0,
            edge_weight_delta=round(ew_delta, 3),
            impact_label=impact_label,
        ))

    # ── Nouvel état équipe ────────────────────────────────────
    new_perf     = f_team_after.score
    new_min_a    = f_team_after.jerk_filter.min_agreeableness
    new_mean_es  = f_team_after.emotional.mean_emotional_stability
    new_cohesion = round((new_min_a + new_mean_es) / 2.0, 1)

    new_team_state = TeamState(
        f_team_score=new_perf,
        performance=new_perf,
        cohesion=new_cohesion,
        crew_size=base_sociogram.team_state.crew_size + 1,
        matrix_diagnosis=generate_matrix_diagnosis(new_perf, new_cohesion),
        risk_flags=f_team_after.flags,
    )

    return CandidatePreview(
        candidate_node=candidate_node,
        candidate_edges=candidate_edges,
        delta=delta,
        nodes_delta=nodes_delta,
        new_team_state=new_team_state,
        all_flags=flags,
    )