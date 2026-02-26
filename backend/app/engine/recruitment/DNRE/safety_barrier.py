# engine/recruitment/dnre/safety_barrier.py
"""
Barrière de Sécurité Psychométrique — Modèle Non-Compensatoire à Pénalité Continue

SKILL.md V1 — Directive de code :
    Ne PAS utiliser de fonction indicatrice binaire (𝟙) pour éliminer les
    candidats sous le seuil critique (effet couperet instable).

    À coder : Remplacer le produit binaire par une fonction de pénalité
    continue (courbe logistique) pour l'Indice Global Ajusté (G_fit_adjusted).
    Le score doit s'effondrer progressivement à l'approche du seuil de sécurité.

Principe mathématique :
    Pour chaque règle de veto déclenchée (score observé < seuil), on calcule
    un multiplicateur de pénalité via une sigmoïde centrée sur le seuil :

        penalty(x, s, k) = σ(k · (x − s))
                         = 1 / (1 + e^{−k · (x − s)})

    Où :
        x = score observé (0-100)
        s = seuil critique (threshold)
        k = raideur (steepness) — contrôle la vitesse d'effondrement

    Comportement :
        x >> s  →  penalty → 1.0   (pas de pénalité)
        x =  s  →  penalty = 0.5   (réduction de moitié au seuil)
        x << s  →  penalty → 0.0   (score effacé loin sous le seuil)

    Raideurs par défaut :
        HARD     : k = 0.50  (effondrement rapide, quasi-zéro sous le seuil)
        SOFT     : k = 0.20  (dégradation progressive)
        ADVISORY : k = 0.00  (annotation pure, pas d'impact sur le score)

    Pénalité combinée (plusieurs règles déclenchées) :
        penalty_combined = Π penalty_i   (produit des pénalités individuelles)

    Score ajusté :
        adjusted_score = g_fit × penalty_combined

    Le niveau de sécurité (safety_level) reste classé en CLEAR / ADVISORY /
    HIGH_RISK / DISQUALIFIED pour la lisibilité humaine et l'audit. La valeur
    adjusted_score reflète désormais la dégradation continue.

Architecture des vetos :
    HARD VETO (blocage quasi-total) :
        Pénalité très raide — score proche de zéro bien sous le seuil.
        Reserved pour traits de sécurité absolus (ex: ES < 15 = risque crise).

    SOFT VETO (dégradation marquée) :
        Pénalité progressive — score significativement réduit sous le seuil.
        Reserved pour traits importants mais pas critiques de sécurité.

    ADVISORY (annotation seulement) :
        Aucune pénalité sur le score — flag d'avertissement uniquement.
        Pour signaler des sous-performances contextuelles.

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


# ── Raideurs logistiques par type de veto ─────────────────────────────────────

STEEPNESS_HARD:     float = 0.50   # Effondrement rapide — quasi-zéro sous le seuil
STEEPNESS_SOFT:     float = 0.20   # Dégradation progressive
STEEPNESS_ADVISORY: float = 0.00   # Pas d'impact sur le score


# ── Types de veto ─────────────────────────────────────────────────────────────

class VetoType(str, Enum):
    HARD     = "HARD"      # Pénalité très raide, score quasi-nul sous seuil
    SOFT     = "SOFT"      # Pénalité progressive, score réduit sous seuil
    ADVISORY = "ADVISORY"  # Annotation uniquement, score inchangé


class SafetyLevel(str, Enum):
    CLEAR        = "CLEAR"        # Aucun veto déclenché
    ADVISORY     = "ADVISORY"     # Avertissement(s), score intact
    HIGH_RISK    = "HIGH_RISK"    # Veto SOFT déclenché, score dégradé
    DISQUALIFIED = "DISQUALIFIED" # Veto HARD déclenché, score quasi-nul


# ── Règles de veto par défaut ─────────────────────────────────────────────────

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
                     Permet de surcharger la raideur pour des règles spécifiques.
    """
    trait:           str
    threshold:       float
    veto_type:       VetoType
    label:           str
    context_note:    str = ""
    positions_scope: Optional[List[str]] = None
    steepness:       Optional[float] = None   # None → STEEPNESS_{HARD|SOFT|ADVISORY}

    def effective_steepness(self) -> float:
        """Retourne la raideur effective (surcharge ou défaut par veto_type)."""
        if self.steepness is not None:
            return self.steepness
        if self.veto_type == VetoType.HARD:
            return STEEPNESS_HARD
        if self.veto_type == VetoType.SOFT:
            return STEEPNESS_SOFT
        return STEEPNESS_ADVISORY


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
    """
    Un veto déclenché sur un trait spécifique.

    penalty_multiplier : valeur [0, 1] de la sigmoïde pour cette règle.
                         1.0 = pas de pénalité, 0.0 = score effacé.
    """
    rule:               VetoRule
    trait:              str
    observed_score:     float
    threshold:          float
    veto_type:          VetoType
    label:              str
    context_note:       str = ""
    penalty_multiplier: float = 1.0   # contribution de cette règle à la pénalité combinée


