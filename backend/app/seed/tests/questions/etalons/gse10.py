# app/seed/tests/questions/etalons/gse10.py
"""
GSE-10 — General Self-Efficacy Scale (Schwarzer & Jerusalem, 1995).

10 items Likert 1-4 évaluant l'auto-efficacité généralisée.
1 facteur unidimensionnel : General Self-Efficacy (gse).

Source : Schwarzer, R., & Jerusalem, M. (1995). Generalized Self-Efficacy scale.
    In J. Weinman, S. Wright, & M. Johnston (Eds.),
    Measures in health psychology: A user's portfolio (pp. 35–37). NFER-NELSON.

Droits : Free for research use — schwarzer.de (déclaration explicite sur le site).
Licence : FREE_RESEARCH_USE
Status  : ETALON

⚠️ ÉTALON R&D — Usage calibration interne uniquement.
   Étalon de référence pour Q7 ICE Physical (items auto-efficacité
   en environnement contraignant).

    seed_gse10(db)   → idempotent, retourne le TestCatalogue
    delete_gse10(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.etalons.gse10
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

GSE10_QUESTIONS = [
    # ── General Self-Efficacy — 10 items ──────────────────────────────────────
    # Wording exact : Schwarzer & Jerusalem (1995) — schwarzer.de
    {
        "order":  1, "trait": "gse", "reverse": False,
        "text": "I can always manage to solve difficult problems if I try hard enough.",
    },
    {
        "order":  2, "trait": "gse", "reverse": False,
        "text": "If someone opposes me, I can find the means and ways to get what I want.",
    },
    {
        "order":  3, "trait": "gse", "reverse": False,
        "text": "It is easy for me to stick to my aims and accomplish my goals.",
    },
    {
        "order":  4, "trait": "gse", "reverse": False,
        "text": "I am confident that I could deal efficiently with unexpected events.",
    },
    {
        "order":  5, "trait": "gse", "reverse": False,
        "text": "Thanks to my resourcefulness, I know how to handle unforeseen situations.",
    },
    {
        "order":  6, "trait": "gse", "reverse": False,
        "text": "I can solve most problems if I invest the necessary effort.",
    },
    {
        "order":  7, "trait": "gse", "reverse": False,
        "text": "I can remain calm when facing difficulties because I can rely on my coping abilities.",
    },
    {
        "order":  8, "trait": "gse", "reverse": False,
        "text": "When I am confronted with a problem, I can usually find several solutions.",
    },
    {
        "order":  9, "trait": "gse", "reverse": False,
        "text": "If I am in trouble, I can usually think of a solution.",
    },
    {
        "order": 10, "trait": "gse", "reverse": False,
        "text": "I can usually handle whatever comes my way.",
    },
]

_CATALOGUE_NAME = "GSE-10"


async def seed_gse10(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent de la GSE-10."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [gse10] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "GSE-10 — General Self-Efficacy Scale. "
            "10 items Likert 1-4 évaluant l'auto-efficacité généralisée. "
            "Facteur unidimensionnel (gse). "
            "Instrument de référence (étalon) pour la calibration de Q7 ICE Physical "
            "(items auto-efficacité en environnement contraignant). "
            "Durée estimée : 3–5 minutes."
        ),
        instructions=(
            "Rate each statement according to how true it is for you. "
            "1 = Not at all true  →  4 = Exactly true."
        ),
        test_type="likert",
        max_score_per_question=4,
        n_questions=10,
        is_active=True,
        status="ETALON",
        license="FREE_RESEARCH_USE",
        validation_notes=(
            "GSE-10 — Schwarzer, R., & Jerusalem, M. (1995). Generalized Self-Efficacy scale. "
            "In J. Weinman, S. Wright, & M. Johnston (Eds.), "
            "Measures in health psychology: A user's portfolio (pp. 35–37). NFER-NELSON. "
            "Free for research use — schwarzer.de (déclaration explicite). "
            "⚠️ ÉTALON R&D UNIQUEMENT — ne pas déployer en production commerciale. "
            "Étalon de calibration pour Q7 ICE Physical (construct auto-efficacité). "
            "Alpha attendu : α ≈ .75–.90 selon les populations (Schwarzer & Jerusalem, 1995). "
            "Score total /40 → normalisé 0–100. "
            "Aucun item inversé — tous formulés positivement. "
            "Validé dans de nombreuses langues et cultures (schwarzer.de/gse.htm). "
            "Non étalonné sur population maritime — calibration à effectuer Phase 0."
        ),
        modules_config=[
            {
                "index": 0,
                "name": "General Self-Efficacy",
                "trait": "gse",
                "n_items": 10,
                "duration_min": 4,
                "priority": "STANDARD",
                "description": (
                    "Croyance généralisée en sa capacité à gérer les obstacles et événements imprévus — "
                    "prédicteur de résilience ICE (environnements contraignants)."
                ),
            },
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in GSE10_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="likert",
            trait=q["trait"],
            options=None,
            correct_answer=None,
            reverse=q["reverse"],
            module_index=0,
        ))

    await db.flush()
    print(f"  [gse10] Seeded '{_CATALOGUE_NAME}' ({len(GSE10_QUESTIONS)} questions)")
    return catalogue


async def delete_gse10(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [gse10] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_gse10(db)
        await seed_gse10(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
