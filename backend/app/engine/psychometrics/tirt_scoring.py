# app/engine/psychometrics/tirt_scoring.py
"""
T-IRT Scoring Engine pour l'assessment CUTTY SARK.

Implémente la Théorie de Réponse aux Items Thurstonienne (T-IRT)
selon Brown & Maydeu-Olivares (2011) avec estimation MAP.

Références :
  Brown, A., & Maydeu-Olivares, A. (2011). Item response modeling of
  forced-choice questionnaires. Educational and Psychological Measurement,
  71(3), 460-502.

  Maples, J. L., et al. (2014). A comparison of fifteen structural models
  for personality measurement. Psychological Assessment, 26(4), 1116-1138.

Architecture :
  Entrée  → réponses binaires "left"|"right" pour 60 paires IPIP-120 maritime
  Sortie  → θ = [θ_O, θ_C, θ_E, θ_A, θ_N] + Z-scores + centiles + fiabilité

Appelé par : modules/assessment/service.py  (test_type == "tirt")
Zéro accès DB — fonction 100 % pure et testable.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm as _norm
from typing import Any, Dict, List, Tuple

# ─── Domaines Big Five ───────────────────────────────────────────────────────

DOMAINS = ["O", "C", "E", "A", "N"]

DOMAIN_NAMES: Dict[str, str] = {
    "O": "openness",
    "C": "conscientiousness",
    "E": "extraversion",
    "A": "agreeableness",
    "N": "neuroticism",
}

DOMAIN_IDX: Dict[str, int] = {d: i for i, d in enumerate(DOMAINS)}

# ─── Seuils de fiabilité ────────────────────────────────────────────────────

_MIN_SECONDS_PER_PAIR = 2.0      # Temps moyen minimal par paire (secondes)
_MAX_ONE_SIDE_RATIO = 0.85       # Ratio max pour une seule face (acquiescence)
_MIN_RELIABILITY_IDX = 0.60     # SEM-based reliability index minimum

# ─── Paramètres d'items CUTTY SARK ──────────────────────────────────────────
# Calibration IPIP-120 maritime (inspiré de Maples et al., 2014).
#
# λ (lambda_) : loading sur le trait latent — sensibilité (0.65 – 1.05)
# μ (mu)      : intercept (désirabilité sociale intrinsèque)
#               > 0 → formulation positive (désirable, favorable)
#               < 0 → formulation négative (indésirable, peu avouable)
#
# Note : la direction trait (score_weight ±1) est gérée séparément par
# le calcul du loading effectif : λ_eff = λ * score_weight.
# Ne pas confondre μ (formulation sociale) et score_weight (direction trait).

ITEM_PARAMS: Dict[str, Dict[str, float]] = {

    # ── Conscientiousness (C) ─────────────────────────────────────────────────
    "C1_5":    {"lambda_": 0.88, "mu":  0.75},  # mène à bien ses missions de quart
    "C1_35":   {"lambda_": 0.85, "mu":  0.70},  # vise l'excellence dans chaque manœuvre
    "C1_65":   {"lambda_": 0.82, "mu":  0.65},  # gère ses responsabilités avec efficacité
    "C1_155R": {"lambda_": 0.75, "mu": -0.50},  # doute de ses compétences (situations complexes)
    "C2_10":   {"lambda_": 0.80, "mu":  0.55},  # matériel rangé de manière maniaque
    "C2_40":   {"lambda_": 0.86, "mu":  0.80},  # range son poste de travail après chaque tâche
    "C2_190R": {"lambda_": 0.78, "mu": -0.60},  # laisse ses affaires encombrer les espaces
    "C2_220R": {"lambda_": 0.74, "mu": -0.45},  # laisse traîner ses outils (reviendra plus tard)
    "C3_45":   {"lambda_": 0.90, "mu":  0.85},  # respecte scrupuleusement les consignes sécurité
    "C3_105":  {"lambda_": 0.87, "mu":  0.75},  # dit toujours la vérité sur les incidents
    "C3_195R": {"lambda_": 0.76, "mu": -0.55},  # oublie des détails techniques dans ses rapports
    "C3_225R": {"lambda_": 0.72, "mu": -0.50},  # délègue ses corvées pour gagner du temps
    "C4_50":   {"lambda_": 0.84, "mu":  0.65},  # travaille avec acharnement jusqu'à l'impeccable
    "C4_170":  {"lambda_": 0.70, "mu":  0.10},  # place la barre si haut qu'il est rarement satisfait
    "C4_230R": {"lambda_": 0.78, "mu": -0.70},  # se contente du minimum syndical
    "C5_85":   {"lambda_": 0.83, "mu":  0.72},  # commence ses tâches dès qu'elles sont planifiées
    "C5_175R": {"lambda_": 0.76, "mu": -0.55},  # repousse les tâches administratives ennuyeuses
    "C5_235R": {"lambda_": 0.75, "mu": -0.65},  # a besoin qu'on le pousse pour démarrer
    "C5_265R": {"lambda_": 0.77, "mu": -0.58},  # mal à se motiver pour les tâches répétitives
    "C6_15":   {"lambda_": 0.86, "mu":  0.80},  # réfléchit toujours aux conséquences en mer
    "C6_120R": {"lambda_": 0.79, "mu": -0.60},  # peut agir de manière impulsive sous pression
    "C6_150":  {"lambda_": 0.85, "mu":  0.75},  # pèse chaque décision pour éviter tout risque

    # ── Agreeableness (A) ─────────────────────────────────────────────────────
    "A1_16":   {"lambda_": 0.80, "mu":  0.70},  # fait naturellement confiance à ses collègues
    "A1_41":   {"lambda_": 0.82, "mu":  0.75},  # croit sincèrement en l'honnêteté des gens
    "A1_166R": {"lambda_": 0.74, "mu": -0.55},  # remet souvent en question les motivations supérieurs
    "A2_46":   {"lambda_": 0.85, "mu":  0.80},  # traite tout le monde avec honnêteté et respect total
    "A2_136R": {"lambda_": 0.76, "mu": -0.75},  # manipule la situation pour obtenir ce qu'il veut
    "A2_196R": {"lambda_": 0.78, "mu": -0.80},  # peut tricher sur les règles si personne ne regarde
    "A3_76":   {"lambda_": 0.83, "mu":  0.70},  # prend plaisir à anticiper les besoins des collègues
    "A3_119":  {"lambda_": 0.86, "mu":  0.75},  # toujours prêt à dépanner un collègue surchargé
    "A3_221R": {"lambda_": 0.72, "mu": -0.60},  # privilégie son propre repos avant d'aider les autres
    "A4_16":   {"lambda_": 0.82, "mu":  0.72},  # pardonne facilement les erreurs des collègues
    "A4_106":  {"lambda_": 0.78, "mu":  0.60},  # préfère s'effacer pour éviter un conflit inutile
    "A4_256R": {"lambda_": 0.75, "mu": -0.68},  # entre en conflit pour imposer son point de vue
    "A5_131":  {"lambda_": 0.80, "mu":  0.65},  # sait rester humble même après une prouesse technique
    "A5_226R": {"lambda_": 0.74, "mu": -0.65},  # parfois perçu comme froid ou distant
    "A5_286R": {"lambda_": 0.76, "mu": -0.60},  # critique ouvertement les incompétences
    "A6_59":   {"lambda_": 0.84, "mu":  0.75},  # soutient moralement ses collègues quand le moral flanche
    "A6_149R": {"lambda_": 0.77, "mu": -0.55},  # reste indifférent aux émotions de son équipe

    # ── Extraversion (E) ──────────────────────────────────────────────────────
    "E1_6":    {"lambda_": 0.83, "mu":  0.65},  # crée facilement un lien chaleureux avec les passagers
    "E1_36":   {"lambda_": 0.80, "mu":  0.68},  # sait mettre les passagers à l'aise dès les premières secondes
    "E1_156R": {"lambda_": 0.75, "mu": -0.40},  # garde ses distances pour rester strictement professionnel
    "E2_37":   {"lambda_": 0.85, "mu":  0.70},  # s'épanouit dans l'animation et l'effervescence du bord
    "E2_127R": {"lambda_": 0.80, "mu": -0.50},  # préfère s'isoler en cabine plutôt que de socialiser
    "E3_66":   {"lambda_": 0.88, "mu":  0.72},  # prend naturellement le leadership lors des briefings
    "E3_187R": {"lambda_": 0.78, "mu": -0.55},  # préfère que les autres prennent les décisions importantes
    "E4_96":   {"lambda_": 0.82, "mu":  0.65},  # maintient un rythme d'activité soutenu tout au long du charter
    "E4_277R": {"lambda_": 0.76, "mu": -0.45},  # travaille à son rythme et n'aime pas être bousculé
    "E5_156":  {"lambda_": 0.81, "mu":  0.68},  # apporte une énergie positive et dynamique à tout l'équipage
    "E5_216R": {"lambda_": 0.74, "mu": -0.50},  # préfère une routine calme aux activités nautiques mouvementées
    "E6_126":  {"lambda_": 0.84, "mu":  0.70},  # transmet sa bonne humeur à tout l'équipage
    "E6_217R": {"lambda_": 0.76, "mu": -0.45},  # a du mal à paraître enthousiaste quand il est fatigué

    # ── Neuroticism (N) ───────────────────────────────────────────────────────
    # μ dépend uniquement de la formulation sociale (positive/négative),
    # indépendamment de score_weight.
    "N1_1":    {"lambda_": 0.85, "mu":  0.72},  # reste serein même quand les conditions se dégradent
    "N2_31":   {"lambda_": 0.82, "mu": -0.55},  # s'agace facilement quand les ordres changent
    "N2_186R": {"lambda_": 0.80, "mu": -0.60},  # parfois très en colère contre ses collègues
    "N3_61":   {"lambda_": 0.80, "mu": -0.50},  # broie du noir après une journée difficile
    "N4_91":   {"lambda_": 0.83, "mu":  0.68},  # reste imperturbable face aux critiques des passagers
    "N4_126R": {"lambda_": 0.78, "mu": -0.58},  # se sent souvent mal à l'aise face aux passagers exigeants
    "N4_181":  {"lambda_": 0.82, "mu":  0.65},  # ne se sent jamais gêné, même dans des situations délicates
    "N5_121":  {"lambda_": 0.76, "mu": -0.70},  # compense le stress par des excès (nourriture, etc.)
    "N6_151":  {"lambda_": 0.86, "mu":  0.75},  # garde les idées claires lors des situations d'urgence
    "N6_271R": {"lambda_": 0.78, "mu": -0.62},  # se sent vite dépassé quand plusieurs urgences tombent

    # ── Openness (O) ──────────────────────────────────────────────────────────
    "O1_2":    {"lambda_": 0.82, "mu":  0.65},  # propose souvent des idées créatives pour améliorer le service
    "O1_32":   {"lambda_": 0.84, "mu":  0.70},  # trouve toujours des solutions originales aux problèmes
    "O1_152R": {"lambda_": 0.76, "mu": -0.55},  # n'a pas une imagination très fertile pour résoudre
    "O2_14":   {"lambda_": 0.80, "mu":  0.68},  # apprécie la beauté et l'esthétique des destinations
    "O2_164R": {"lambda_": 0.75, "mu": -0.40},  # prête peu d'attention à l'esthétique et au design du yacht
    "O3_88":   {"lambda_": 0.81, "mu":  0.70},  # accueille avec enthousiasme les nouvelles technologies
    "O3_118R": {"lambda_": 0.76, "mu": -0.50},  # n'aime pas s'attarder sur ses sentiments ou états d'âme
    "O4_134":  {"lambda_": 0.83, "mu":  0.65},  # aime explorer de nouvelles escales, sortir des sentiers battus
    "O4_254R": {"lambda_": 0.77, "mu": -0.55},  # n'aime pas que l'on change l'itinéraire au dernier moment
    "O5_58":   {"lambda_": 0.82, "mu":  0.68},  # s'intéresse de près aux enjeux complexes du secteur maritime
    "O5_239R": {"lambda_": 0.74, "mu": -0.55},  # ne s'intéresse pas aux discussions théoriques ou abstraites
    "O6_144":  {"lambda_": 0.80, "mu":  0.65},  # remet volontiers en question les vieilles habitudes inefficaces
    "O6_209":  {"lambda_": 0.82, "mu":  0.68},  # s'adapte rapidement aux changements de planning de dernière minute
    "O6_299R": {"lambda_": 0.75, "mu": -0.60},  # préfère suivre les ordres sans chercher à les discuter
}


# ─── Construction des données de paires ──────────────────────────────────────


def _build_pair_data(
    responses: List[Any],
    questions_map: Dict[int, Any],
) -> Tuple[List[Tuple], int, Dict[str, int]]:
    """
    Convertit les réponses ORM en vecteur numérique pour l'optimisation MAP.

    Chaque élément du résultat : (y, di_l, mu_l, lam_eff_l, di_r, mu_r, lam_eff_r, sigma)
      y        : 1 si item gauche choisi, 0 si item droit choisi
      di_l/r   : index DOMAINS du domaine (0=O, 1=C, 2=E, 3=A, 4=N)
      mu_l/r   : intercept de chaque item (désirabilité sociale)
      lam_eff  : loading effectif = λ * score_weight (négatif si item inversé)
      sigma    : écart-type résiduel de la paire = √(ψ_l² + ψ_r²)

    Le score_weight = -1 inverse le signe du loading, ce qui implémente
    la correction T-IRT pour les items keyed négativement (Brown & Maydeu-Olivares, 2011).
    """
    pair_data: List[Tuple] = []
    side_counts: Dict[str, int] = {"left": 0, "right": 0}

    for response in responses:
        q = questions_map.get(response.question_id)
        if q is None or not getattr(q, "options", None):
            continue

        options = q.options
        if not isinstance(options, list) or len(options) != 2:
            continue

        left_opt = next((o for o in options if o.get("side") == "left"), None)
        right_opt = next((o for o in options if o.get("side") == "right"), None)
        if not left_opt or not right_opt:
            continue

        # Paramètres items
        left_id = left_opt.get("ipip_id", "")
        right_id = right_opt.get("ipip_id", "")
        params_l = ITEM_PARAMS.get(left_id)
        params_r = ITEM_PARAMS.get(right_id)
        if not params_l or not params_r:
            continue  # item inconnu → paire ignorée

        # Domaines
        dom_l = left_opt.get("domain", "")
        dom_r = right_opt.get("domain", "")
        di_l = DOMAIN_IDX.get(dom_l)
        di_r = DOMAIN_IDX.get(dom_r)
        if di_l is None or di_r is None:
            continue

        # Loading effectif : λ_eff = λ * score_weight
        # score_weight = -1 → item inversé → contribution négative au trait
        sw_l = int(left_opt.get("score_weight", 1))
        sw_r = int(right_opt.get("score_weight", 1))
        lam_eff_l = params_l["lambda_"] * sw_l
        lam_eff_r = params_r["lambda_"] * sw_r

        mu_l = params_l["mu"]
        mu_r = params_r["mu"]

        # Variance résiduelle : ψ = √(1 − λ²)  (variance unique du facteur)
        psi_l = max(0.10, (1.0 - params_l["lambda_"] ** 2) ** 0.5)
        psi_r = max(0.10, (1.0 - params_r["lambda_"] ** 2) ** 0.5)
        sigma = (psi_l ** 2 + psi_r ** 2) ** 0.5

        # Réponse binaire
        chosen = str(response.valeur_choisie).strip().lower()
        if chosen == "left":
            y = 1
            side_counts["left"] += 1
        elif chosen == "right":
            y = 0
            side_counts["right"] += 1
        else:
            continue  # valeur invalide

        pair_data.append((y, di_l, mu_l, lam_eff_l, di_r, mu_r, lam_eff_r, sigma))

    return pair_data, len(pair_data), side_counts


# ─── Optimisation MAP ────────────────────────────────────────────────────────


def _neg_log_posterior(
    theta: np.ndarray,
    pair_data: List[Tuple],
) -> float:
    """
    Log-posterior négative à minimiser.

    log P(θ | y) ∝ log L(θ) + log P(θ)

    Vraisemblance (probit forcé) :
      P(y=1 | θ) = Φ( (μ_l − μ_r + λ_eff_l·θ_{dl} − λ_eff_r·θ_{dr}) / σ )

    Prior N(0, I) :
      log P(θ) = −½ Σ_k θ_k²
    """
    nll = 0.0
    for y, di_l, mu_l, lam_l, di_r, mu_r, lam_r, sigma in pair_data:
        z = (mu_l - mu_r + lam_l * theta[di_l] - lam_r * theta[di_r]) / sigma
        p = _norm.cdf(z)
        p = float(np.clip(p, 1e-10, 1.0 - 1e-10))
        nll -= y * np.log(p) + (1 - y) * np.log(1.0 - p)

    # Régularisation via prior N(0, I)
    nll += 0.5 * float(np.dot(theta, theta))
    return nll


def _gradient(
    theta: np.ndarray,
    pair_data: List[Tuple],
) -> np.ndarray:
    """
    Gradient analytique de la log-posterior négative.

    Fourni à BFGS pour une convergence plus rapide et plus stable.
    """
    grad = np.zeros(len(DOMAINS))

    for y, di_l, mu_l, lam_l, di_r, mu_r, lam_r, sigma in pair_data:
        z = (mu_l - mu_r + lam_l * theta[di_l] - lam_r * theta[di_r]) / sigma
        p = _norm.cdf(z)
        p = float(np.clip(p, 1e-10, 1.0 - 1e-10))
        phi = float(_norm.pdf(z))

        # ∂(−log L) / ∂z
        d_nll_dz = -(y / p - (1.0 - y) / (1.0 - p)) * phi

        # ∂z / ∂θ pour les deux domaines impliqués
        grad[di_l] += d_nll_dz * (lam_l / sigma)
        grad[di_r] -= d_nll_dz * (lam_r / sigma)

    # Gradient du prior
    grad += theta
    return grad


def _optimize_map(
    pair_data: List[Tuple],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimation MAP via algorithme BFGS.

    Retourne :
      theta_opt     : np.ndarray (5,) — traits latents estimés [θ_O, θ_C, θ_E, θ_A, θ_N]
      posterior_var : np.ndarray (5,) — variance a posteriori (diag de H⁻¹, approximation de Laplace)
    """
    theta0 = np.zeros(len(DOMAINS))

    result = minimize(
        fun=_neg_log_posterior,
        x0=theta0,
        args=(pair_data,),
        jac=_gradient,
        method="BFGS",
        options={"maxiter": 500, "gtol": 1e-6},
    )

    theta_opt: np.ndarray = result.x

    # Variance a posteriori via l'inverse-Hessien BFGS (approximation de Laplace)
    if hasattr(result, "hess_inv") and result.hess_inv is not None:
        hess_inv = np.asarray(result.hess_inv)
        posterior_var = np.diag(hess_inv)
    else:
        posterior_var = np.ones(len(DOMAINS))  # fallback conservateur

    return theta_opt, posterior_var


