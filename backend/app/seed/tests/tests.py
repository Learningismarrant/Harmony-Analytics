# app/seed/tests/tests.py
"""
Orchestrateur des seeds de tests psychométriques.

    seed_etalon_tests(db)      → seed étalons R&D (IPIP-HEXACO-60, R-MAWS, ICAR-16, LMX-7, GSE-10)
    seed_proprietary_tests(db) → seed instruments propriétaires Radiant Analytics
    seed_tests(db)             → seed tout (étalons + propriétaires)
    delete_tests(db)           → supprime tout

Étalons (R&D uniquement — ne pas déployer en production commerciale) :
    hexaco60   — IPIP-HEXACO-60 (Big Six, 60 items Likert, public domain)
    rmaws      — R-MAWS Gagné 2010 (19 items Likert, COPYRIGHT_RESEARCH_ONLY)
    icar16     — ICAR-16 Condon & Revelle 2014 (8 items QCM text-based P1 + 8 visuels P2, ICAR_PUBLIC_DOMAIN)
    lmx7       — LMX-7 Graen & Uhl-Bien 1995 (7 items Likert, COPYRIGHT_RESEARCH_ONLY)
    gse10      — GSE-10 Schwarzer & Jerusalem 1995 (10 items Likert, FREE_RESEARCH_USE)

Instruments propriétaires Radiant Analytics :
    gca_series      — Q2 GCA Séries numériques (30 items QCM)
    hmr24           — Q2 HMR-24 Matrices visuelles (24 items QCM)
    sdt6            — Q3 SDT-6 Motivation (36 items Likert-7)
    ces_values      — Q5 Valeurs professionnelles (32 items Likert-6)
    management_pref — Q6 Préférence management (18 items Likert-7)
    maritime_tolerance — Q7 Tolérance ICE physique (24 items Likert-5)
    mobility_profile   — Q7 Mobilité maritime (16 items mixte)

Standalone :
    python -m app.seed.tests.tests
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.shared.models import TestResult, Question, TestCatalogue

from app.seed.tests.questions.etalons.hexaco60       import seed_hexaco60,          delete_hexaco60
from app.seed.tests.questions.etalons.rmaws          import seed_rmaws,             delete_rmaws
from app.seed.tests.questions.etalons.icar16         import seed_icar16,            delete_icar16
from app.seed.tests.questions.etalons.lmx7           import seed_lmx7,              delete_lmx7
from app.seed.tests.questions.etalons.gse10          import seed_gse10,             delete_gse10
from app.seed.tests.questions.gca_series             import seed_gca_series,        delete_gca_series
from app.seed.tests.questions.hmr24                  import seed_hmr24,             delete_hmr24
from app.seed.tests.questions.sdt6                   import seed_sdt6,              delete_sdt6
from app.seed.tests.questions.ces_values             import seed_ces_values,        delete_ces_values
from app.seed.tests.questions.management_pref        import seed_management_pref,   delete_management_pref
from app.seed.tests.questions.maritime_tolerance     import seed_maritime_tolerance, delete_maritime_tolerance
from app.seed.tests.questions.mobility_profile       import seed_mobility_profile,  delete_mobility_profile


async def seed_etalon_tests(db: AsyncSession) -> dict:
    """Seed idempotent des étalons R&D uniquement.

    Ces instruments sont réservés à la calibration interne et à la R&D.
    Ne pas déployer en production commerciale sans vérification de licence.
    """
    print("[tests] Seeding étalons R&D...")
    hexaco60 = await seed_hexaco60(db)
    rmaws    = await seed_rmaws(db)
    icar16   = await seed_icar16(db)
    lmx7     = await seed_lmx7(db)
    gse10    = await seed_gse10(db)
    await db.commit()
    print("[tests] Étalons done.")
    return {
        "hexaco60": hexaco60,
        "rmaws":    rmaws,
        "icar16":   icar16,
        "lmx7":     lmx7,
        "gse10":    gse10,
    }


async def seed_proprietary_tests(db: AsyncSession) -> dict:
    """Seed idempotent des instruments propriétaires Radiant Analytics."""
    print("[tests] Seeding instruments propriétaires...")
    gca_series      = await seed_gca_series(db)
    hmr24           = await seed_hmr24(db)
    sdt6            = await seed_sdt6(db)
    ces             = await seed_ces_values(db)
    mgmt_pref       = await seed_management_pref(db)
    mets            = await seed_maritime_tolerance(db)
    mmfs            = await seed_mobility_profile(db)
    await db.commit()
    print("[tests] Instruments propriétaires done.")
    return {
        "gca_series":      gca_series,
        "hmr24":           hmr24,
        "sdt6":            sdt6,
        "ces_values":      ces,
        "management_pref": mgmt_pref,
        "maritime_tolerance": mets,
        "mobility_profile":   mmfs,
    }


async def seed_tests(db: AsyncSession) -> dict:
    """Seed idempotent de tous les catalogues (étalons + propriétaires)."""
    print("[tests] Seeding all catalogues...")

    # Étalons R&D
    hexaco60 = await seed_hexaco60(db)
    rmaws    = await seed_rmaws(db)
    icar16   = await seed_icar16(db)
    lmx7     = await seed_lmx7(db)
    gse10    = await seed_gse10(db)

    # Instruments propriétaires
    gca_series = await seed_gca_series(db)
    hmr24      = await seed_hmr24(db)
    sdt6       = await seed_sdt6(db)
    ces        = await seed_ces_values(db)
    mgmt_pref  = await seed_management_pref(db)
    mets       = await seed_maritime_tolerance(db)
    mmfs       = await seed_mobility_profile(db)

    await db.commit()
    print("[tests] All catalogues done.")
    return {
        # Étalons
        "hexaco60":        hexaco60,
        "rmaws":           rmaws,
        "icar16":          icar16,
        "lmx7":            lmx7,
        "gse10":           gse10,
        # Propriétaires
        "gca_series":      gca_series,
        "hmr24":           hmr24,
        "sdt6":            sdt6,
        "ces_values":      ces,
        "management_pref": mgmt_pref,
        "maritime_tolerance": mets,
        "mobility_profile":   mmfs,
    }


async def delete_tests(db: AsyncSession) -> None:
    """Supprime tous les tests (résultats, questions, catalogues)."""
    print("[tests] Deleting all test data...")
    await delete_mobility_profile(db)
    await delete_maritime_tolerance(db)
    await delete_management_pref(db)
    await delete_ces_values(db)
    await delete_sdt6(db)
    await delete_hmr24(db)
    await delete_gca_series(db)
    await delete_gse10(db)
    await delete_lmx7(db)
    await delete_icar16(db)
    await delete_rmaws(db)
    await delete_hexaco60(db)
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
