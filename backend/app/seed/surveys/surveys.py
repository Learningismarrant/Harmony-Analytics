# app/seed/surveys/surveys.py
"""
Seed des surveys et SurveyResponses.

    seed_surveys(db)   → insère 3 surveys + 6 réponses
    delete_surveys(db) → supprime SurveyResponses + Surveys

Prérequis : seed_candidates, seed_yachts exécutés.

Standalone :
    python -m app.seed.surveys.surveys
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import (
    User, CrewProfile, Yacht, Survey, SurveyResponse,
)
from app.seed.environment.snapshots import (
    BIG_FIVE_SCORES_BY_PROFILE, GCA_CORRECT_BY_PROFILE, _now,
)

random.seed(42)

def _ago(days: int) -> datetime: return _now() - timedelta(days=days)


def _survey_response_scores(profile_key: str, trigger_type: str) -> dict:
    """Génère des scores cohérents avec le profil Big Five du marin."""
    bf  = BIG_FIVE_SCORES_BY_PROFILE[profile_key]
    es  = 100 - bf["neuroticism"]
    a   = bf["agreeableness"]
    c   = bf["conscientiousness"]
    gca = GCA_CORRECT_BY_PROFILE.get(profile_key, 10) / 20 * 100

    def _jitter(base: float, scale: float = 8.0) -> float:
        return round(max(0.0, min(100.0, base + random.gauss(0, scale))), 1)

    team_cohesion  = _jitter((a * 0.5 + es * 0.5))
    workload_felt  = _jitter(100 - (es * 0.4 + c * 0.3 + 30), scale=10)
    leadership_fit = _jitter((es * 0.45 + a * 0.35 + c * 0.2))
    perf_self      = _jitter((c * 0.5 + gca * 0.3 + es * 0.2))

    raw_intent = (es * 0.35 + a * 0.25 + c * 0.20 + (100 - workload_felt) * 0.20)
    if trigger_type == "exit_interview":
        raw_intent *= 0.35
    intent_to_stay = _jitter(raw_intent, scale=6.0)

    free_texts = {
        "high":   ["RAS, très satisfait de cette saison.", "Super ambiance à bord, je recommande."],
        "medium": ["Quelques tensions mais globalement positif.", "La charge est parfois lourde mais gérable."],
        "low":    ["Je ressens une fatigue accumulée.", "La communication s'est dégradée ces dernières semaines."],
    }
    bucket = "high" if intent_to_stay >= 70 else ("medium" if intent_to_stay >= 40 else "low")

    return {
        "team_cohesion_observed":      team_cohesion,
        "workload_felt":               workload_felt,
        "leadership_fit_felt":         leadership_fit,
        "individual_performance_self": perf_self,
        "intent_to_stay":              intent_to_stay,
        "free_text":                   random.choice(free_texts[bucket]),
    }


async def seed_surveys(db: AsyncSession) -> dict:
    print("  [surveys] Seeding...")

    # Récupérer profiles + yachts depuis la DB
    r = await db.execute(select(CrewProfile, User).join(User, User.id == CrewProfile.user_id))
    profiles = {u.email.split("@")[0].replace(".", "_"): cp for cp, u in r.all()}

    r = await db.execute(select(Yacht))
    yachts = {y.name: y for y in r.scalars().all()}
    aurora = yachts.get("Lady Aurora")
    nomad  = yachts.get("Nomad Spirit")
    stella = yachts.get("Stella Maris")

    aurora_employer_id = aurora.employer_profile_id if aurora else None
    stella_employer_id = stella.employer_profile_id if stella else None

    aurora_crew_ids = [profiles[k].id for k in ["marcus_webb", "sofia_reyes", "niko_papadis", "emma_larsen"] if k in profiles]
    nomad_crew_ids  = [profiles[k].id for k in ["isabelle_moreau", "jake_torres", "lena_kovacs"] if k in profiles]
    stella_crew_ids = [profiles[k].id for k in ["mei_zhang", "ryan_okafor", "clara_dumont"] if k in profiles]

    # ── Survey 1 — Post-charter Lady Aurora (fermé, 4/4) ──────────────────────
    survey_aurora = Survey(
        yacht_id=aurora.id if aurora else None,
        triggered_by_id=aurora_employer_id,
        title="Post-charter — Lady Aurora / Été 2025",
        trigger_type="post_charter",
        target_crew_ids=aurora_crew_ids,
        is_open=False,
        created_at=_ago(20),
        closed_at=_ago(13),
    )
    db.add(survey_aurora)

    # ── Survey 2 — Monthly pulse Nomad (ouvert, 2/3) ──────────────────────────
    survey_nomad = Survey(
        yacht_id=nomad.id if nomad else None,
        triggered_by_id=aurora_employer_id,
        title="Pulse mensuel — Nomad Spirit / Juillet 2025",
        trigger_type="monthly_pulse",
        target_crew_ids=nomad_crew_ids,
        is_open=True,
        created_at=_ago(5),
        closed_at=None,
    )
    db.add(survey_nomad)

    # ── Survey 3 — Post-charter Stella (ouvert, 0/3) ──────────────────────────
    survey_stella = Survey(
        yacht_id=stella.id if stella else None,
        triggered_by_id=stella_employer_id,
        title="Post-charter — Stella Maris / Juillet 2025",
        trigger_type="post_charter",
        target_crew_ids=stella_crew_ids,
        is_open=True,
        created_at=_ago(2),
        closed_at=None,
    )
    db.add(survey_stella)
    await db.flush()

    # ── SurveyResponses ───────────────────────────────────────────────────────
    n_responses = 0

    for key, days_offset in [("marcus_webb", 19), ("sofia_reyes", 18), ("niko_papadis", 17), ("emma_larsen", 16)]:
        cp = profiles.get(key)
        if not cp:
            continue
        scores = _survey_response_scores(key, "post_charter")
        db.add(SurveyResponse(
            survey_id=survey_aurora.id,
            crew_profile_id=cp.id,
            yacht_id=aurora.id,
            trigger_type="post_charter",
            team_cohesion_observed=      scores["team_cohesion_observed"],
            workload_felt=               scores["workload_felt"],
            leadership_fit_felt=         scores["leadership_fit_felt"],
            individual_performance_self= scores["individual_performance_self"],
            intent_to_stay=              scores["intent_to_stay"],
            free_text=                   scores["free_text"],
            submitted_at=_ago(days_offset),
        ))
        n_responses += 1

    for key, days_offset in [("isabelle_moreau", 4), ("jake_torres", 3)]:
        cp = profiles.get(key)
        if not cp:
            continue
        scores = _survey_response_scores(key, "monthly_pulse")
        db.add(SurveyResponse(
            survey_id=survey_nomad.id,
            crew_profile_id=cp.id,
            yacht_id=nomad.id,
            trigger_type="monthly_pulse",
            team_cohesion_observed=      scores["team_cohesion_observed"],
            workload_felt=               scores["workload_felt"],
            leadership_fit_felt=         scores["leadership_fit_felt"],
            individual_performance_self= scores["individual_performance_self"],
            intent_to_stay=              scores["intent_to_stay"],
            free_text=                   scores["free_text"],
            submitted_at=_ago(days_offset),
        ))
        n_responses += 1

    await db.flush()
    print(f"  [surveys] 3 surveys, {n_responses} réponses créées")
    return {"aurora": survey_aurora, "nomad": survey_nomad, "stella": survey_stella}


async def delete_surveys(db: AsyncSession) -> None:
    print("  [surveys] Deleting...")
    await db.execute(delete(SurveyResponse))
    await db.execute(delete(Survey))
    await db.commit()
    print("  [surveys] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_surveys(db)
        await seed_surveys(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
