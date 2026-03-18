# engine/recruitment/pe_fit/ps_fit/weights.py
"""
Constantes de pondération pour F_lmx (Person-Supervisor Fit).

Extraites de MLPSM/f_lmx.py — aucune modification des valeurs originales.
Les 3 dimensions ont un poids uniforme de 1/3 chacune (Temps 1).
validate_weights() vérifie la somme à l'import.
"""
import math
from app.engine.pe_fit.weight_schema import validate_weights

# ── Pondérations des dimensions du vecteur leadership ─────────────────────────
W_AUTONOMY   = 1.0 / 3.0
W_FEEDBACK   = 1.0 / 3.0
W_STRUCTURE  = 1.0 / 3.0

# Distance maximale dans un espace [0,1]³ pondéré uniformément
D_MAX_UNIFORM = math.sqrt(3)

# ── Seuils d'alerte ───────────────────────────────────────────────────────────
CRITICAL_DISTANCE_THRESHOLD = 0.70
HIGH_DISTANCE_THRESHOLD     = 0.50
LOW_DATA_THRESHOLD          = 0.50

# ── Validation à l'import ─────────────────────────────────────────────────────
validate_weights({
    "autonomy":  W_AUTONOMY,
    "feedback":  W_FEEDBACK,
    "structure": W_STRUCTURE,
})
