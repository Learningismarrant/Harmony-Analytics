# app/seed/surveys/pulses.py
"""
Seed des DailyPulses (~120 entrées).

    seed_pulses(db)   → génère les pulses journaliers par marin
    delete_pulses(db) → supprime tous les DailyPulses

Prérequis : seed_candidates, seed_yachts exécutés.

Standalone :
    python -m app.seed.surveys.pulses
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import User, CrewProfile, Yacht, DailyPulse
from app.seed.environment.snapshots import PULSE_PATTERNS, _now

random.seed(42)

def _ago(days: int, hours: int = 0) -> datetime:
    return _now() - timedelta(days=days, hours=hours)


# (profile_key, yacht_name, n_days, skip_days)
PULSE_SCHEDULE = [
    ("marcus_webb",    "Lady Aurora",  30, {5, 12, 20}),
    ("sofia_reyes",    "Lady Aurora",  30, {3, 11, 25}),
    ("niko_papadis",   "Lady Aurora",  28, {7, 15}),
    ("emma_larsen",    "Lady Aurora",  27, {2, 18, 26}),
    ("isabelle_moreau","Nomad Spirit", 20, {4, 13}),
    ("jake_torres",    "Nomad Spirit", 18, {1, 9, 16}),
    ("lena_kovacs",    "Nomad Spirit", 15, {5, 12}),
    ("mei_zhang",      "Stella Maris", 15, {3}),
    ("ryan_okafor",    "Stella Maris", 14, {7}),
    ("clara_dumont",   "Stella Maris", 13, set()),
    ("dimitri_volkov", "Blue Horizon", 10, {4, 8}),
]


async def seed_pulses(db: AsyncSession) -> None:
    print("  [pulses] Seeding...")

    r = await db.execute(select(CrewProfile, User).join(User, User.id == CrewProfile.user_id))
    profiles = {u.email.split("@")[0].replace(".", "_"): cp for cp, u in r.all()}

    r = await db.execute(select(Yacht))
    yachts = {y.name: y for y in r.scalars().all()}

    n_pulses = 0
    for key, yacht_name, n_days, skip in PULSE_SCHEDULE:
        cp    = profiles.get(key)
        yacht = yachts.get(yacht_name)
        if not cp or not yacht:
            continue

        mean, std = PULSE_PATTERNS.get(key, (3.5, 0.7))

        for day_offset in range(1, n_days + 1):
            if day_offset in skip:
                continue

            score = max(1, min(5, round(random.gauss(mean, std))))

            comment = None
            if score <= 2:
                comment = random.choice([
                    "Journée difficile, fatigue accumulée.",
                    "Tensions ressenties à bord.",
                    "Pas au mieux de ma forme.",
                ])
            elif score == 5 and random.random() < 0.3:
                comment = random.choice([
                    "Excellente journée, super ambiance.",
                    "Tout s'est très bien passé aujourd'hui.",
                ])

            db.add(DailyPulse(
                crew_profile_id=cp.id,
                yacht_id=yacht.id,
                score=score,
                comment=comment,
                created_at=_ago(n_days - day_offset, hours=random.randint(0, 8)),
            ))
            n_pulses += 1

    await db.flush()
    print(f"  [pulses] {n_pulses} pulses créés")


async def delete_pulses(db: AsyncSession) -> None:
    print("  [pulses] Deleting...")
    await db.execute(delete(DailyPulse))
    await db.commit()
    print("  [pulses] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_pulses(db)
        await seed_pulses(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
