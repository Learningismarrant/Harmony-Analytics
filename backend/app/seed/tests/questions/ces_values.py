# app/seed/tests/questions/ces_values.py
"""
Comparative Emphasis Scale (CES) — Valeurs professionnelles

16 items Likert 1-5 évaluant 4 valeurs professionnelles fondamentales :
    honesty      (4 items) — honnêteté et transparence au travail
    achievement  (4 items) — accomplissement par le travail bien fait
    fairness     (4 items) — équité dans le traitement des collaborateurs
    solidarity   (4 items) — entraide et solidarité en équipage

Source :
    Ravlin, E.C., & Meglino, B.M. (1987). Effect of values on perception
    and decision making. Journal of Applied Psychology, 72, 666–673.
    Adaptation maritime Radiant Analytics (2026) — contexte embarquement.

Usage :
    seed_ces_values(db)   → idempotent, retourne le TestCatalogue
    delete_ces_values(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.ces_values
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

CES_VALUES_QUESTIONS = [
    # ── Honesty (honnêteté / transparence) ───────────────────────────────────
    {"order": 1,  "trait": "honesty", "reverse": False,
     "text": "I always tell the truth, even when it may be uncomfortable for others."},
    {"order": 2,  "trait": "honesty", "reverse": False,
     "text": "I believe that being transparent with colleagues about mistakes is essential."},
    {"order": 3,  "trait": "honesty", "reverse": True,
     "text": "It is sometimes better to omit information to avoid conflict on board."},
    {"order": 4,  "trait": "honesty", "reverse": False,
     "text": "I feel uncomfortable when people are not straightforward with each other at work."},

    # ── Achievement (accomplissement / travail bien fait) ─────────────────────
    {"order": 5,  "trait": "achievement", "reverse": False,
     "text": "I take great pride in doing every task, even routine ones, to the best of my ability."},
    {"order": 6,  "trait": "achievement", "reverse": False,
     "text": "I feel a strong sense of satisfaction when I complete a task exceptionally well."},
    {"order": 7,  "trait": "achievement", "reverse": True,
     "text": "Doing a job 'good enough' is perfectly acceptable to me when time is limited."},
    {"order": 8,  "trait": "achievement", "reverse": False,
     "text": "I set high personal standards for my work and hold myself accountable to them."},

    # ── Fairness (équité / traitement des collaborateurs) ─────────────────────
    {"order": 9,  "trait": "fairness", "reverse": False,
     "text": "I believe everyone on board deserves to be treated with the same level of respect."},
    {"order": 10, "trait": "fairness", "reverse": False,
     "text": "When assigning tasks, workload should be distributed equitably among all crew members."},
    {"order": 11, "trait": "fairness", "reverse": True,
     "text": "It is acceptable to give preferential treatment to crew members with more experience."},
    {"order": 12, "trait": "fairness", "reverse": False,
     "text": "I speak up when I witness unfair treatment of a colleague, even if it risks conflict."},

    # ── Solidarity (entraide / solidarité en équipage) ────────────────────────
    {"order": 13, "trait": "solidarity", "reverse": False,
     "text": "When a colleague is struggling, I offer help even if it is not part of my duties."},
    {"order": 14, "trait": "solidarity", "reverse": False,
     "text": "The success of the crew as a whole matters more to me than individual recognition."},
    {"order": 15, "trait": "solidarity", "reverse": True,
     "text": "I focus on my own responsibilities and prefer not to get involved in others' tasks."},
    {"order": 16, "trait": "solidarity", "reverse": False,
     "text": "I feel a strong sense of belonging and shared purpose with my crew."},
]

_CATALOGUE_NAME = "Professional Values Scale (CES)"


async def seed_ces_values(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du CES valeurs professionnelles."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [ces_values] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Échelle de valeurs professionnelles — 16 items Likert 1-5. "
            "Évalue 4 dimensions : honnêteté, accomplissement, équité, solidarité. "
            "Adapté du Comparative Emphasis Scale (Ravlin & Meglino, 1987) "
            "pour le contexte maritime embarqué. Durée estimée : 5-8 minutes."
        ),
        instructions=(
            "Indiquez dans quelle mesure chaque affirmation vous correspond, "
            "de 1 (Pas du tout d'accord) à 5 (Tout à fait d'accord). "
            "Il n'y a pas de bonnes ou mauvaises réponses — répondez honnêtement."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=16,
        is_active=True,
        status="ALPHA",
        license="CUSTOM_ALPHA",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — PROTOTYPAGE UNIQUEMENT. "
            "Adaptation maritime du CES (Ravlin & Meglino, 1987). "
            "4 items par dimension. Non étalonné sur population maritime. "
            "Recommandation : calibrer les seuils PSI sur données réelles "
            "avant utilisation en décision de recrutement."
        ),
        modules_config=[
            {"index": 0, "name": "Honnêteté",
             "trait": "honesty", "n_items": 4, "duration_min": 2, "priority": "STANDARD"},
            {"index": 1, "name": "Accomplissement",
             "trait": "achievement", "n_items": 4, "duration_min": 2, "priority": "STANDARD"},
            {"index": 2, "name": "Équité",
             "trait": "fairness", "n_items": 4, "duration_min": 2, "priority": "STANDARD"},
            {"index": 3, "name": "Solidarité",
             "trait": "solidarity", "n_items": 4, "duration_min": 2, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in CES_VALUES_QUESTIONS:
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
    print(f"  [ces_values] Seeded '{_CATALOGUE_NAME}' ({len(CES_VALUES_QUESTIONS)} questions)")
    return catalogue


async def delete_ces_values(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [ces_values] Supprimé '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_ces_values(db)
        await seed_ces_values(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
