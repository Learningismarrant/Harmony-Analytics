# app/seed/environment/snapshots.py
"""
Données statiques partagées entre les modules de seed.

Importé par :
    environment/candidates.py  → SNAPSHOTS (psychometric_snapshot)
    environment/yachts.py      → SNAPSHOTS + _vessel_snapshot (vessel_snapshot)
    tests/results.py           → BIG_FIVE_SCORES_BY_PROFILE, GCA_CORRECT_BY_PROFILE
    surveys/surveys.py         → BIG_FIVE_SCORES_BY_PROFILE, GCA_CORRECT_BY_PROFILE
    surveys/pulses.py          → PULSE_PATTERNS
"""
from datetime import datetime, timezone, timedelta


def _now() -> datetime:
    return datetime.now(timezone.utc)

def _ago(days: int, hours: int = 0) -> datetime:
    return _now() - timedelta(days=days, hours=hours)


# ── Helpers psychométriques ────────────────────────────────────────────────────

def _snapshot(
    agreeableness: float,
    conscientiousness: float,
    neuroticism: float,
    openness: float,
    extraversion: float,
    gca: float,
    resilience: float,
    autonomy: float = 0.5,
    feedback: float = 0.5,
    structure: float = 0.6,
    motivation: dict = None,
) -> dict:
    es = round(100.0 - neuroticism, 1)

    # Dériver les scores de motivation depuis le Big Five si non fournis
    if motivation is None:
        intrinsic        = min(100.0, max(0.0, openness * 0.8 + conscientiousness * 0.2))
        identified       = min(100.0, max(0.0, conscientiousness * 0.7 + (100 - neuroticism) * 0.3))
        introjected      = min(100.0, max(0.0, neuroticism * 0.6 + (100 - agreeableness) * 0.4))
        extrinsic_social = min(100.0, max(0.0, extraversion * 0.7 + agreeableness * 0.3))
        extrinsic_material = min(100.0, max(0.0, 50 + (100 - conscientiousness) * 0.2))
        amotivation      = min(100.0, max(0.0, neuroticism * 0.5))
        motivation = {
            "intrinsic":          round(intrinsic, 1),
            "identified":         round(identified, 1),
            "introjected":        round(introjected, 1),
            "extrinsic_social":   round(extrinsic_social, 1),
            "extrinsic_material": round(extrinsic_material, 1),
            "amotivation":        round(amotivation, 1),
        }

    return {
        "version": "2.0",
        "big_five": {
            "agreeableness":     {"score": agreeableness, "reliable": True},
            "conscientiousness": {"score": conscientiousness, "reliable": True},
            "neuroticism":       {"score": neuroticism, "reliable": True},
            "openness":          {"score": openness, "reliable": True},
            "extraversion":      {"score": extraversion, "reliable": True},
        },
        "emotional_stability": es,
        "cognitive": {
            "gca_score": gca,
            "n_tests": 2,
        },
        "resilience": resilience,
        "leadership_preferences": {
            "autonomy_preference": autonomy,
            "feedback_preference": feedback,
            "structure_preference": structure,
        },
        "motivation": motivation,
        "onboarding_tips": {
            "first_week": ["Observer la dynamique avant d'initier des changements."],
            "month_1": ["Développer des routines de communication claire."],
        },
        "integration_risks": [],
        "management_advice": {},
        "test_history": [],
    }


def _vessel_snapshot(
    crew_snapshots: list,
    salary_index: float = 0.70,
    rest_days_ratio: float = 0.55,
    private_cabin_ratio: float = 0.80,
    charter_intensity: float = 0.60,
    management_pressure: float = 0.55,
    captain_autonomy: float = 0.5,
    captain_feedback: float = 0.6,
    captain_structure: float = 0.7,
) -> dict:
    return {
        "crew_count": len(crew_snapshots),
        "vessel_params": {
            "salary_index":        salary_index,
            "rest_days_ratio":     rest_days_ratio,
            "private_cabin_ratio": private_cabin_ratio,
            "charter_intensity":   charter_intensity,
            "management_pressure": management_pressure,
        },
        "captain_vector": {
            "autonomy_given":     captain_autonomy,
            "feedback_style":     captain_feedback,
            "structure_imposed":  captain_structure,
        },
        # Rétrocompat : ancien format conservé pour les consommateurs existants
        "captain_leadership_vector": {
            "autonomy_given":     captain_autonomy,
            "feedback_style":     captain_feedback,
            "structure_imposed":  captain_structure,
        },
        "harmony_result": {
            "performance": 72.0,
            "cohesion": 68.0,
            "risk_factors": {
                "conscientiousness_divergence": 9.2,
                "weakest_link_stability": 44.0,
            }
        },
        "f_team_baseline_score": 72.0,
        "f_team_data_quality": 1.0,
        "f_team_flags": [],
    }


