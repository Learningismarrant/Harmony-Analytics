# app/seed/environment/candidates.py
"""
Seed des candidats (Users CANDIDATE + CrewProfile + psychometric_snapshot).

    seed_candidates(db)   → insère 15 profils, retourne {"marcus_webb": CrewProfile, ...}
    delete_candidates(db) → supprime toutes les données dépendantes + profils candidats

Standalone :
    python -m app.seed.environment.candidates
"""
import asyncio
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import (
    User, CrewProfile, CrewAssignment,
    TestResult, DailyPulse, SurveyResponse, CampaignCandidate,
)
from app.shared.enums import UserRole, YachtPosition, AvailabilityStatus
from app.seed.environment.snapshots import SNAPSHOTS, _now

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash(p: str) -> str: return _pwd.hash(p)
def _ago(days: int) -> datetime: return _now() - timedelta(days=days)


CREW_DATA = [
    # (key, email, name, location, position, exp_years)
    # ── Lady Aurora ──
    ("marcus_webb",     "marcus.webb@gmail.com",     "Marcus Webb",     "UK",      "Captain",        18),
    ("sofia_reyes",     "sofia.reyes@gmail.com",     "Sofia Reyes",     "Spain",   "First Mate",      9),
    ("niko_papadis",    "niko.papadis@gmail.com",    "Niko Papadis",    "Greece",  "Chef",             7),
    ("emma_larsen",     "emma.larsen@gmail.com",     "Emma Larsen",     "Denmark", "Stewardess",       4),
    # ── Nomad Spirit ──
    ("isabelle_moreau", "isabelle.moreau@gmail.com", "Isabelle Moreau", "France",  "First Mate",      11),
    ("jake_torres",     "jake.torres@gmail.com",     "Jake Torres",     "USA",     "Chief Engineer",   6),
    ("lena_kovacs",     "lena.kovacs@gmail.com",     "Lena Kovacs",     "Hungary", "Deckhand",         2),
    # ── Stella Maris ──
    ("mei_zhang",       "mei.zhang@gmail.com",       "Mei Zhang",       "China",   "Stewardess",       5),
    ("ryan_okafor",     "ryan.okafor@gmail.com",     "Ryan Okafor",     "Nigeria", "Bosun",            4),
    ("clara_dumont",    "clara.dumont@gmail.com",    "Clara Dumont",    "France",  "Stewardess",       3),
    # ── Blue Horizon ──
    ("dimitri_volkov",  "dimitri.volkov@gmail.com",  "Dimitri Volkov",  "Russia",  "Deckhand",         2),
    # ── Non assignés ──
    ("sam_adler",       "sam.adler@gmail.com",       "Sam Adler",       "USA",     "Deckhand",         1),
    ("tom_bradley",     "tom.bradley@gmail.com",     "Tom Bradley",     "UK",      "First Mate",      12),
    ("aisha_nkosi",     "aisha.nkosi@gmail.com",     "Aisha Nkosi",     "Kenya",   "Captain",         14),
    ("carlos_mendez",   "carlos.mendez@gmail.com",   "Carlos Mendez",   "Mexico",  "Deckhand",         1),
]


async def seed_candidates(db: AsyncSession) -> dict:
    print("  [candidates] Seeding...")
    crew_profiles: dict = {}

    for key, email, name, location, position, exp_years in CREW_DATA:
        u = User(
            email=email,
            name=name,
            hashed_password=_hash("testpassword123"),
            role=UserRole.CANDIDATE,
            is_active=True,
            location=location,
            avatar_url=f"https://i.pravatar.cc/150?u={email}",
            is_harmony_verified=True,
            created_at=_ago(40),
        )
        db.add(u)
        await db.flush()

        cp = CrewProfile(
            user_id=u.id,
            position_targeted=YachtPosition(position),
            experience_years=exp_years,
            availability_status=AvailabilityStatus.AVAILABLE,
            psychometric_snapshot=SNAPSHOTS[key],
            snapshot_updated_at=_now(),
        )
        db.add(cp)
        await db.flush()
        crew_profiles[key] = cp

    print(f"  [candidates] {len(crew_profiles)} profils créés")
    return crew_profiles


async def delete_candidates(db: AsyncSession) -> None:
    """Supprime les candidats et toutes leurs données dépendantes."""
    print("  [candidates] Deleting...")

    result = await db.execute(select(User.id).where(User.role == UserRole.CANDIDATE))
    user_ids = [r[0] for r in result.all()]
    if not user_ids:
        print("  [candidates] Nothing to delete.")
        return

    result = await db.execute(
        select(CrewProfile.id).where(CrewProfile.user_id.in_(user_ids))
    )
    cp_ids = [r[0] for r in result.all()]

    if cp_ids:
        await db.execute(delete(DailyPulse).where(DailyPulse.crew_profile_id.in_(cp_ids)))
        await db.execute(delete(SurveyResponse).where(SurveyResponse.crew_profile_id.in_(cp_ids)))
        await db.execute(delete(TestResult).where(TestResult.crew_profile_id.in_(cp_ids)))
        await db.execute(delete(CrewAssignment).where(CrewAssignment.crew_profile_id.in_(cp_ids)))
        await db.execute(delete(CampaignCandidate).where(CampaignCandidate.crew_profile_id.in_(cp_ids)))
        await db.execute(delete(CrewProfile).where(CrewProfile.id.in_(cp_ids)))

    await db.execute(delete(User).where(User.id.in_(user_ids)))
    await db.commit()
    print("  [candidates] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_candidates(db)
        await seed_candidates(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
