# app/seed/tests/questions/cogiq.py
"""
Cognitive IQ Assessment — COG-IQ (Carroll, 1993).

21 items QCM : raisonnement numérique (6), logique (7), verbal (8).
Ancré sur le g de Spearman (raisonnement fluide Gf).
Corrections appliquées :
  - Clé CAKE/BREAD corrigée (CSFBG → CSFBE)
  - Calcul jour corrigé (Thursday → Wednesday)
  - Item ambigu Circle/Square/Sphere remplacé
  - 3 items vocabulaire pur remplacés par raisonnement relationnel
  - 1 item analogie relationnelle ajouté

    seed_cogiq(db)   → idempotent, retourne le TestCatalogue
    delete_cogiq(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.cogiq
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

COGIQ_QUESTIONS = [
    # ── Numérique (6 items) ───────────────────────────────────────────────────
    {"order": 1,  "trait": "numerical", "correct_answer": "C",
     "text": "4, 9, 16, 25, ... What is the next number?",
     "options": {"A": "30", "B": "34", "C": "36", "D": "49"}},

    {"order": 2,  "trait": "numerical", "correct_answer": "B",
     "text": "3, 6, 11, 18, ... What is the next number?",
     "options": {"A": "25", "B": "27", "C": "29", "D": "31"}},

    {"order": 3,  "trait": "numerical", "correct_answer": "B",
     "text": "120, 60, 30, 15, ... What is the next number?",
     "options": {"A": "5", "B": "7.5", "C": "10", "D": "8"}},

    {"order": 4,  "trait": "numerical", "correct_answer": "D",
     "text": "1, 1, 2, 3, 5, 8, ... What is the next number?",
     "options": {"A": "10", "B": "11", "C": "12", "D": "13"}},

    {"order": 5,  "trait": "numerical", "correct_answer": "B",
     "text": "If 3 widgets cost $4.50, how much do 7 widgets cost?",
     "options": {"A": "$9.00", "B": "$10.50", "C": "$11.00", "D": "$12.00"}},

    {"order": 6,  "trait": "numerical", "correct_answer": "B",
     "text": "A bat and a ball together cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost?",
     "options": {"A": "$0.10", "B": "$0.05", "C": "$0.15", "D": "$0.55"}},

    # ── Logique (7 items) ─────────────────────────────────────────────────────
    {"order": 7,  "trait": "logical", "correct_answer": "A",
     "text": "All A are B. All B are C. Are all A also C?",
     "options": {"A": "Yes", "B": "No", "C": "Uncertain", "D": "Only sometimes"}},

    {"order": 8,  "trait": "logical", "correct_answer": "C",
     "text": "If North becomes South and East becomes West, what does Northwest become?",
     "options": {"A": "Northeast", "B": "Southwest", "C": "Southeast", "D": "Northwest"}},

    {"order": 9,  "trait": "logical", "correct_answer": "D",
     "text": "Find the odd one out: 3, 6, 9, 13.",
     "options": {"A": "3", "B": "6", "C": "9", "D": "13"}},

    {"order": 10, "trait": "logical", "correct_answer": "B",
     "text": "Book is to reading as fork is to ___",
     "options": {"A": "Cooking", "B": "Eating", "C": "Spoon", "D": "Cutlery"}},

    {"order": 11, "trait": "logical", "correct_answer": "A",
     "text": "If 'CAKE' is coded as 'DBLF', what is 'BREAD'?",
     "options": {"A": "CSFBE", "B": "CSFBG", "C": "DSFBE", "D": "CTFBG"}},

    {"order": 12, "trait": "logical", "correct_answer": "C",
     "text": "John is taller than Sam. Sam is shorter than Alex. Is John taller than Alex?",
     "options": {"A": "Yes", "B": "No", "C": "Uncertain", "D": "They are equal"}},

    {"order": 13, "trait": "logical", "correct_answer": "C",
     "text": "2 days ago was Friday. What day will it be 3 days from now?",
     "options": {"A": "Monday", "B": "Tuesday", "C": "Wednesday", "D": "Thursday"}},

    # ── Verbal / Raisonnement relationnel (8 items) ───────────────────────────
    {"order": 14, "trait": "verbal", "correct_answer": "A",
     "text": "If 'library' relates to 'books', then 'gallery' relates to ___",
     "options": {"A": "Paintings", "B": "Books", "C": "Concerts", "D": "Athletes"}},

    {"order": 15, "trait": "verbal", "correct_answer": "C",
     "text": "The opposite of 'expand' is to ___",
     "options": {"A": "Grow", "B": "Add", "C": "Shrink", "D": "Inflate"}},

    {"order": 16, "trait": "verbal", "correct_answer": "B",
     "text": "'Prudence' is to 'caution' as 'efficiency' is to ___",
     "options": {"A": "Speed", "B": "Productivity", "C": "Laziness", "D": "Waste"}},

    {"order": 17, "trait": "verbal", "correct_answer": "A",
     "text": "Rearrange the letters R-A-I-N-T to form a common word.",
     "options": {"A": "TRAIN", "B": "RAINY", "C": "RAIN", "D": "ANTI"}},

    {"order": 18, "trait": "verbal", "correct_answer": "C",
     "text": "Which item does not belong in the same category? Apple, Banana, Carrot, Grape",
     "options": {"A": "Apple", "B": "Banana", "C": "Carrot", "D": "Grape"}},

    {"order": 19, "trait": "verbal", "correct_answer": "D",
     "text": "If a task is described as 'mandatory', it means it is ___",
     "options": {"A": "Optional", "B": "Suggested", "C": "Forbidden", "D": "Required"}},

    {"order": 20, "trait": "verbal", "correct_answer": "B",
     "text": "Complete the sentence: 'The expedition was ___ due to unforeseen weather conditions.'",
     "options": {"A": "Promoted", "B": "Cancelled", "C": "Organised", "D": "Celebrated"}},

    {"order": 21, "trait": "verbal", "correct_answer": "B",
     "text": "Captain is to ship as conductor is to ___",
     "options": {"A": "Train", "B": "Orchestra", "C": "Electricity", "D": "Baton"}},
]

_CATALOGUE_NAME = "Cognitive IQ Assessment (COG-IQ)"


async def seed_cogiq(db: AsyncSession) -> TestCatalogue:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [cogiq] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Test d'aptitudes cognitives — raisonnement numérique, logique et verbal. "
            "21 items à choix multiples. Ancré sur le g de Spearman (Carroll, 1993). "
            "Durée estimée : 20-25 minutes."
        ),
        instructions=(
            "Pour chaque question, choisissez la réponse qui vous semble la plus "
            "logique ou correcte. Prenez le temps nécessaire — il n'y a pas de limite de temps globale."
        ),
        test_type="qcm",
        max_score_per_question=1,
        n_questions=21,
        is_active=True,
        status="ALPHA",
        license="CUSTOM_ALPHA",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA NON ÉTALONNÉ — PROTOTYPAGE UNIQUEMENT. "
            "21 items QCM construits ad hoc pour le prototypage Harmony. "
            "Non validé psychométriquement. Le label 'GCA' est une approximation — "
            "ce composite n'a pas de corrélation documentée avec des tests GCA standardisés "
            "(Raven SPM, Wonderlic WPT-R). "
            "Recommandation head-of-science (2026-03) : reconstruire en 3 sous-tests CHC "
            "calibrés (Gf matrices + Gc verbal + Gq quantitatif, minimum 32 items) "
            "avant mise en production. Ne pas utiliser les scores GCA pour des décisions "
            "de recrutement réelles jusqu'à validation externe."
        ),
        modules_config=[
            {"index": 0, "name": "Raisonnement numérique (Gq)",
             "trait": "numerical", "n_items": 6, "duration_min": 5, "priority": "STANDARD"},
            {"index": 1, "name": "Raisonnement logique (Gf)",
             "trait": "logical", "n_items": 7, "duration_min": 6, "priority": "STANDARD"},
            {"index": 2, "name": "Raisonnement verbal (Gc)",
             "trait": "verbal", "n_items": 8, "duration_min": 7, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    _TRAIT_MODULE = {
        "numerical": 0,
        "logical":   1,
        "verbal":    2,
    }

    for q in COGIQ_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            text=q["text"],
            question_type="qcm",
            trait=q["trait"],
            reverse=False,
            order=q["order"],
            correct_answer=q["correct_answer"],
            options=q.get("options"),
            module_index=_TRAIT_MODULE.get(q["trait"]),
        ))
    await db.flush()
    print(f"  [cogiq] Créé (id={catalogue.id}, {len(COGIQ_QUESTIONS)} questions)")
    return catalogue


async def delete_cogiq(db: AsyncSession) -> None:
    print("  [cogiq] Deleting...")
    result = await db.execute(
        select(TestCatalogue.id).where(TestCatalogue.name == _CATALOGUE_NAME)
    )
    cat_id = result.scalar_one_or_none()
    if cat_id:
        await db.execute(delete(Question).where(Question.test_id == cat_id))
        await db.execute(delete(TestCatalogue).where(TestCatalogue.id == cat_id))
    await db.commit()
    print("  [cogiq] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_cogiq(db)
        await seed_cogiq(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
