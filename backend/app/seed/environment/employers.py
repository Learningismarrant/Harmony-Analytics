# app/seed/environment/employers.py
"""
Seed des employers (Users CLIENT + EmployerProfile).

    seed_employers(db)   → insère 2 employers, retourne {"azure": ..., "pacific": ...}
    delete_employers(db) → supprime employers + leurs users CLIENT

Standalone :
    python -m app.seed.environment.employers
"""
import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import User, EmployerProfile
from app.shared.enums import UserRole

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash(p: str) -> str: return _pwd.hash(p)
def _now() -> datetime: return datetime.now(timezone.utc)
def _ago(days: int) -> datetime: return _now() - timedelta(days=days)


async def seed_employers(db: AsyncSession) -> dict:
    print("  [employers] Seeding...")

    user_thomas = User(
        email="thomas.laurent@azure-maritime.com",
        name="Thomas Laurent",
        hashed_password=_hash("testpassword123"),
        role=UserRole.CLIENT,
        is_active=True,
        location="Monaco",
        created_at=_ago(60),
    )
    db.add(user_thomas)
    await db.flush()

    employer_azure = EmployerProfile(
        user_id=user_thomas.id,
        company_name="Azure Maritime Management",
        is_billing_active=True,
    )
    db.add(employer_azure)

    user_diana = User(
        email="diana.chen@pacific-yachting.com",
        name="Diana Chen",
        hashed_password=_hash("testpassword123"),
        role=UserRole.CLIENT,
        is_active=True,
        location="Antibes",
        created_at=_ago(45),
    )
    db.add(user_diana)
    await db.flush()

    employer_pacific = EmployerProfile(
        user_id=user_diana.id,
        company_name="Pacific Yachting Group",
        is_billing_active=True,
    )
    db.add(employer_pacific)
    await db.flush()

    print(f"  [employers] Azure (id={employer_azure.id}), Pacific (id={employer_pacific.id})")
    return {
        "azure": employer_azure,
        "pacific": employer_pacific,
        "user_thomas": user_thomas,
        "user_diana": user_diana,
    }


async def delete_employers(db: AsyncSession) -> None:
    print("  [employers] Deleting...")
    # Employer profiles first, then users
    result = await db.execute(select(User.id).where(User.role == UserRole.CLIENT))
    user_ids = [r[0] for r in result.all()]
    if user_ids:
        await db.execute(delete(EmployerProfile).where(EmployerProfile.user_id.in_(user_ids)))
        await db.execute(delete(User).where(User.id.in_(user_ids)))
    await db.commit()
    print("  [employers] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_employers(db)
        await seed_employers(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
