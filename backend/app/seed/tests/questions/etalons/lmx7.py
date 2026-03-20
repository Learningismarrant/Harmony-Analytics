# app/seed/tests/questions/etalons/lmx7.py
"""
LMX-7 — Leader-Member Exchange Scale (Graen & Uhl-Bien, 1995).

7 items Likert 1-5 évaluant la qualité de la relation supervisor-subordonné.
3 facettes : mutual_understanding, respect, affect.

Source : Graen, G.B., & Uhl-Bien, M. (1995). Relationship-based approach to
    leadership: Development of leader-member exchange (LMX) theory of leadership
    over 25 years. Leadership Quarterly, 6(2), 219–247.

Droits : Copyright JAI Press / Elsevier.
         Usage R&D interne uniquement — ne pas déployer en production commerciale.
Licence : COPYRIGHT_RESEARCH_ONLY
Status  : ETALON

⚠️ ÉTALON R&D — Réservé à la calibration de Q6 Management Preference.
   Le LMX-7 original utilise des échelles à libellés spécifiques par item.
   Pour simplification alpha, échelle Likert 5 uniforme :
   1 = "Not at all" → 5 = "Completely / Always".

    seed_lmx7(db)   → idempotent, retourne le TestCatalogue
    delete_lmx7(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.etalons.lmx7
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

LMX7_QUESTIONS = [
    # ── Mutual Understanding (items 1–3) ──────────────────────────────────────
    {
        "order": 1, "trait": "lmx_mutual_understanding", "reverse": False,
        "text": "Do you know where you stand with your supervisor — how your supervisor feels about you?",
    },
    {
        "order": 2, "trait": "lmx_mutual_understanding", "reverse": False,
        "text": "How well does your supervisor understand your job problems and needs?",
    },
    {
        "order": 3, "trait": "lmx_mutual_understanding", "reverse": False,
        "text": "How well does your supervisor recognize your potential?",
    },

    # ── Respect (items 4–5) ───────────────────────────────────────────────────
    {
        "order": 4, "trait": "lmx_respect", "reverse": False,
        "text": (
            "Regardless of how much formal authority your supervisor has, "
            "what are the chances that they would use their influence to help you solve problems in your work?"
        ),
    },
    {
        "order": 5, "trait": "lmx_respect", "reverse": False,
        "text": (
            "Regardless of the amount of formal authority your supervisor has, "
            "to what extent would they support you at their own expense when you need it?"
        ),
    },

    # ── Affect (items 6–7) ────────────────────────────────────────────────────
    {
        "order": 6, "trait": "lmx_affect", "reverse": False,
        "text": (
            "I have enough confidence in my supervisor that I would defend and justify "
            "their decisions if they were not present to do so."
        ),
    },
    {
        "order": 7, "trait": "lmx_affect", "reverse": False,
        "text": "How would you characterize your working relationship with your supervisor?",
    },
]

_CATALOGUE_NAME = "LMX-7"

_TRAIT_MODULE = {
    "lmx_mutual_understanding": 0,
    "lmx_respect":              1,
    "lmx_affect":               2,
}


async def seed_lmx7(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du LMX-7."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [lmx7] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "LMX-7 — Leader-Member Exchange Scale. "
            "7 items Likert 1-5 évaluant la qualité de la relation superviseur-subordonné. "
            "3 facettes : compréhension mutuelle, respect, affect. "
            "Instrument de référence (étalon) pour la calibration de Q6 Management Preference. "
            "Durée estimée : 3–5 minutes."
        ),
        instructions=(
            "Thinking about your current or most recent supervisor, rate each statement. "
            "1 = Not at all  →  5 = Completely / Always."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=7,
        is_active=True,
        status="ETALON",
        license="COPYRIGHT_RESEARCH_ONLY",
        validation_notes=(
            "LMX-7 — Graen, G.B., & Uhl-Bien, M. (1995). "
            "Relationship-based approach to leadership: Development of leader-member exchange "
            "(LMX) theory of leadership over 25 years. Leadership Quarterly, 6(2), 219–247. "
            "Copyright JAI Press / Elsevier. Usage R&D interne uniquement. "
            "⚠️ ÉTALON R&D UNIQUEMENT — ne pas déployer en production commerciale "
            "sans accord de licence. "
            "Étalon de calibration pour Q6 Management Preference (construct LMX). "
            "Alpha attendu (7 items) : α ≈ .85–.90 (Graen & Uhl-Bien, 1995). "
            "Score total /35 → normalisé 0–100. "
            "Note : le LMX-7 original utilise des ancrages verbaux spécifiques par item. "
            "Pour simplification alpha, échelle Likert 5 uniforme utilisée. "
            "⚠️ ALPHA RADIANT : Q6 LMX est une dérivation approximative — "
            "VIF Q3/Q5 à surveiller (corrélation potentielle < .5 recommandée)."
        ),
        modules_config=[
            {
                "index": 0,
                "name": "Mutual Understanding",
                "trait": "lmx_mutual_understanding",
                "n_items": 3,
                "duration_min": 2,
                "priority": "STANDARD",
                "description": "Connaissance mutuelle et reconnaissance du potentiel par le superviseur",
            },
            {
                "index": 1,
                "name": "Respect",
                "trait": "lmx_respect",
                "n_items": 2,
                "duration_min": 1,
                "priority": "STANDARD",
                "description": "Soutien et influence du superviseur — échange professionnel",
            },
            {
                "index": 2,
                "name": "Affect",
                "trait": "lmx_affect",
                "n_items": 2,
                "duration_min": 1,
                "priority": "STANDARD",
                "description": "Confiance et qualité perçue de la relation de travail",
            },
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in LMX7_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="likert",
            trait=q["trait"],
            options=None,
            correct_answer=None,
            reverse=q["reverse"],
            module_index=_TRAIT_MODULE.get(q["trait"]),
        ))

    await db.flush()
    print(f"  [lmx7] Seeded '{_CATALOGUE_NAME}' ({len(LMX7_QUESTIONS)} questions)")
    return catalogue


async def delete_lmx7(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [lmx7] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_lmx7(db)
        await seed_lmx7(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