# ─── Fiabilité ───────────────────────────────────────────────────────────────


def _compute_reliability_index(posterior_var: np.ndarray) -> float:
    """
    Indice de fiabilité basé sur l'erreur standard de mesure (SEM).

    Formule : ρ = 1 − mean(SEM²) = 1 − mean(Var_post)
    Sous prior N(0,1), la variance totale = 1 → ρ ∈ [0, 1].
    """
    sem_sq = np.clip(posterior_var, 0.0, 1.0)
    return float(np.clip(1.0 - float(np.mean(sem_sq)), 0.0, 1.0))


def _check_response_quality(
    n_answered: int,
    side_counts: Dict[str, int],
    total_seconds: float,
) -> Tuple[bool, List[str]]:
    """Détecte les biais de réponse (vitesse et acquiescement)."""
    is_reliable = True
    reasons: List[str] = []

    # Vitesse moyenne par paire
    if n_answered > 0 and total_seconds > 0:
        avg_sec = total_seconds / n_answered
        if avg_sec < _MIN_SECONDS_PER_PAIR:
            is_reliable = False
            reasons.append(
                f"Temps de réponse suspect ({avg_sec:.1f}s/paire, minimum {_MIN_SECONDS_PER_PAIR}s)"
            )

    # Acquiescement (toujours le même côté)
    if n_answered > 10:
        for side, count in side_counts.items():
            ratio = count / n_answered
            if ratio > _MAX_ONE_SIDE_RATIO:
                is_reliable = False
                reasons.append(
                    f"Biais d'acquiescement ({side!r} choisi dans {ratio:.0%} des paires)"
                )
                break

    return is_reliable, reasons


