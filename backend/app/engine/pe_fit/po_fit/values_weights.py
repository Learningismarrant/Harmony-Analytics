# pe_fit/po_fit/values_weights.py
"""
Pondérations du PO fit par congruence de valeurs (CES).

Famille 3 — PO fit (document de référence §2.2, §6.4)
    3.1.a  Honnêteté / transparence    ÉLEVÉE  0.25
    3.1.b  Accomplissement             ÉLEVÉE  0.25
    3.1.c  Équité                      ÉLEVÉE  0.25
    3.1.d  Entraide / solidarité       ÉLEVÉE  0.25

Les 4 valeurs CES sont équipondérées — la littérature (Ravlin & Meglino, 1987)
ne hiérarchise pas ces valeurs de travail fondamentales.

Sources :
    Document de référence Harmony Analytics v0.7, §3.1 (Famille 3 — PO fit)
    Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception.
        Journal of Applied Psychology, 72, 666–673.
"""

# Pondérations intra-famille 3 (somme = 1.0)
W_HONESTY:      float = 0.25
"""3.1.a — Honnêteté et transparence dans les relations de travail."""

W_ACHIEVEMENT:  float = 0.25
"""3.1.b — Accomplissement par le travail bien fait."""

W_FAIRNESS:     float = 0.25
"""3.1.c — Équité dans le traitement des collaborateurs."""

W_SOLIDARITY:   float = 0.25
"""3.1.d — Entraide et solidarité entre collègues."""

# Seuil d'alerte
LOW_VALUES_ALIGNMENT_THRESHOLD: float = 0.40
"""
Seuil sous lequel un PSI de valeur est signalé comme désalignement fort.
score_dim < 0.40 → alerte valeurs (delta P/E > 60% de l'échelle).
"""