# ── Profils psychométriques ────────────────────────────────────────────────────

SNAPSHOTS = {
    # ── ELITE ─────────────────────────────────────────────────────────────────
    "marcus_webb": _snapshot(
        agreeableness=72, conscientiousness=82, neuroticism=22,
        openness=68, extraversion=74, gca=80, resilience=78,
        autonomy=0.7, feedback=0.4, structure=0.8,
    ),
    "isabelle_moreau": _snapshot(
        agreeableness=70, conscientiousness=85, neuroticism=25,
        openness=72, extraversion=66, gca=77, resilience=76,
        autonomy=0.65, feedback=0.55, structure=0.75,
    ),
    "tom_bradley": _snapshot(
        agreeableness=74, conscientiousness=81, neuroticism=21,
        openness=70, extraversion=71, gca=78, resilience=80,
        autonomy=0.68, feedback=0.52, structure=0.78,
    ),

    # ── GOOD_FIT ──────────────────────────────────────────────────────────────
    "sofia_reyes": _snapshot(
        agreeableness=68, conscientiousness=79, neuroticism=29,
        openness=65, extraversion=60, gca=74, resilience=71,
        autonomy=0.6, feedback=0.5, structure=0.7,
    ),
    "emma_larsen": _snapshot(
        agreeableness=80, conscientiousness=68, neuroticism=34,
        openness=74, extraversion=78, gca=58, resilience=66,
        autonomy=0.4, feedback=0.65, structure=0.55,
    ),
    "mei_zhang": _snapshot(
        agreeableness=76, conscientiousness=65, neuroticism=31,
        openness=71, extraversion=69, gca=61, resilience=69,
        autonomy=0.5, feedback=0.6, structure=0.6,
    ),
    "clara_dumont": _snapshot(
        agreeableness=82, conscientiousness=62, neuroticism=27,
        openness=68, extraversion=76, gca=56, resilience=73,
        autonomy=0.45, feedback=0.7, structure=0.5,
    ),
    "aisha_nkosi": _snapshot(
        agreeableness=66, conscientiousness=77, neuroticism=32,
        openness=74, extraversion=62, gca=75, resilience=70,
        autonomy=0.62, feedback=0.48, structure=0.72,
    ),

    # ── MODERATE ──────────────────────────────────────────────────────────────
    "niko_papadis": _snapshot(
        agreeableness=74, conscientiousness=71, neuroticism=38,
        openness=62, extraversion=58, gca=65, resilience=62,
        autonomy=0.55, feedback=0.5, structure=0.65,
    ),
    "jake_torres": _snapshot(
        agreeableness=58, conscientiousness=73, neuroticism=45,
        openness=60, extraversion=52, gca=70, resilience=55,
        autonomy=0.6, feedback=0.45, structure=0.7,
    ),
    "lena_kovacs": _snapshot(
        agreeableness=62, conscientiousness=60, neuroticism=52,
        openness=58, extraversion=61, gca=52, resilience=50,
        autonomy=0.5, feedback=0.5, structure=0.55,
    ),
    "ryan_okafor": _snapshot(
        agreeableness=52, conscientiousness=64, neuroticism=56,
        openness=55, extraversion=55, gca=55, resilience=48,
        autonomy=0.5, feedback=0.55, structure=0.6,
    ),

    # ── HIGH_RISK (ES soft veto : 15-30) ──────────────────────────────────────
    "dimitri_volkov": _snapshot(
        agreeableness=35, conscientiousness=55, neuroticism=78,
        openness=45, extraversion=48, gca=48, resilience=28,
        autonomy=0.7, feedback=0.3, structure=0.4,
    ),
    "carlos_mendez": _snapshot(
        agreeableness=40, conscientiousness=52, neuroticism=82,
        openness=42, extraversion=44, gca=49, resilience=24,
        autonomy=0.65, feedback=0.35, structure=0.45,
    ),

    # ── DISQUALIFIED (ES hard veto : < 15) ────────────────────────────────────
    "sam_adler": _snapshot(
        agreeableness=45, conscientiousness=50, neuroticism=90,
        openness=40, extraversion=42, gca=44, resilience=15,
        autonomy=0.6, feedback=0.4, structure=0.5,
    ),
}


