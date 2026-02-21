# engine/recruitment/master.py
"""
Équation maîtresse Ŷ_success et les 4 facteurs psychosociaux.

Ŷ_success = β1·P_ind + β2·F_team + β3·F_env + β4·F_lmx + ε

Toutes les fonctions sont pures — aucun accès DB.
Les données arrivent via les snapshots hydratés par les services.
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
# BETAS — chargés depuis ModelVersion (DB)
# Ces valeurs sont les priors de la littérature (Temps 1)
# Remplacés par les betas de la régression dès que n > 150
# ─────────────────────────────────────────────

DEFAULT_BETAS = {
    "b1_p_ind": 0.25,   # Performance individuelle
    "b2_f_team": 0.35,  # Compatibilité équipe (dominant dans le yachting)
    "b3_f_env": 0.20,   # Compatibilité environnementale JD-R
    "b4_f_lmx": 0.20,   # Compatibilité leadership Captain's Shadow
}


@dataclass
class RecruitmentScore:
    y_success: float        # Score final 0-100
    p_ind: float
    f_team: float
    f_env: float
    f_lmx: float
    betas_used: Dict        # Snapshot des betas au moment du calcul
    completeness: float     # Qualité des données d'entrée


# ─────────────────────────────────────────────
# P_ind : Performance Individuelle (Taskwork)
# P_ind = ω1·GCA + ω2·C
# ─────────────────────────────────────────────

def compute_p_ind(candidate_inputs: Dict) -> float:
    """
    Prédit la capacité brute à exécuter le travail technique.

    Args:
        candidate_inputs: extrait de extract_engine_inputs(snapshot)
    """
    gca = candidate_inputs.get("gca", 0)
    conscientiousness = candidate_inputs.get("conscientiousness", 0)

    omega_1 = 0.60  # Intelligence cognitive — prédicteur le plus robuste (Schmidt & Hunter, 1998)
    omega_2 = 0.40  # Conscienciosité

    return round((gca * omega_1) + (conscientiousness * omega_2), 1)


# ─────────────────────────────────────────────
# F_team : Compatibilité d'Équipe (Social Harmony)
# F_team = wa·min(A_i) - wc·σ(C_i) + we·μ(ES_i)
# ─────────────────────────────────────────────

def compute_f_team(harmony_result) -> float:
    """
    Compatibilité d'équipe depuis un HarmonyResult.

    Args:
        harmony_result: HarmonyResult depuis engine/team/harmony.py
    """
    wa = 0.40  # Poids agréabilité (modèle disjonctif)
    wc = 0.30  # Poids variance conscienciosité (pénalité faultlines)
    we = 0.30  # Poids stabilité émotionnelle (modèle additif)

    f_team = (
        (harmony_result.min_agreeableness * wa)
        - (harmony_result.sigma_conscientiousness * wc)
        + (harmony_result.mean_emotional_stability * we)
    )
    return round(max(0.0, min(100.0, f_team)), 1)


# ─────────────────────────────────────────────
# F_env : Compatibilité Environnementale (JD-R)
# F_env = (R_yacht / D_yacht) × Resilience_ind
# ─────────────────────────────────────────────

def compute_f_env(
    candidate_inputs: Dict,
    vessel_params: Dict,
) -> float:
    """
    Ratio entre les ressources du yacht et ses demandes,
    pondéré par la résilience individuelle du candidat.

    Args:
        candidate_inputs: extrait de extract_engine_inputs(snapshot)
        vessel_params: depuis VesselProfile (charter_intensity, salary_index, etc.)
    """
    # Ressources du yacht (R_yacht) — normalisées 0-1
    salary_index = vessel_params.get("salary_index", 0.5)
    rest_days_ratio = vessel_params.get("rest_days_ratio", 0.5)
    private_cabin = vessel_params.get("private_cabin_ratio", 0.5)

    r_yacht = (salary_index * 0.40) + (rest_days_ratio * 0.35) + (private_cabin * 0.25)

    # Demandes du yacht (D_yacht) — normalisées 0-1
    charter_intensity = vessel_params.get("charter_intensity", 0.5)
    management_pressure = vessel_params.get("management_pressure", 0.5)

    d_yacht = (charter_intensity * 0.60) + (management_pressure * 0.40)
    d_yacht = max(d_yacht, 0.01)  # éviter division par zéro

    # Résilience individuelle (0-100 → normalisée 0-1)
    resilience_norm = candidate_inputs.get("resilience", 50) / 100

    # Ratio JD-R × Résilience → score 0-100
    jdr_ratio = min(r_yacht / d_yacht, 2.0)  # cap à 2x pour éviter les outliers
    f_env = (jdr_ratio / 2.0) * resilience_norm * 100

    return round(max(0.0, min(100.0, f_env)), 1)


# ─────────────────────────────────────────────
# F_lmx : Compatibilité Leadership (Captain's Shadow)
# F_lmx = 1 - |L_capt - V_crew| / d_max
# ─────────────────────────────────────────────

def compute_f_lmx(
    candidate_inputs: Dict,
    captain_vector: Dict,
) -> float:
    """
    Distance vectorielle entre le style du capitaine et les préférences du candidat.
    Plus la distance est faible, plus la compatibilité est élevée.

    Args:
        candidate_inputs: extrait de extract_engine_inputs(snapshot)
        captain_vector: depuis Yacht.captain_leadership_vector
                        {"autonomy_given": 0.6, "feedback_style": 0.4, "structure_imposed": 0.7}
    """
    # Vecteur candidat (préférences)
    v_crew = np.array([
        candidate_inputs.get("autonomy_preference", 0.5),
        candidate_inputs.get("feedback_preference", 0.5),
        candidate_inputs.get("structure_preference", 0.5),
    ])

    # Vecteur capitaine (style de commandement)
    l_capt = np.array([
        captain_vector.get("autonomy_given", 0.5),
        captain_vector.get("feedback_style", 0.5),
        captain_vector.get("structure_imposed", 0.5),
    ])

    # Distance euclidienne normalisée
    d_max = np.sqrt(3)  # distance max possible dans un espace [0,1]^3
    distance = np.linalg.norm(l_capt - v_crew)

    f_lmx = (1 - (distance / d_max)) * 100
    return round(max(0.0, min(100.0, f_lmx)), 1)


# ─────────────────────────────────────────────
# ÉQUATION MAÎTRESSE
# ─────────────────────────────────────────────

def compute_y_success(
    candidate_snapshot: Dict,
    current_crew_snapshots: List[Dict],
    vessel_params: Dict,
    captain_vector: Dict,
    betas: Optional[Dict] = None,
) -> RecruitmentScore:
    """
    Calcule le score de succès prédit pour un candidat sur un yacht donné.

    Cette fonction est le point d'entrée unique de l'engine de recrutement.
    Toutes les données doivent être hydratées en amont par le service.

    Args:
        candidate_snapshot: psychometric_snapshot du candidat
        current_crew_snapshots: liste des snapshots de l'équipe actuelle
        vessel_params: paramètres JD-R du yacht (depuis vessel_snapshot)
        captain_vector: vecteur de leadership du capitaine
        betas: betas du ModelVersion actif (DEFAULT_BETAS si None)
    """
    from engine.psychometrics.snapshot import extract_engine_inputs
    from engine.team.harmony import compute as compute_harmony

    betas = betas or DEFAULT_BETAS

    candidate_inputs = extract_engine_inputs(candidate_snapshot)

    # 1. P_ind
    p_ind = compute_p_ind(candidate_inputs)

    # 2. F_team — avec le candidat intégré à l'équipe
    all_snapshots = current_crew_snapshots + [candidate_snapshot]
    harmony_result = compute_harmony(all_snapshots)
    f_team = compute_f_team(harmony_result)

    # 3. F_env
    f_env = compute_f_env(candidate_inputs, vessel_params)

    # 4. F_lmx
    f_lmx = compute_f_lmx(candidate_inputs, captain_vector)

    # 5. Équation maîtresse
    y_success = (
        betas["b1_p_ind"] * p_ind
        + betas["b2_f_team"] * f_team
        + betas["b3_f_env"] * f_env
        + betas["b4_f_lmx"] * f_lmx
    )

    return RecruitmentScore(
        y_success=round(max(0.0, min(100.0, y_success)), 1),
        p_ind=p_ind,
        f_team=f_team,
        f_env=f_env,
        f_lmx=f_lmx,
        betas_used=betas,
        completeness=candidate_inputs.get("completeness", 0),
    )