@dataclass
class SafetyBarrierResult:
    """
    Résultat de l'analyse de la barrière de sécurité.

    safety_level       → CLEAR | ADVISORY | HIGH_RISK | DISQUALIFIED
    g_fit_suspended    → True si au moins un veto HARD ou SOFT est déclenché
    triggers           → liste des vetos déclenchés (tous types)
    penalty_multiplier → produit des pénalités logistiques ∈ [0, 1]
                         (ADVISORY non compris — annotation seulement)
    adjusted_score     → g_fit × penalty_multiplier (score dégradé continûment)
                         None uniquement si safety_level = CLEAR ou ADVISORY
                         (aucune règle HARD/SOFT déclenchée → score intact)
    context_flags      → messages lisibles pour le rapport client
    audit_trail        → log interne des vérifications effectuées
    """
    safety_level:      SafetyLevel
    g_fit_suspended:   bool
    triggers:          List[VetoTrigger] = field(default_factory=list)
    penalty_multiplier: float = 1.0    # 1.0 = aucune pénalité
    adjusted_score:    Optional[float] = None  # None = score inchangé (CLEAR/ADVISORY)
    context_flags:     List[str] = field(default_factory=list)
    audit_trail:       List[str] = field(default_factory=list)


# ── Calcul de la pénalité logistique ─────────────────────────────────────────

def _logistic_penalty(observed: float, threshold: float, steepness: float) -> float:
    """
    Calcule le multiplicateur de pénalité logistique pour un trait donné.

    Formule :
        penalty = σ(k · (x − s)) = 1 / (1 + e^{−k · (x − s)})

    Où k = steepness, x = observed, s = threshold.

    Propriétés :
        - Si observed = threshold → penalty = 0.5 (réduction de moitié)
        - Si observed >> threshold → penalty → 1.0 (pas de pénalité)
        - Si observed << threshold → penalty → 0.0 (score effacé)
        - Si steepness = 0 → penalty = 0.5 toujours (non utilisé en pratique)

    Args:
        observed  : score observé du candidat (0-100)
        threshold : seuil de la règle de veto
        steepness : raideur de la courbe (k > 0)

    Returns:
        float ∈ (0.0, 1.0)
    """
    if steepness == 0.0:
        # Règle ADVISORY — pénalité neutralisée (aucun impact sur le score)
        return 1.0
    return 1.0 / (1.0 + math.exp(-steepness * (observed - threshold)))


# ── Extraction de score de trait ──────────────────────────────────────────────

