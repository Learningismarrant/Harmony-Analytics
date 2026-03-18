# engine/recruitment/pe_fit/pj_fit/safety_barrier.py
"""
Barrière de Sécurité Psychométrique — module pe_fit/pj_fit.

Copie fonctionnelle de DNRE/safety_barrier.py avec une modification :
    _get_trait_score() interne remplacé par extract_strict() du trait_extractor.
    Cette refactorisation centralise la logique d'extraction et supprime la
    duplication de code entre les modules.

Toutes les dataclasses (SafetyLevel, VetoTrigger, SafetyBarrierResult)
et la fonction evaluate() conservent la même signature.

Modèle Non-Compensatoire à Pénalité Continue :
    penalty(x, s, k) = σ(k · (x − s)) = 1 / (1 + e^{−k · (x − s)})

    x = score observé (0-100)
    s = seuil critique
    k = raideur de l'effondrement

    adjusted_score = g_fit × Π penalty_i

Sources :
    Hogan, R. & Hogan, J. (2001). Assessing leadership: a view from the
    dark side. International Journal of Selection and Assessment.
    Sandal, G.M. et al. (2006). Coping in isolated and confined
    environments. Reviews in Environmental Science & Bio/Technology.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.engine.pe_fit.trait_extractor import extract_strict


# ── Raideurs logistiques par type de veto ─────────────────────────────────────

STEEPNESS_HARD:     float = 0.50
STEEPNESS_SOFT:     float = 0.20
STEEPNESS_ADVISORY: float = 0.00


# ── Types de veto ─────────────────────────────────────────────────────────────

class VetoType(str, Enum):
    HARD     = "HARD"
    SOFT     = "SOFT"
    ADVISORY = "ADVISORY"


class SafetyLevel(str, Enum):
    CLEAR        = "CLEAR"
    ADVISORY     = "ADVISORY"
    HIGH_RISK    = "HIGH_RISK"
    DISQUALIFIED = "DISQUALIFIED"


# ── Règle de veto ─────────────────────────────────────────────────────────────

@dataclass
class VetoRule:
    """
    Règle de veto sur un trait psychométrique.

    trait          : clé du trait dans le psychometric_snapshot
    threshold      : seuil critique (score 0-100)
    veto_type      : HARD / SOFT / ADVISORY
    label          : description lisible pour le rapport client
    context_note   : justification du seuil (audit)
    positions_scope: None = tous les postes, sinon liste des postes ciblés
    steepness      : raideur de la courbe logistique (None → défaut par veto_type)
    """
    trait:           str
    threshold:       float
    veto_type:       VetoType
    label:           str
    context_note:    str = ""
    positions_scope: Optional[List[str]] = None
    steepness:       Optional[float] = None

    def effective_steepness(self) -> float:
        if self.steepness is not None:
            return self.steepness
        if self.veto_type == VetoType.HARD:
            return STEEPNESS_HARD
        if self.veto_type == VetoType.SOFT:
            return STEEPNESS_SOFT
        return STEEPNESS_ADVISORY


# ── Règles de veto par défaut ─────────────────────────────────────────────────

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
    rule:               VetoRule
    trait:              str
    observed_score:     float
    threshold:          float
    veto_type:          VetoType
    label:              str
    context_note:       str = ""
    penalty_multiplier: float = 1.0


@dataclass
class SafetyBarrierResult:
    """
    Résultat de l'analyse de la barrière de sécurité.

    safety_level       → CLEAR | ADVISORY | HIGH_RISK | DISQUALIFIED
    g_fit_suspended    → True si au moins un veto HARD ou SOFT est déclenché
    triggers           → liste des vetos déclenchés (tous types)
    penalty_multiplier → produit des pénalités logistiques ∈ [0, 1]
    adjusted_score     → g_fit × penalty_multiplier (score dégradé continûment)
    context_flags      → messages lisibles pour le rapport client
    audit_trail        → log interne des vérifications effectuées
    """
    safety_level:       SafetyLevel
    g_fit_suspended:    bool
    triggers:           List[VetoTrigger] = field(default_factory=list)
    penalty_multiplier: float = 1.0
    adjusted_score:     Optional[float] = None
    context_flags:      List[str] = field(default_factory=list)
    audit_trail:        List[str] = field(default_factory=list)


# ── Calcul de la pénalité logistique ─────────────────────────────────────────

def _logistic_penalty(observed: float, threshold: float, steepness: float) -> float:
    """
    Calcule le multiplicateur de pénalité logistique.

    penalty = σ(k · (x − s)) = 1 / (1 + e^{−k · (x − s)})

    steepness = 0.0 → ADVISORY → penalty = 1.0 (pas d'impact)
    """
    if steepness == 0.0:
        return 1.0
    return 1.0 / (1.0 + math.exp(-steepness * (observed - threshold)))


# ── Évaluation principale ─────────────────────────────────────────────────────

def evaluate(
    candidate_snapshot: Dict,
    g_fit_score: float,
    veto_rules: Optional[List[VetoRule]] = None,
    position_key: Optional[str] = None,
) -> SafetyBarrierResult:
    """
    Évalue la barrière de sécurité et calcule le score ajusté par pénalité continue.

    Utilise extract_strict() du trait_extractor — un veto n'est déclenché
    que si la donnée est réellement mesurée (bénéfice du doute si absente).

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        g_fit_score        : score global avant ajustement (0-100)
        veto_rules         : règles personnalisées (DEFAULT_VETO_RULES si None)
        position_key       : YachtPosition.value — filtre les règles position-scoped

    Returns:
        SafetyBarrierResult avec penalty_multiplier et adjusted_score.
    """
    rules = veto_rules or DEFAULT_VETO_RULES
    triggers: List[VetoTrigger] = []
    audit: List[str] = []

    for rule in rules:
        # Filtre position si défini
        if rule.positions_scope and position_key:
            if position_key not in rule.positions_scope:
                continue

        # Extraction via extract_strict (pas de fallback — bénéfice du doute)
        observed = extract_strict(candidate_snapshot, rule.trait)
        if observed is None:
            audit.append(f"SKIP {rule.trait}: trait non mesuré — veto non applicable")
            continue

        audit.append(
            f"CHECK {rule.trait}: score={observed:.1f} threshold={rule.threshold:.1f} "
            f"({rule.veto_type.value})"
        )

        if observed < rule.threshold:
            k = rule.effective_steepness()
            penalty = _logistic_penalty(observed, rule.threshold, k)

            triggers.append(VetoTrigger(
                rule=rule,
                trait=rule.trait,
                observed_score=observed,
                threshold=rule.threshold,
                veto_type=rule.veto_type,
                label=rule.label,
                context_note=rule.context_note,
                penalty_multiplier=penalty,
            ))
            audit.append(
                f"  → TRIGGERED: {rule.label} "
                f"({observed:.1f} < {rule.threshold:.1f}) "
                f"penalty={penalty:.4f} (k={k})"
            )

    # ── Détermination du safety_level ────────────────────────
    hard_triggers     = [t for t in triggers if t.veto_type == VetoType.HARD]
    soft_triggers     = [t for t in triggers if t.veto_type == VetoType.SOFT]
    advisory_triggers = [t for t in triggers if t.veto_type == VetoType.ADVISORY]

    penalizing_triggers = hard_triggers + soft_triggers
    combined_penalty: float = 1.0
    for t in penalizing_triggers:
        combined_penalty *= t.penalty_multiplier

    # ── Classification et score ajusté ───────────────────────
    if hard_triggers:
        safety_level    = SafetyLevel.DISQUALIFIED
        g_fit_suspended = True
        adjusted_score  = round(g_fit_score * combined_penalty, 3)
        context_flags   = [
            f"DISQUALIFIED: {t.label} "
            f"(score {t.observed_score:.0f} < seuil {t.threshold:.0f}, "
            f"pénalité={t.penalty_multiplier:.3f})"
            for t in hard_triggers
        ]
        for t in soft_triggers:
            context_flags.append(
                f"{t.label} (score {t.observed_score:.0f}, pénalité={t.penalty_multiplier:.3f})"
            )
        for t in advisory_triggers:
            context_flags.append(f"{t.label} (score {t.observed_score:.0f})")

    elif soft_triggers:
        safety_level    = SafetyLevel.HIGH_RISK
        g_fit_suspended = True
        adjusted_score  = round(g_fit_score * combined_penalty, 3)
        context_flags   = [
            f"HIGH RISK: {t.label} "
            f"(score {t.observed_score:.0f} < seuil {t.threshold:.0f}, "
            f"pénalité={t.penalty_multiplier:.3f})"
            for t in soft_triggers
        ]
        for t in advisory_triggers:
            context_flags.append(f"{t.label} (score {t.observed_score:.0f})")

    elif advisory_triggers:
        safety_level     = SafetyLevel.ADVISORY
        g_fit_suspended  = False
        adjusted_score   = None
        combined_penalty = 1.0
        context_flags    = [
            f"{t.label} (score {t.observed_score:.0f} < seuil {t.threshold:.0f})"
            for t in advisory_triggers
        ]

    else:
        safety_level     = SafetyLevel.CLEAR
        g_fit_suspended  = False
        adjusted_score   = None
        combined_penalty = 1.0
        context_flags    = []

    return SafetyBarrierResult(
        safety_level=safety_level,
        g_fit_suspended=g_fit_suspended,
        triggers=triggers,
        penalty_multiplier=round(combined_penalty, 6),
        adjusted_score=adjusted_score,
        context_flags=context_flags,
        audit_trail=audit,
    )