# ── Données par profil (pour seeds surveys / résultats) ───────────────────────

BIG_FIVE_SCORES_BY_PROFILE = {
    "marcus_webb":     {"agreeableness": 72, "conscientiousness": 82, "neuroticism": 22, "openness": 68, "extraversion": 74},
    "isabelle_moreau": {"agreeableness": 70, "conscientiousness": 85, "neuroticism": 25, "openness": 72, "extraversion": 66},
    "tom_bradley":     {"agreeableness": 74, "conscientiousness": 81, "neuroticism": 21, "openness": 70, "extraversion": 71},
    "sofia_reyes":     {"agreeableness": 68, "conscientiousness": 79, "neuroticism": 29, "openness": 65, "extraversion": 60},
    "emma_larsen":     {"agreeableness": 80, "conscientiousness": 68, "neuroticism": 34, "openness": 74, "extraversion": 78},
    "mei_zhang":       {"agreeableness": 76, "conscientiousness": 65, "neuroticism": 31, "openness": 71, "extraversion": 69},
    "clara_dumont":    {"agreeableness": 82, "conscientiousness": 62, "neuroticism": 27, "openness": 68, "extraversion": 76},
    "aisha_nkosi":     {"agreeableness": 66, "conscientiousness": 77, "neuroticism": 32, "openness": 74, "extraversion": 62},
    "niko_papadis":    {"agreeableness": 74, "conscientiousness": 71, "neuroticism": 38, "openness": 62, "extraversion": 58},
    "jake_torres":     {"agreeableness": 58, "conscientiousness": 73, "neuroticism": 45, "openness": 60, "extraversion": 52},
    "lena_kovacs":     {"agreeableness": 62, "conscientiousness": 60, "neuroticism": 52, "openness": 58, "extraversion": 61},
    "ryan_okafor":     {"agreeableness": 52, "conscientiousness": 64, "neuroticism": 56, "openness": 55, "extraversion": 55},
    "dimitri_volkov":  {"agreeableness": 35, "conscientiousness": 55, "neuroticism": 78, "openness": 45, "extraversion": 48},
    "carlos_mendez":   {"agreeableness": 40, "conscientiousness": 52, "neuroticism": 82, "openness": 42, "extraversion": 44},
    "sam_adler":       {"agreeableness": 45, "conscientiousness": 50, "neuroticism": 90, "openness": 40, "extraversion": 42},
}

GCA_CORRECT_BY_PROFILE = {
    "marcus_webb":    17,
    "isabelle_moreau": 16,
    "tom_bradley":    16,
    "sofia_reyes":    15,
    "emma_larsen":    12,
    "mei_zhang":      13,
    "clara_dumont":   11,
    "aisha_nkosi":    15,
    "niko_papadis":   13,
    "jake_torres":    14,
    "lena_kovacs":    11,
    "ryan_okafor":    11,
    "dimitri_volkov":  9,
    "carlos_mendez":  10,
    "sam_adler":       9,
}

PULSE_PATTERNS = {
    # Lady Aurora — équipe ELITE, scores hauts, faible variance
    "marcus_webb":     (4.4, 0.4),
    "sofia_reyes":     (4.2, 0.5),
    "niko_papadis":    (3.8, 0.7),
    "emma_larsen":     (4.1, 0.5),
    # Nomad Spirit — équipe mixte, quelques tensions
    "isabelle_moreau": (4.0, 0.6),
    "jake_torres":     (3.2, 1.0),
    "lena_kovacs":     (3.0, 1.1),
    # Stella Maris — profils moyens
    "mei_zhang":       (3.7, 0.6),
    "ryan_okafor":     (3.2, 0.9),
    "clara_dumont":    (3.9, 0.5),
    # Blue Horizon — Dimitri HIGH_RISK, scores bas et volatils
    "dimitri_volkov":  (2.4, 1.2),
}