def _get_trait_score(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait le score brut d'un trait depuis le snapshot.
    Retourne None si le trait est absent (veto non applicable).
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
        return None  # Pas de proxy — veto non applicable si non mesuré

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
    Évalue la barrière de sécurité et calcule le G_fit ajusté par pénalité continue.

    L'ajustement est continu (sigmoïde) et non binaire :
    - Le score ne tombe pas brusquement à 0.0 sur un couperet
    - Il s'effondre progressivement à l'approche du seuil de sécurité
    - Plus le candidat est loin sous le seuil, plus la pénalité est sévère

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        g_fit_score        : G_fit calculé par global_fit.py (avant ajustement)
        veto_rules         : règles personnalisées (DEFAULT_VETO_RULES si None)
        position_key       : YachtPosition.value — filtre les règles position-scoped

    Returns:
        SafetyBarrierResult avec :
        - safety_level   : classification humaine (CLEAR / ADVISORY / HIGH_RISK / DISQUALIFIED)
        - penalty_multiplier : produit des sigmoïdes des règles HARD + SOFT déclenchées
        - adjusted_score : g_fit × penalty_multiplier (ou None si CLEAR/ADVISORY)

    Comportement par safety_level :
        CLEAR      → penalty_multiplier = 1.0, adjusted_score = None (score intact)
        ADVISORY   → penalty_multiplier = 1.0, adjusted_score = None (score intact)
        HIGH_RISK  → 0 < penalty_multiplier < 1, adjusted_score < g_fit_score (dégradé)
        DISQUALIFIED → penalty_multiplier ≈ 0, adjusted_score ≈ 0 (quasi-nul)

    Règle de priorité des labels :
        HARD > SOFT > ADVISORY
        La pénalité est le produit de TOUTES les règles HARD + SOFT déclenchées.
        Les règles ADVISORY n'affectent jamais le score (steepness = 0.0).
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
            # Calcul de la pénalité logistique pour cette règle
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

    # ── Calcul de la pénalité combinée (HARD + SOFT seulement) ───────────────
    # La pénalité combinée est le produit des pénalités individuelles.
    # ADVISORY : steepness=0.0 → _logistic_penalty retourne 1.0 → pas d'impact.
    # On l'exclut explicitement pour clarté et pour ne pas l'accumuler.
    penalizing_triggers = hard_triggers + soft_triggers
    combined_penalty: float = 1.0
    for t in penalizing_triggers:
        combined_penalty *= t.penalty_multiplier

    # ── Classification humaine et score ajusté ────────────────────────────────
    if hard_triggers:
        safety_level   = SafetyLevel.DISQUALIFIED
        g_fit_suspended = True
        # Score quasi-nul — la pénalité combinée HARD est très proche de 0.
        # On conserve 3 décimales pour garantir que la valeur continue est visible
        # même quand le produit des pénalités est très faible (ex: 0.023).
        adjusted_score = round(g_fit_score * combined_penalty, 3)

        context_flags = [
            f"🚨 DISQUALIFIÉ: {t.label} "
            f"(score {t.observed_score:.0f} < seuil {t.threshold:.0f}, "
            f"pénalité={t.penalty_multiplier:.3f})"
            for t in hard_triggers
        ]
        for t in soft_triggers:
            context_flags.append(
                f"⚠️ {t.label} (score {t.observed_score:.0f}, pénalité={t.penalty_multiplier:.3f})"
            )
        for t in advisory_triggers:
            context_flags.append(f"ℹ️ {t.label} (score {t.observed_score:.0f})")

    elif soft_triggers:
        safety_level    = SafetyLevel.HIGH_RISK
        g_fit_suspended = True
        # Score réduit proportionnellement à la sévérité du dépassement.
        # 3 décimales pour la cohérence et la traçabilité des pénalités continues.
        adjusted_score  = round(g_fit_score * combined_penalty, 3)

        context_flags = [
            f"⚠️ HIGH RISK: {t.label} "
            f"(score {t.observed_score:.0f} < seuil {t.threshold:.0f}, "
            f"pénalité={t.penalty_multiplier:.3f})"
            for t in soft_triggers
        ]
        for t in advisory_triggers:
            context_flags.append(f"ℹ️ {t.label} (score {t.observed_score:.0f})")

    elif advisory_triggers:
        safety_level    = SafetyLevel.ADVISORY
        g_fit_suspended = False
        adjusted_score  = None   # Score intact — ADVISORY n'affecte pas le score
        combined_penalty = 1.0   # Redondant mais explicite

        context_flags = [
            f"ℹ️ {t.label} (score {t.observed_score:.0f} < seuil {t.threshold:.0f})"
            for t in advisory_triggers
        ]

    else:
        safety_level    = SafetyLevel.CLEAR
        g_fit_suspended = False
        adjusted_score  = None
        combined_penalty = 1.0
        context_flags   = []

    return SafetyBarrierResult(
        safety_level=safety_level,
        g_fit_suspended=g_fit_suspended,
        triggers=triggers,
        penalty_multiplier=round(combined_penalty, 6),
        adjusted_score=adjusted_score,
        context_flags=context_flags,
        audit_trail=audit,
    )
