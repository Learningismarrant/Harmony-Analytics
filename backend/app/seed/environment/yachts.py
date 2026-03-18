# app/seed/environment/yachts.py
"""
Seed des yachts + CrewAssignments.

    seed_yachts(db)   → insère 4 yachts + 11 assignments, retourne dict yachts
    delete_yachts(db) → supprime assignments + yachts (+ données dépendantes)

Prérequis : seed_employers et seed_candidates exécutés.

Standalone :
    python -m app.seed.environment.yachts
"""
import asyncio
import secrets
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import (
    User, EmployerProfile, CrewProfile, Yacht, CrewAssignment,
    DailyPulse, SurveyResponse, Survey, Campaign, CampaignCandidate,
)
from app.shared.enums import UserRole, YachtPosition
from app.seed.environment.snapshots import SNAPSHOTS, _vessel_snapshot, _now

def _ago(days: int) -> datetime: return _now() - timedelta(days=days)


async def seed_yachts(db: AsyncSession) -> dict:
    print("  [yachts] Seeding...")

    # Récupérer les employers depuis la DB
    r = await db.execute(
        select(EmployerProfile, User).join(User, User.id == EmployerProfile.user_id)
    )
    employers = {u.email.split("@")[0].replace(".", "_"): ep for ep, u in r.all()}
    employer_azure   = employers.get("thomas_laurent")
    employer_pacific = employers.get("diana_chen")

    # Récupérer les crew profiles depuis la DB
    r = await db.execute(select(CrewProfile, User).join(User, User.id == CrewProfile.user_id))
    profiles = {
        u.email.split("@")[0].replace(".", "_"): cp
        for cp, u in r.all()
    }

    # ── Yachts ────────────────────────────────────────────────────────────────
    yacht_aurora = Yacht(
        name="Lady Aurora", length=55, type="Motor",
        employer_profile_id=employer_azure.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["marcus_webb"], SNAPSHOTS["sofia_reyes"],
             SNAPSHOTS["niko_papadis"], SNAPSHOTS["emma_larsen"]],
            salary_index=0.85, rest_days_ratio=0.45,
            private_cabin_ratio=1.0, charter_intensity=0.85, management_pressure=0.60,
            captain_autonomy=0.7, captain_feedback=0.4, captain_structure=0.8,
        ),
        captain_leadership_vector={"autonomy_given": 0.7, "feedback_style": 0.4, "structure_imposed": 0.8},
        created_at=_ago(50),
    )
    db.add(yacht_aurora)

    yacht_nomad = Yacht(
        name="Nomad Spirit", length=42, type="Sail",
        employer_profile_id=employer_azure.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["isabelle_moreau"], SNAPSHOTS["jake_torres"], SNAPSHOTS["lena_kovacs"]],
            salary_index=0.75, rest_days_ratio=0.60,
            private_cabin_ratio=0.90, charter_intensity=0.40, management_pressure=0.50,
            captain_autonomy=0.65, captain_feedback=0.55, captain_structure=0.75,
        ),
        captain_leadership_vector={"autonomy_given": 0.3, "feedback_style": 0.6, "structure_imposed": 0.2},
        created_at=_ago(40),
    )
    db.add(yacht_nomad)

    yacht_stella = Yacht(
        name="Stella Maris", length=68, type="Motor",
        employer_profile_id=employer_pacific.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["mei_zhang"], SNAPSHOTS["ryan_okafor"], SNAPSHOTS["clara_dumont"]],
            salary_index=0.65, rest_days_ratio=0.55,
            private_cabin_ratio=0.70, charter_intensity=0.60, management_pressure=0.55,
            captain_autonomy=0.5, captain_feedback=0.6, captain_structure=0.7,
        ),
        captain_leadership_vector={"autonomy_given": 0.3, "feedback_style": 0.6, "structure_imposed": 0.5},
        created_at=_ago(35),
    )
    db.add(yacht_stella)

    yacht_blue = Yacht(
        name="Blue Horizon", length=38, type="Motor",
        employer_profile_id=employer_pacific.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["dimitri_volkov"]],
            salary_index=0.60, rest_days_ratio=0.40,
            private_cabin_ratio=0.60, charter_intensity=0.90, management_pressure=0.70,
        ),
        captain_leadership_vector={"autonomy_given": 0.1, "feedback_style": 0.2, "structure_imposed": 0.1},
        created_at=_ago(20),
    )
    db.add(yacht_blue)
    await db.flush()

    yachts = {
        "aurora": yacht_aurora,
        "nomad":  yacht_nomad,
        "stella": yacht_stella,
        "blue":   yacht_blue,
    }
    print(f"  [yachts] 4 yachts créés: {[y.name for y in yachts.values()]}")

    # ── CrewAssignments ────────────────────────────────────────────────────────
    assignments_data = [
        # Lady Aurora
        ("marcus_webb",    yacht_aurora, "Captain",        45),
        ("sofia_reyes",    yacht_aurora, "First Mate",     40),
        ("niko_papadis",   yacht_aurora, "Chef",           38),
        ("emma_larsen",    yacht_aurora, "Stewardess",     30),
        # Nomad Spirit
        ("isabelle_moreau",yacht_nomad,  "First Mate",     35),
        ("jake_torres",    yacht_nomad,  "Chief Engineer", 32),
        ("lena_kovacs",    yacht_nomad,  "Deckhand",       20),
        # Stella Maris
        ("mei_zhang",      yacht_stella, "Stewardess",     28),
        ("ryan_okafor",    yacht_stella, "Bosun",          25),
        ("clara_dumont",   yacht_stella, "Stewardess",     22),
        # Blue Horizon
        ("dimitri_volkov", yacht_blue,   "Deckhand",       10),
    ]

    for key, yacht, role, days in assignments_data:
        cp = profiles.get(key)
        if not cp:
            continue
        db.add(CrewAssignment(
            crew_profile_id=cp.id,
            yacht_id=yacht.id,
            role=YachtPosition(role),
            is_active=True,
            start_date=_ago(days),
        ))

    await db.flush()
    print(f"  [yachts] {len(assignments_data)} assignments créés")
    return yachts


async def delete_yachts(db: AsyncSession) -> None:
    """Supprime les yachts et toutes leurs données dépendantes."""
    print("  [yachts] Deleting...")
    result = await db.execute(select(Yacht.id))
    yacht_ids = [r[0] for r in result.all()]
    if not yacht_ids:
        print("  [yachts] Nothing to delete.")
        return
    await db.execute(delete(DailyPulse).where(DailyPulse.yacht_id.in_(yacht_ids)))
    await db.execute(delete(SurveyResponse).where(SurveyResponse.yacht_id.in_(yacht_ids)))
    await db.execute(delete(Survey).where(Survey.yacht_id.in_(yacht_ids)))
    await db.execute(delete(CampaignCandidate).where(
        CampaignCandidate.campaign_id.in_(
            select(Campaign.id).where(Campaign.yacht_id.in_(yacht_ids))
        )
    ))
    await db.execute(delete(Campaign).where(Campaign.yacht_id.in_(yacht_ids)))
    await db.execute(delete(CrewAssignment).where(CrewAssignment.yacht_id.in_(yacht_ids)))
    await db.execute(delete(Yacht))
    await db.commit()
    print("  [yachts] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_yachts(db)
        await seed_yachts(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
