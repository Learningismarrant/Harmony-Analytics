# app/seed/seed.py
"""
Orchestrateur principal du seed Harmony.

Usage :
    python -m app.seed.seed                       # Full : drop + recreate + seed tout
    python -m app.seed.seed --delete              # Supprime toutes les données (drop/recreate tables)
    python -m app.seed.seed --module environment  # Reseed uniquement l'environnement
    python -m app.seed.seed --module tests        # Reseed uniquement les tests
    python -m app.seed.seed --module surveys      # Reseed uniquement surveys + pulses

Ordre de seed complet :
    employers → candidates → yachts → campaigns → tests → surveys → pulses
"""
import asyncio
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base

# ── Imports modules ───────────────────────────────────────────────────────────
from app.seed.environment.employers  import seed_employers,  delete_employers
from app.seed.environment.candidates import seed_candidates, delete_candidates
from app.seed.environment.yachts     import seed_yachts,     delete_yachts
from app.seed.environment.campaigns  import seed_campaigns,  delete_campaigns
from app.seed.tests.tests            import seed_tests,      delete_tests
from app.seed.surveys.surveys        import seed_surveys,    delete_surveys
from app.seed.surveys.pulses         import seed_pulses,     delete_pulses


engine       = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


# ── Full pipeline ─────────────────────────────────────────────────────────────

async def seed_all() -> None:
    """Drop + recreate toutes les tables, puis seed complet."""
    print("[seed] Nettoyage de la base de données...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("[seed] Création des tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession() as db:
        employers = await seed_employers(db)
        await db.commit()

        candidates = await seed_candidates(db)
        await db.commit()

        yachts = await seed_yachts(db)
        await db.commit()

        await seed_campaigns(db)
        await db.commit()

    async with AsyncSession() as db:
        await seed_tests(db)

    async with AsyncSession() as db:
        await seed_surveys(db)
        await db.commit()

        await seed_pulses(db)
        await db.commit()

    print()
    print("Seed complet termine.")
    _print_summary()


async def delete_all() -> None:
    """Drop + recreate toutes les tables (repart d'une base vide)."""
    print("[seed] Suppression de toutes les données (drop + recreate)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[seed] Base vide prete.")


# ── Modules isolés ────────────────────────────────────────────────────────────

async def reseed_environment() -> None:
    """Reseed uniquement l'environnement (employers, candidates, yachts, campaigns)."""
    print("[seed] Reseed environment...")
    async with AsyncSession() as db:
        await delete_campaigns(db)
        await delete_yachts(db)
        await delete_candidates(db)
        await delete_employers(db)

        await seed_employers(db)
        await db.commit()
        await seed_candidates(db)
        await db.commit()
        await seed_yachts(db)
        await db.commit()
        await seed_campaigns(db)
        await db.commit()
    print("[seed] Environment reseede.")


async def reseed_tests() -> None:
    """Reseed uniquement les tests (catalogues + questions)."""
    print("[seed] Reseed tests...")
    async with AsyncSession() as db:
        await delete_tests(db)
        await seed_tests(db)
    print("[seed] Tests reseedes.")


async def reseed_surveys() -> None:
    """Reseed uniquement surveys + pulses."""
    print("[seed] Reseed surveys + pulses...")
    async with AsyncSession() as db:
        await delete_pulses(db)
        await delete_surveys(db)
        await seed_surveys(db)
        await db.commit()
        await seed_pulses(db)
        await db.commit()
    print("[seed] Surveys reseedes.")


# ── Résumé ────────────────────────────────────────────────────────────────────

def _print_summary() -> None:
    print()
    print("Comptes de connexion de test :")
    print("  thomas.laurent@azure-maritime.com / testpassword123  (Employer — Azure)")
    print("  diana.chen@pacific-yachting.com   / testpassword123  (Employer — Pacific)")
    print("  marcus.webb@gmail.com              / testpassword123  (Captain ELITE)")
    print("  dimitri.volkov@gmail.com           / testpassword123  (HIGH_RISK)")
    print("  sam.adler@gmail.com                / testpassword123  (DISQUALIFIED)")
    print()
    print("Modules disponibles en standalone :")
    print("  python -m app.seed.environment.employers")
    print("  python -m app.seed.environment.candidates")
    print("  python -m app.seed.environment.yachts")
    print("  python -m app.seed.environment.campaigns")
    print("  python -m app.seed.tests.questions.etalons.ipip120")
    print("  python -m app.seed.tests.questions.etalons.rmaws")
    print("  python -m app.seed.tests.questions.cogiq")
    print("  python -m app.seed.tests.questions.hmr24")
    print("  python -m app.seed.tests.questions.ces_values")
    print("  python -m app.seed.tests.questions.maritime_tolerance")
    print("  python -m app.seed.tests.questions.mobility_profile")
    print("  python -m app.seed.tests.tests")
    print("  python -m app.seed.surveys.surveys")
    print("  python -m app.seed.surveys.pulses")


# ── CLI ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    parser = argparse.ArgumentParser(description="Harmony seed CLI")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Supprime toutes les données (drop + recreate tables vides)",
    )
    parser.add_argument(
        "--module",
        choices=["environment", "tests", "surveys"],
        help="Reseed uniquement ce module (sans toucher aux autres)",
    )
    args = parser.parse_args()

    try:
        if args.delete:
            await delete_all()
        elif args.module == "environment":
            await reseed_environment()
        elif args.module == "tests":
            await reseed_tests()
        elif args.module == "surveys":
            await reseed_surveys()
        else:
            await seed_all()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
