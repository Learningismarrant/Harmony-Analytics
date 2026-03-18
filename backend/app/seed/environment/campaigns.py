# app/seed/environment/campaigns.py
"""
Seed des campagnes de recrutement (Campaign + CampaignCandidate).

    seed_campaigns(db)   → insère 2 campagnes + 6 candidatures
    delete_campaigns(db) → supprime candidatures + campagnes

Prérequis : seed_employers, seed_candidates, seed_yachts exécutés.

Standalone :
    python -m app.seed.environment.campaigns
"""
import asyncio
import secrets
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import (
    User, EmployerProfile, CrewProfile, Yacht, Campaign, CampaignCandidate,
)
from app.shared.enums import UserRole, CampaignStatus, ApplicationStatus
from app.seed.environment.snapshots import _now

def _ago(days: int) -> datetime: return _now() - timedelta(days=days)


async def seed_campaigns(db: AsyncSession) -> dict:
    print("  [campaigns] Seeding...")

    # Récupérer employers depuis la DB
    r = await db.execute(
        select(EmployerProfile, User).join(User, User.id == EmployerProfile.user_id)
    )
    employers = {u.email.split("@")[0].replace(".", "_"): ep for ep, u in r.all()}
    employer_azure   = employers.get("thomas_laurent")
    employer_pacific = employers.get("diana_chen")

    # Récupérer yachts
    r = await db.execute(select(Yacht))
    yachts = {y.name: y for y in r.scalars().all()}
    aurora = yachts.get("Lady Aurora")
    stella = yachts.get("Stella Maris")

    # Récupérer crew profiles
    r = await db.execute(select(CrewProfile, User).join(User, User.id == CrewProfile.user_id))
    profiles = {
        u.email.split("@")[0].replace(".", "_"): cp
        for cp, u in r.all()
    }

    # ── Campaigns ─────────────────────────────────────────────────────────────
    campaign_aurora = Campaign(
        title="Chief Officer — Lady Aurora (Saison 2025)",
        position="Chief Officer",
        yacht_id=aurora.id,
        employer_profile_id=employer_azure.id,
        status=CampaignStatus.OPEN,
        invite_token=secrets.token_urlsafe(16),
        description="Remplacement Chief Officer pour saison Méditerranée juillet-septembre.",
        created_at=_ago(15),
    )
    db.add(campaign_aurora)

    campaign_stella = Campaign(
        title="Captain — Stella Maris",
        position="Captain",
        yacht_id=stella.id,
        employer_profile_id=employer_pacific.id,
        status=CampaignStatus.OPEN,
        invite_token=secrets.token_urlsafe(16),
        description="Recherche capitaine expérimenté pour grand yacht 68m.",
        created_at=_ago(10),
    )
    db.add(campaign_stella)
    await db.flush()

    # ── CampaignCandidates ────────────────────────────────────────────────────
    for key, status in [
        ("tom_bradley",   ApplicationStatus.PENDING),   # STRONG_FIT
        ("aisha_nkosi",   ApplicationStatus.PENDING),   # GOOD_FIT
        ("carlos_mendez", ApplicationStatus.PENDING),   # HIGH_RISK
        ("sam_adler",     ApplicationStatus.PENDING),   # DISQUALIFIED
    ]:
        cp = profiles.get(key)
        if cp:
            db.add(CampaignCandidate(
                campaign_id=campaign_aurora.id,
                crew_profile_id=cp.id,
                status=status,
                joined_at=_ago(8),
            ))

    for key, status in [
        ("aisha_nkosi", ApplicationStatus.PENDING),
        ("marcus_webb", ApplicationStatus.PENDING),
    ]:
        cp = profiles.get(key)
        if cp:
            db.add(CampaignCandidate(
                campaign_id=campaign_stella.id,
                crew_profile_id=cp.id,
                status=status,
                joined_at=_ago(5),
            ))

    await db.flush()
    print(f"  [campaigns] Aurora (id={campaign_aurora.id}), Stella (id={campaign_stella.id})")
    return {"aurora": campaign_aurora, "stella": campaign_stella}


async def delete_campaigns(db: AsyncSession) -> None:
    print("  [campaigns] Deleting...")
    await db.execute(delete(CampaignCandidate))
    await db.execute(delete(Campaign))
    await db.commit()
    print("  [campaigns] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_campaigns(db)
        await seed_campaigns(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
