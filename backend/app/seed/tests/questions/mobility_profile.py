# app/seed/tests/questions/mobility_profile.py
"""
Maritime Mobility & Flexibility Scale (MMFS)

12 items Likert 1-5 évaluant la flexibilité face aux contraintes de mobilité
et temporelles du travail maritime embarqué :

    mobility_flexibility   (3 items) — flexibilité géographique / déplacements
    embarkation_tolerance  (3 items) — tolérance aux longues durées d'embarquement
    uncertainty_tolerance  (3 items) — tolérance à l'imprévisibilité des plannings
    contract_flexibility   (3 items) — flexibilité contractuelle (saisonnier / CDD)

Les scores alimentent snapshot['mobility_profile'] utilisé par
l'engine mobility_fit (Famille 7, Radiant Analytics v0.7 §7).

Source :
    Construit ad hoc pour Radiant Analytics (2026).
    Ancré sur la littérature Work Flexibility (Valcour & Ladge, 2008)
    et les contraintes spécifiques du yachting de luxe (MYBA, ISWAN).

Standalone :
    python -m app.seed.tests.questions.mobility_profile
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

MMFS_QUESTIONS = [
    # ── Flexibilité géographique ──────────────────────────────────────────────
    {"order": 1,  "trait": "mobility_flexibility", "reverse": False,
     "text": "I am comfortable relocating or travelling extensively for work with little notice."},
    {"order": 2,  "trait": "mobility_flexibility", "reverse": True,
     "text": "Having a fixed home base and predictable travel schedule is very important to me."},
    {"order": 3,  "trait": "mobility_flexibility", "reverse": False,
     "text": "I enjoy the variety of working in different locations and countries throughout the year."},

    # ── Durée d'embarquement ──────────────────────────────────────────────────
    {"order": 4,  "trait": "embarkation_tolerance", "reverse": False,
     "text": "I am comfortable spending several months continuously aboard a vessel."},
    {"order": 5,  "trait": "embarkation_tolerance", "reverse": True,
     "text": "Being away from home for more than a few weeks significantly affects my motivation."},
    {"order": 6,  "trait": "embarkation_tolerance", "reverse": False,
     "text": "Long rotations at sea suit my lifestyle better than frequent short assignments."},

    # ── Tolérance à l'imprévisibilité ─────────────────────────────────────────
    {"order": 7,  "trait": "uncertainty_tolerance", "reverse": False,
     "text": "I adapt easily when plans change suddenly or itineraries are modified last-minute."},
    {"order": 8,  "trait": "uncertainty_tolerance", "reverse": True,
     "text": "Unpredictable schedules and last-minute changes are a major source of stress for me."},
    {"order": 9,  "trait": "uncertainty_tolerance", "reverse": False,
     "text": "I thrive in dynamic work environments where no two days are the same."},

    # ── Flexibilité contractuelle ─────────────────────────────────────────────
    {"order": 10, "trait": "contract_flexibility", "reverse": False,
     "text": "I am comfortable working on seasonal or fixed-term contracts rather than permanent positions."},
    {"order": 11, "trait": "contract_flexibility", "reverse": True,
     "text": "Job security and a permanent contract are among my highest professional priorities."},
    {"order": 12, "trait": "contract_flexibility", "reverse": False,
     "text": "I see short-term contracts as opportunities to gain varied experience across different vessels."},
]

_CATALOGUE_NAME = "Maritime Mobility & Flexibility Scale (MMFS)"


async def seed_mobility_profile(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du MMFS — profil de mobilité maritime."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [mmfs] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Échelle de mobilité et flexibilité maritime — 12 items Likert 1-5. "
            "Évalue 4 dimensions : flexibilité géographique, tolérance aux longues "
            "durées d'embarquement, tolérance à l'imprévisibilité, flexibilité contractuelle. "
            "Conçu pour le recrutement en yachting de luxe (Radiant Analytics, 2026). "
            "Durée estimée : 4-6 minutes."
        ),
        instructions=(
            "Indiquez dans quelle mesure chaque affirmation vous correspond, "
            "de 1 (Pas du tout d'accord) à 5 (Tout à fait d'accord). "
            "Répondez en fonction de vos préférences et expériences réelles."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=12,
        is_active=True,
        status="ALPHA",
        license="CUSTOM_ALPHA",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — PROTOTYPAGE UNIQUEMENT. "
            "Construit ad hoc pour Radiant Analytics (2026). "
            "3 items par dimension. Non étalonné. "
            "Les scores alimentent snapshot['mobility_profile'] pour le mobility_fit (Fam. 7). "
            "Recommandation : validation factorielle confirmative (CFA) sur N≥200 "
            "et calibration des breakpoints PSI sur données terrain avant production."
        ),
        modules_config=[
            {"index": 0, "name": "Flexibilité géographique",
             "trait": "mobility_flexibility", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 1, "name": "Durée d'embarquement",
             "trait": "embarkation_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 2, "name": "Tolérance à l'imprévisibilité",
             "trait": "uncertainty_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 3, "name": "Flexibilité contractuelle",
             "trait": "contract_flexibility", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in MMFS_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="likert",
            trait=q["trait"],
            options=None,
            correct_answer=None,
            reverse=q["reverse"],
        ))

    await db.flush()
    print(f"  [mmfs] Seeded '{_CATALOGUE_NAME}' ({len(MMFS_QUESTIONS)} questions)")
    return catalogue


async def delete_mobility_profile(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [mmfs] Supprimé '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_mobility_profile(db)
        await seed_mobility_profile(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
