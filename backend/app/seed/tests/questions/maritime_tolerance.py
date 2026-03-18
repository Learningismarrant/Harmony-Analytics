# app/seed/tests/questions/maritime_tolerance.py
"""
Maritime Environmental Tolerance Scale (METS)

15 items Likert 1-5 évaluant la tolérance aux 5 contraintes physiques
et environnementales du milieu maritime embarqué :

    confined_space_tolerance  (3 items) — espace confiné à bord
    isolation_tolerance       (3 items) — isolement prolongé en mer
    physical_risk_tolerance   (3 items) — risques physiques maritimes
    schedule_tolerance        (3 items) — horaires irréguliers / quarts
    weather_tolerance         (3 items) — conditions météo exigeantes

Les scores alimentent snapshot['maritime_tolerance'] utilisé par
l'engine physical_fit (Famille 6, Radiant Analytics v0.7 §6).

Source :
    Construit ad hoc pour Radiant Analytics (2026) — pas d'étalon
    externe disponible pour ce domaine spécifique.
    Ancré sur les exigences opérationnelles des yachts de luxe (MCA, STCW).

Standalone :
    python -m app.seed.tests.questions.maritime_tolerance
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

METS_QUESTIONS = [
    # ── Espace confiné ────────────────────────────────────────────────────────
    {"order": 1,  "trait": "confined_space_tolerance", "reverse": False,
     "text": "I feel comfortable working and living in small, confined spaces for extended periods."},
    {"order": 2,  "trait": "confined_space_tolerance", "reverse": True,
     "text": "Spending weeks in a cramped cabin makes me feel anxious or claustrophobic."},
    {"order": 3,  "trait": "confined_space_tolerance", "reverse": False,
     "text": "I can adapt easily to having limited personal space when living aboard a vessel."},

    # ── Isolement ─────────────────────────────────────────────────────────────
    {"order": 4,  "trait": "isolation_tolerance", "reverse": False,
     "text": "I am comfortable being away from family and friends for weeks at a time."},
    {"order": 5,  "trait": "isolation_tolerance", "reverse": True,
     "text": "Long periods without access to the city or social activities affect my well-being significantly."},
    {"order": 6,  "trait": "isolation_tolerance", "reverse": False,
     "text": "I enjoy the focused, self-contained environment of being at sea away from land."},

    # ── Risques physiques ─────────────────────────────────────────────────────
    {"order": 7,  "trait": "physical_risk_tolerance", "reverse": False,
     "text": "Working in physically demanding or potentially hazardous conditions does not deter me."},
    {"order": 8,  "trait": "physical_risk_tolerance", "reverse": False,
     "text": "I am comfortable performing tasks at height, in the water, or in adverse weather conditions."},
    {"order": 9,  "trait": "physical_risk_tolerance", "reverse": True,
     "text": "The possibility of physical injury at work is a significant concern for me."},

    # ── Horaires irréguliers ──────────────────────────────────────────────────
    {"order": 10, "trait": "schedule_tolerance", "reverse": False,
     "text": "I adapt easily to rotating watch schedules and irregular sleep patterns."},
    {"order": 11, "trait": "schedule_tolerance", "reverse": True,
     "text": "Unpredictable work hours significantly impact my performance and mood."},
    {"order": 12, "trait": "schedule_tolerance", "reverse": False,
     "text": "I function well even when my daily routine changes frequently or without notice."},

    # ── Conditions météo ──────────────────────────────────────────────────────
    {"order": 13, "trait": "weather_tolerance", "reverse": False,
     "text": "I remain calm and focused when working in rough sea conditions or heavy weather."},
    {"order": 14, "trait": "weather_tolerance", "reverse": True,
     "text": "Rough seas or strong winds significantly increase my stress levels and discomfort."},
    {"order": 15, "trait": "weather_tolerance", "reverse": False,
     "text": "I enjoy the physical challenge of operating in demanding weather conditions at sea."},
]

_CATALOGUE_NAME = "Maritime Environmental Tolerance Scale (METS)"


async def seed_maritime_tolerance(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du METS — tolérance environnementale maritime."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [mets] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Échelle de tolérance environnementale maritime — 15 items Likert 1-5. "
            "Évalue 5 dimensions : espace confiné, isolement, risques physiques, "
            "horaires irréguliers, conditions météo. "
            "Conçu pour le recrutement en yachting de luxe (Radiant Analytics, 2026). "
            "Durée estimée : 5-7 minutes."
        ),
        instructions=(
            "Indiquez dans quelle mesure chaque affirmation vous correspond, "
            "de 1 (Pas du tout d'accord) à 5 (Tout à fait d'accord). "
            "Répondez en pensant à votre expérience réelle ou à la façon dont "
            "vous vous comporteriez dans ces situations."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=15,
        is_active=True,
        status="ALPHA",
        license="CUSTOM_ALPHA",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — PROTOTYPAGE UNIQUEMENT. "
            "Construit ad hoc pour Radiant Analytics (2026). "
            "3 items par dimension. Non étalonné. "
            "Les scores alimentent snapshot['maritime_tolerance'] pour le physical_fit (Fam. 6). "
            "Recommandation : valider la structure factorielle (CFA) sur N≥200 "
            "avant utilisation décisionnelle."
        ),
        modules_config=[
            {"index": 0, "name": "Espace confiné",
             "trait": "confined_space_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 1, "name": "Isolement en mer",
             "trait": "isolation_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 2, "name": "Risques physiques",
             "trait": "physical_risk_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 3, "name": "Horaires irréguliers",
             "trait": "schedule_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
            {"index": 4, "name": "Conditions météo",
             "trait": "weather_tolerance", "n_items": 3, "duration_min": 1, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in METS_QUESTIONS:
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
    print(f"  [mets] Seeded '{_CATALOGUE_NAME}' ({len(METS_QUESTIONS)} questions)")
    return catalogue


async def delete_maritime_tolerance(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [mets] Supprimé '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_maritime_tolerance(db)
        await seed_maritime_tolerance(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