# ─── Label qualitatif ────────────────────────────────────────────────────────


def _level_label(percentile: float) -> str:
    """Convertit un centile (0-100) en étiquette qualitative."""
    if percentile >= 75:
        return "Élevé"
    if percentile >= 30:
        return "Moyen"
    return "Faible"


# ─── Point d'entrée public ───────────────────────────────────────────────────


def calculate_tirt_scores(
    responses: List[Any],
    questions_map: Dict[int, Any],
    total_seconds: float = 0.0,
) -> Dict:
    """
    Calcule les scores T-IRT pour l'assessment CUTTY SARK (60 paires IPIP-120).

    Implémente l'estimation MAP de Brown & Maydeu-Olivares (2011).
    Les items inversés (score_weight: -1) sont gérés via le loading effectif
    λ_eff = λ * score_weight, qui inverse la contribution à θ_k.

    Args:
        responses     : List de ResponseIn ORM (valeur_choisie = "left" | "right")
        questions_map : {question_id: Question ORM}  — Question.options = JSON paire
        total_seconds : Durée totale du test en secondes (pour détection de vitesse)

    Returns:
        Dict compatible avec TestResult.scores :
          "traits"      → {nom_domaine: {"score": centile 0-100, "niveau": str}}
          "global_score"→ float  (moyenne des percentiles bénéfiques : C, A, E, O, stabilité)
          "reliability" → {"is_reliable": bool, "reasons": List[str]}
          "meta"        → {"total_time_seconds": float, "avg_seconds_per_question": float}
          "tirt_detail" → {domaine: {"z_score": float, "percentile": float},
                           "reliability_index": float}

    Raises:
        ValueError : si aucune paire valide ne peut être extraite des réponses.
    """
    pair_data, n_answered, side_counts = _build_pair_data(responses, questions_map)

    if not pair_data:
        raise ValueError(
            "Aucune paire TIRT valide extraite des réponses. "
            "Vérifiez que les Question.options contiennent les champs "
            "'side', 'ipip_id', 'domain' et 'score_weight'."
        )

    # ── Estimation MAP ──────────────────────────────────────────────────────
    theta_opt, posterior_var = _optimize_map(pair_data)

    # ── Scores ─────────────────────────────────────────────────────────────
    # θ est sur l'échelle N(0,1) grâce au prior MAP → interprétable comme Z-score
    z_scores = {d: float(theta_opt[i]) for i, d in enumerate(DOMAINS)}
    percentiles = {d: float(_norm.cdf(z) * 100.0) for d, z in z_scores.items()}

    # ── Fiabilité ───────────────────────────────────────────────────────────
    reliability_index = _compute_reliability_index(posterior_var)
    is_reliable, reasons = _check_response_quality(n_answered, side_counts, total_seconds)

    if reliability_index < _MIN_RELIABILITY_IDX:
        is_reliable = False
        reasons.append(
            f"Indice de fiabilité psychométrique insuffisant (ρ = {reliability_index:.2f})"
        )

    # ── Traits 0-100 (format compatible build_snapshot / DNRE) ─────────────
    trait_scores = {
        DOMAIN_NAMES[d]: {
            "score": round(percentiles[d], 1),
            "niveau": _level_label(percentiles[d]),
        }
        for d in DOMAINS
    }

    # ── Score global bénéfique ──────────────────────────────────────────────
    # Pour N : la stabilité émotionnelle (100 − N) est l'attribut positif
    stability_pct = 100.0 - percentiles["N"]
    global_score = round(
        (percentiles["O"] + percentiles["C"] + percentiles["E"]
         + percentiles["A"] + stability_pct) / 5.0,
        1,
    )

    # ── Détail T-IRT (Z-scores bruts + centiles + fiabilité) ───────────────
    tirt_detail: Dict[str, Any] = {
        d: {
            "z_score": round(z_scores[d], 3),
            "percentile": round(percentiles[d], 1),
        }
        for d in DOMAINS
    }
    tirt_detail["reliability_index"] = round(reliability_index, 3)

    return {
        "traits": trait_scores,
        "global_score": global_score,
        "reliability": {
            "is_reliable": is_reliable,
            "reasons": reasons,
        },
        "meta": {
            "total_time_seconds": total_seconds,
            "avg_seconds_per_question": (
                round(total_seconds / n_answered, 1) if n_answered > 0 else 0.0
            ),
        },
        "tirt_detail": tirt_detail,
    }
