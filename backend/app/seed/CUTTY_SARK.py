# app/seed/CUTTY_SARK.py
"""
Point d'entrée pour le seed du test CUTTY SARK T-IRT.

Les données (60 paires IPIP-120 maritime) et la fonction de seed
sont définies dans HEXACO.py.

Appelé depuis seed_tests_surveys.py :
    from app.seed.CUTTY_SARK import seed_cutty_sark
"""
from app.seed.HEXACO import seed_cutty_sark  # noqa: F401
