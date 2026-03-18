# engine/recruitment/pe_fit/po_fit/weights.py
"""
Constantes de pondération pour F_env (Person-Organization Fit).

Extraites de MLPSM/f_env.py — aucune modification des valeurs originales.
validate_weights() vérifie la cohérence de chaque groupe à l'import.
"""
from app.engine.pe_fit.weight_schema import validate_weights

# ── Pondérations des ressources yacht (R_yacht) ───────────────────────────────
W_SALARY_INDEX    = 0.40   # Rémunération — prédicteur engagement le plus fort
W_REST_DAYS_RATIO = 0.35   # Jours de repos — critique pour le burnout marin
W_PRIVATE_CABIN   = 0.25   # Espace privé — essentiel en isolement prolongé

# ── Pondérations des demandes yacht (D_yacht) ─────────────────────────────────
W_CHARTER_INTENSITY    = 0.60   # Intensité charters — charge opérationnelle principale
W_MANAGEMENT_PRESSURE  = 0.40  # Pression management — charge émotionnelle / relationnelle

# ── Seuils d'alerte ───────────────────────────────────────────────────────────
JDR_RATIO_CAP            = 2.0
BURNOUT_RISK_THRESHOLD   = 0.40
COMFORT_THRESHOLD        = 1.50
RESILIENCE_LOW_THRESHOLD = 40.0

# ── Validation à l'import ─────────────────────────────────────────────────────
validate_weights({
    "salary_index":    W_SALARY_INDEX,
    "rest_days_ratio": W_REST_DAYS_RATIO,
    "private_cabin":   W_PRIVATE_CABIN,
})

validate_weights({
    "charter_intensity":   W_CHARTER_INTENSITY,
    "management_pressure": W_MANAGEMENT_PRESSURE,
})
