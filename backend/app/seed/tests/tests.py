# app/seed/tests/tests.py
"""
Orchestrateur des seeds de tests psychométriques.

    seed_tests(db)   → seed IPIP-120, R-MAWS, COG-IQ, HMR-24
    delete_tests(db) → supprime tous les catalogues + questions + résultats

Standalone :
    python -m app.seed.tests.tests
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.shared.models import TestResult, Question, TestCatalogue
from app.seed.tests.questions.etalons.ipip120 import seed_ipip120, delete_ipip120
from app.seed.tests.questions.etalons.rmaws import seed_rmaws, delete_rmaws
from app.seed.tests.questions.cogiq import seed_cogiq, delete_cogiq
from app.seed.tests.questions.hmr24 import seed_hmr24, delete_hmr24


async def seed_tests(db: AsyncSession) -> dict:
    """Seed idempotent des 5 catalogues de tests."""
    print("[tests] Seeding catalogues...")
    ipip120    = await seed_ipip120(db)
    rmaws      = await seed_rmaws(db)
    cogiq      = await seed_cogiq(db)
    hmr24      = await seed_hmr24(db)
    await db.commit()
    print("[tests] Done.")
    return {
        "ipip120": ipip120,
        "hmr24": hmr24,
    }


async def delete_tests(db: AsyncSession) -> None:
    """Supprime tous les tests (résultats, questions, catalogues)."""
    print("[tests] Deleting all test data...")
    await delete_hmr24(db)
    await db.execute(delete(TestResult))
    await db.execute(delete(Question))
    await db.execute(delete(TestCatalogue))
    await db.commit()
    print("[tests] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_tests(db)
        await seed_tests(db)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
