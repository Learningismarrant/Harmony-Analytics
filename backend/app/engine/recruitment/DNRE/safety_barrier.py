# engine/recruitment/dnre/safety_barrier.py
"""
Barrière de Sécurité Psychométrique — Modèle Non-Compensatoire

Le DNRE applique une Règle de Veto sur les traits critiques :

    Si x_{i,t} < Seuil_{critique}
        → G_fit marqué "High Risk"
        → Agrégation compensatoire suspendue pour cette dimension

Justification :
    Un modèle purement compensatoire laisse passer des profils dangereux.
    Ex : un candidat avec GCA = 90 et Emotional_Stability = 15 obtiendrait
    un G_fit correct malgré une instabilité émotionnelle sévère — inadmissible
    en environnement maritime isolé.

    La logique non-compensatoire interrompt cette compensation pour les traits
    qui conditionnent la SÉCURITÉ (psychologique ou physique) de l'équipage.

Architecture des vetos :
    HARD VETO (blocage total) :
        G_fit = 0.0, candidat marqué DISQUALIFIED.
        Reserved pour traits de sécurité absolus (ex: ES < 15 = risque crise).

    SOFT VETO (flag High Risk, pas de blocage) :
        G_fit calculé normalement mais annoté HIGH_RISK.
        L'employeur est alerté et peut décider en connaissance de cause.
        Reserved pour traits importants mais pas critiques de sécurité.

    ADVISORY (avertissement sans impact sur le score) :
        Flag ADVISORY ajouté mais calcul inchangé.
        Pour signaler des sous-performances contextuelles.

Seuils par défaut (SME-consensuels, Phase 0) :
    Peuvent être surchargés par poste (Capitaine > Deckhand) ou contexte.

Sources :
    Hogan, R. & Hogan, J. (2001). Assessing leadership: a view from the
    dark side. International Journal of Selection and Assessment.
    (Traits "dark triad" — veto absolu dans contextes isolés)

    Sandal, G.M. et al. (2006). Coping in isolated and confined
    environments. Reviews in Environmental Science & Bio/Technology.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ── Types de veto ─────────────────────────────────────────────────────────────

class VetoType(str, Enum):
    HARD     = "HARD"      # Disqualification totale
    SOFT     = "SOFT"      # High Risk flag, score maintenu
    ADVISORY = "ADVISORY"  # Avertissement seulement


class SafetyLevel(str, Enum):
    CLEAR      = "CLEAR"        # Aucun veto déclenché
    ADVISORY   = "ADVISORY"     # Avertissement(s)
    HIGH_RISK  = "HIGH_RISK"    # Veto SOFT déclenché
    DISQUALIFIED = "DISQUALIFIED"  # Veto HARD déclenché


# ── Règles de veto par défaut ─────────────────────────────────────────────────

@dataclass
class VetoRule:
    """
    Règle de veto sur un trait.

    trait          : clé du trait dans le psychometric_snapshot
    threshold      : seuil critique (score 0-100)
    veto_type      : HARD / SOFT / ADVISORY
    label          : description lisible
    context_note   : justification du seuil (pour l'audit)
    positions_scope: None = tous les postes, sinon liste des postes ciblés
    """
    trait:           str
    threshold:       float
    veto_type:       VetoType
    label:           str
    context_note:    str = ""
    positions_scope: Optional[List[str]] = None


# Règles de veto par défaut — Phase 0 SME panel maritime
DEFAULT_VETO_RULES: List[VetoRule] = [

    # ── HARD VETO ────────────────────────────────────────────
    VetoRule(
        trait="emotional_stability",
        threshold=15.0,
        veto_type=VetoType.HARD,
        label="Instabilité émotionnelle sévère",
        context_note=(
            "ES < 15 correspond à un profil de Neuroticism > 85. "
            "En environnement maritime isolé (6-12 mois), ce niveau "
            "génère un risque de crise psychologique aigu pour l'individu "
            "et l'équipage. Veto absolu de sécurité."
        ),
    ),
    VetoRule(
        trait="agreeableness",
        threshold=15.0,
        veto_type=VetoType.HARD,
        label="Niveau d'agréabilité critique",
        context_note=(
            "A < 15 signale un profil potentiellement hostile. "
            "Dans un espace confiné sans échappatoire, le risque "
            "de conflit violent est jugé inacceptable. "
            "(Hackman 2002 — règle du maillon faible, version sécurité)"
        ),
    ),

    # ── SOFT VETO (High Risk) ─────────────────────────────────
    VetoRule(
        trait="emotional_stability",
        threshold=30.0,
        veto_type=VetoType.SOFT,
        label="Fragilité émotionnelle — risque d'épuisement",
        context_note=(
            "ES entre 15 et 30 : profil vulnérable au burnout en haute saison. "
            "L'employeur doit peser le risque de turnover anticipé."
        ),
    ),
    VetoRule(
        trait="agreeableness",
        threshold=30.0,
        veto_type=VetoType.SOFT,
        label="Agréabilité basse — risque de friction équipe",
        context_note=(
            "A entre 15 et 30 : marin difficile à manager, risque de climat toxique. "
            "Non rédhibitoire mais requiert une attention managériale particulière."
        ),
    ),
    VetoRule(
        trait="conscientiousness",
        threshold=25.0,
        veto_type=VetoType.SOFT,
        label="Conscienciosité très basse — risque de négligence",
        context_note=(
            "C < 25 corrèle avec la négligence dans les tâches de maintenance. "
            "Risque élevé sur un yacht où les standards techniques sont critiques."
        ),
    ),
    VetoRule(
        trait="gca",
        threshold=20.0,
        veto_type=VetoType.SOFT,
        label="Capacité cognitive très basse",
        context_note=(
            "GCA < 20 indique des difficultés d'apprentissage qui peuvent "
            "compromettre la maîtrise des procédures de sécurité maritimes."
        ),
        positions_scope=["Captain", "Chief Officer", "Chief Engineer", "Engineer"],
    ),

    # ── ADVISORY ─────────────────────────────────────────────
    VetoRule(
        trait="resilience",
        threshold=35.0,
        veto_type=VetoType.ADVISORY,
        label="Résilience faible",
        context_note=(
            "Résilience < 35 : le candidat peut avoir du mal à récupérer "
            "des périodes intensives (charter consécutifs). Non rédhibitoire."
        ),
    ),
    VetoRule(
        trait="conscientiousness",
        threshold=35.0,
        veto_type=VetoType.ADVISORY,
        label="Conscienciosité sous la médiane",
        context_note="C entre 25 et 35 : légèrement sous le niveau recommandé.",
    ),
]


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class VetoTrigger:
    """Un veto déclenché sur un trait spécifique."""
    rule:            VetoRule
    trait:           str
    observed_score:  float
    threshold:       float
    veto_type:       VetoType
    label:           str
    context_note:    str = ""


@dataclass
class SafetyBarrierResult:
    """
    Résultat de l'analyse de la barrière de sécurité.

    safety_level    → CLEAR | ADVISORY | HIGH_RISK | DISQUALIFIED
    g_fit_suspended → True si l'agrégation compensatoire est suspendue
    triggers        → liste des vetos déclenchés
    adjusted_score  → G_fit modifié selon la logique non-compensatoire
                      (0.0 si DISQUALIFIED, inchangé si ADVISORY/CLEAR)
    context_flags   → messages lisibles pour le rapport client
    """
    safety_level:      SafetyLevel
    g_fit_suspended:   bool
    triggers:          List[VetoTrigger] = field(default_factory=list)
    adjusted_score:    Optional[float] = None  # None = score inchangé
    context_flags:     List[str] = field(default_factory=list)
    audit_trail:       List[str] = field(default_factory=list)


# ── Extraction de score de trait ──────────────────────────────────────────────

def _get_trait_score(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait le score brut d'un trait depuis le snapshot.
    Retourne None si le trait est absent (non vérifié).
    """
    if trait == "gca":
        cog = snapshot.get("cognitive") or {}
        return cog.get("gca_score")

    if trait == "emotional_stability":
        val = snapshot.get("emotional_stability")
        if val is not None:
            return float(val)
        bf = snapshot.get("big_five") or {}
        n = bf.get("neuroticism")
        if n is not None:
            n_score = n.get("score", n) if isinstance(n, dict) else n
            return 100.0 - float(n_score)
        return None

    if trait == "resilience":
        val = snapshot.get("resilience")
        if val is not None:
            return float(val)
        return None  # Pas de proxy ici — on ne veto que si le trait est mesuré

    bf = snapshot.get("big_five") or {}
    val = bf.get(trait)
    if val is None:
        return None
    return float(val.get("score", 0)) if isinstance(val, dict) else float(val)


# ── Évaluation principale ─────────────────────────────────────────────────────

def evaluate(
    candidate_snapshot: Dict,
    g_fit_score: float,
    veto_rules: Optional[List[VetoRule]] = None,
    position_key: Optional[str] = None,
) -> SafetyBarrierResult:
    """
    Évalue la barrière de sécurité et ajuste G_fit si nécessaire.

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        g_fit_score        : G_fit calculé par global_fit.py (avant ajustement)
        veto_rules         : règles personnalisées (DEFAULT_VETO_RULES si None)
        position_key       : YachtPosition.value — filtre les règles position-scoped

    Returns:
        SafetyBarrierResult :
        - CLEAR        → adjusted_score = g_fit_score (inchangé)
        - ADVISORY     → adjusted_score = g_fit_score (inchangé, flag seulement)
        - HIGH_RISK    → adjusted_score = g_fit_score (calculé mais annoté HIGH_RISK)
        - DISQUALIFIED → adjusted_score = 0.0 (agrégation suspendue)

    Règle de priorité des vetos :
        HARD > SOFT > ADVISORY
        Si un HARD est déclenché → DISQUALIFIED, stop.
        Plusieurs SOFT → HIGH_RISK global.
    """
    rules = veto_rules or DEFAULT_VETO_RULES
    triggers: List[VetoTrigger] = []
    audit: List[str] = []

    for rule in rules:
        # Filtre position si défini
        if rule.positions_scope and position_key:
            if position_key not in rule.positions_scope:
                continue

        observed = _get_trait_score(candidate_snapshot, rule.trait)
        if observed is None:
            audit.append(f"SKIP {rule.trait}: trait non mesuré — veto non applicable")
            continue

        audit.append(
            f"CHECK {rule.trait}: score={observed:.1f} threshold={rule.threshold:.1f} "
            f"({rule.veto_type.value})"
        )

        if observed < rule.threshold:
            triggers.append(VetoTrigger(
                rule=rule,
                trait=rule.trait,
                observed_score=observed,
                threshold=rule.threshold,
                veto_type=rule.veto_type,
                label=rule.label,
                context_note=rule.context_note,
            ))
            audit.append(f"  → TRIGGERED: {rule.label} ({observed:.1f} < {rule.threshold:.1f})")

    # ── Détermination du safety_level ────────────────────────
    hard_triggers = [t for t in triggers if t.veto_type == VetoType.HARD]
    soft_triggers = [t for t in triggers if t.veto_type == VetoType.SOFT]
    advisory_triggers = [t for t in triggers if t.veto_type == VetoType.ADVISORY]

    if hard_triggers:
        # DISQUALIFIED — agrégation suspendue
        safety_level = SafetyLevel.DISQUALIFIED
        g_fit_suspended = True
        adjusted_score = 0.0

        context_flags = [
            f"🚨 DISQUALIFIÉ: {t.label} (score {t.observed_score:.0f} < seuil {t.threshold:.0f})"
            for t in hard_triggers
        ]
        for t in soft_triggers + advisory_triggers:
            context_flags.append(f"⚠️ {t.label} (score {t.observed_score:.0f})")

    elif soft_triggers:
        # HIGH_RISK — score maintenu mais annoté
        safety_level = SafetyLevel.HIGH_RISK
        g_fit_suspended = True    # Agrégation suspendue = score affiché séparément
        adjusted_score = g_fit_score  # Score calculé mais noté HIGH_RISK

        context_flags = [
            f"⚠️ HIGH RISK: {t.label} (score {t.observed_score:.0f} < seuil {t.threshold:.0f})"
            for t in soft_triggers
        ]
        for t in advisory_triggers:
            context_flags.append(f"ℹ️ {t.label} (score {t.observed_score:.0f})")

    elif advisory_triggers:
        # ADVISORY — calcul inchangé
        safety_level = SafetyLevel.ADVISORY
        g_fit_suspended = False
        adjusted_score = None  # Inchangé

        context_flags = [
            f"ℹ️ {t.label} (score {t.observed_score:.0f} < seuil {t.threshold:.0f})"
            for t in advisory_triggers
        ]

    else:
        # CLEAR — tout ok
        safety_level = SafetyLevel.CLEAR
        g_fit_suspended = False
        adjusted_score = None
        context_flags = []

    return SafetyBarrierResult(
        safety_level=safety_level,
        g_fit_suspended=g_fit_suspended,
        triggers=triggers,
        adjusted_score=adjusted_score,
        context_flags=context_flags,
        audit_trail=audit,
    )