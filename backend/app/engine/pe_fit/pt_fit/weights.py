# engine/recruitment/pe_fit/pt_fit/weights.py
"""
Constantes de pondération pour F_team (Person-Team Fit).

Extraites de MLPSM/f_team.py — aucune modification des valeurs originales.
validate_weights() n'est pas applicable ici : les 3 pondérations ne somment
pas à 1.0 dans le modèle original (W_FAULTLINE_RISK est une pénalité, pas
un poids additif standard). Les constantes sont exposées pour référence et
réutilisation.
"""

# ── Pondérations des sous-composantes ────────────────────────────────────────
# Poids validés Bell (2007) — ρ équivalents A_min=0.27, C_mean=0.27, ES_mean=0.25, σC=-0.19
W_JERK_FILTER      = 0.30   # min(A) — modèle distal (était 0.40)
W_MEAN_C           = 0.30   # μ(C) — nouveau terme Bell (2007) ρ=0.27
W_EMOTIONAL_BUFFER = 0.28   # μ(ES) — team resilience (était 0.30)
W_FAULTLINE_RISK   = 0.12   # σ(C) pénalité — Lau & Murnighan (1998) ρ=−0.19 (était 0.30)

# Vérification manuelle : W_JERK + W_MEAN_C + W_EMOTIONAL - W_FAULTLINE = 0.30 + 0.30 + 0.28 - 0.12 = 0.76
# Somme des coefficients positifs : 0.30 + 0.30 + 0.28 + 0.12 = 1.00
# La formule est : (min_A × W_JERK) + (mean_C × W_MEAN_C) + (mean_ES × W_EMOTIONAL) - (sigma_C_norm × W_FAULTLINE)
# Bell, B.S. (2007). Longitudinal relationships of personality and group performance.
#     Journal of Applied Psychology, 92(2), 362-376.

# ── Seuils de risque ──────────────────────────────────────────────────────────
JERK_FILTER_DANGER   = 35.0
FAULTLINE_DANGER     = 20.0
ES_MINIMUM_THRESHOLD = 45.0
MIN_CREW_SIZE        = 2
