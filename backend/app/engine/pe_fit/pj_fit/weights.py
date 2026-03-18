# engine/recruitment/pe_fit/pj_fit/weights.py
"""
Poids SME par défaut pour le PJ-Fit (C1 : Individual Performance).

Ces poids sont extraits de DEFAULT_SME_WEIGHTS[C1_individual_performance]
de DNRE/sme_score.py. Ils correspondent aux priors Phase 0 du panel SME
maritime, calibrés d'après Schmidt & Hunter (1998) et Sackett et al. (2022).

    GCA (0.60)           : prédicteur le plus robuste de la performance (ρ ≈ 0.51)
    Conscientiousness (0.40) : seul trait Big Five universellement prédictif (ρ ≈ 0.31)

Source : Schmidt, F.L. & Hunter, J.E. (1998). The validity and utility of
selection methods. Psychological Bulletin, 124(2).
"""
from __future__ import annotations

from app.engine.pe_fit.weight_schema import validate_weights


DEFAULT_PJ_WEIGHTS: dict[str, float] = {
    "gca":               0.60,
    "conscientiousness": 0.40,
}

# Validation au niveau module — lève ValueError au chargement si invalide
validate_weights(DEFAULT_PJ_WEIGHTS, "pj_fit")
