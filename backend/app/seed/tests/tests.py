# app/seed/tests/tests.py
"""
Orchestrateur des seeds de tests psychométriques.

    seed_tests(db)   → seed 7 catalogues de tests
    delete_tests(db) → supprime tous les catalogues + questions + résultats

Catalogues (7 au total) :
    1. IPIP-120        — Big Five (personnalité, 120 items Likert)
    2. R-MAWS          — Work Motivation SDT (19 items Likert)
    3. COG-IQ          — Aptitudes cognitives (21 items QCM)
    4. HMR-24          — Raisonnement visuel (24 matrices)
    5. CES Values      — Valeurs professionnelles (16 items Likert) [PO Fit Fam. 3]
    6. METS            — Tolérance environnementale maritime (15 items Likert) [Phys Fit Fam. 6]
    7. MMFS            — Mobilité et flexibilité maritime (12 items Likert) [Mob Fit Fam. 7]

Standalone :
    python -m app.seed.tests.tests
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.shared.models import TestResult, Question, TestCatalogue
from app.seed.tests.questions.etalons.ipip120    import seed_ipip120,            delete_ipip120
from app.seed.tests.questions.etalons.rmaws      import seed_rmaws,              delete_rmaws
from app.seed.tests.questions.cogiq              import seed_cogiq,              delete_cogiq
from app.seed.tests.questions.hmr24              import seed_hmr24,              delete_hmr24
from app.seed.tests.questions.ces_values         import seed_ces_values,         delete_ces_values
from app.seed.tests.questions.maritime_tolerance import seed_maritime_tolerance,  delete_maritime_tolerance
from app.seed.tests.questions.mobility_profile   import seed_mobility_profile,   delete_mobility_profile


async def seed_tests(db: AsyncSession) -> dict:
    """Seed idempotent des 7 catalogues de tests."""
    print("[tests] Seeding catalogues...")
    ipip120    = await seed_ipip120(db)
    rmaws      = await seed_rmaws(db)
    cogiq      = await seed_cogiq(db)
    hmr24      = await seed_hmr24(db)
    ces        = await seed_ces_values(db)
    mets       = await seed_maritime_tolerance(db)
    mmfs       = await seed_mobility_profile(db)
    await db.commit()
    print("[tests] Done.")
    return {
        "ipip120":    ipip120,
        "hmr24":      hmr24,
        "ces_values": ces,
        "mets":       mets,
        "mmfs":       mmfs,
    }


async def delete_tests(db: AsyncSession) -> None:
    """Supprime tous les tests (résultats, questions, catalogues)."""
    print("[tests] Deleting all test data...")
    await delete_mobility_profile(db)
    await delete_maritime_tolerance(db)
    await delete_ces_values(db)
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
