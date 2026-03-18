"""
Inventaire IPIP-120 basé sur l'IRT (Maples et al., 2014).
https://ipip.ori.org/IPIP300-120ComparisonTable_Maples_etal.htm
120 items Likert 1-5 évaluant les 5 grands domaines et leurs 30 facettes.
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

# Les items sont extraits de l'appendice "IRT-Based IPIP-120 Items" 
IPIP120_QUESTIONS = [
    # ── Neuroticism (N) ───────────────────────────────────────────────────────
    {"order": 1,  "trait": "neuroticism", "reverse": False, "text": "Worry about things."},
    {"order": 2,  "trait": "neuroticism", "reverse": False, "text": "Fear for the worst."},
    {"order": 3,  "trait": "neuroticism", "reverse": False, "text": "Am afraid of many things."},
    {"order": 4,  "trait": "neuroticism", "reverse": False, "text": "Get stressed out easily."},
    {"order": 5,  "trait": "neuroticism", "reverse": False, "text": "Get angry easily."},
    {"order": 6,  "trait": "neuroticism", "reverse": False, "text": "Get irritated easily."},
    {"order": 7,  "trait": "neuroticism", "reverse": False, "text": "Lose my temper."},
    {"order": 8,  "trait": "neuroticism", "reverse": True,  "text": "Rarely get irritated."},
    {"order": 9,  "trait": "neuroticism", "reverse": False, "text": "Often feel blue."},
    {"order": 10, "trait": "neuroticism", "reverse": False, "text": "Dislike myself."},
    {"order": 11, "trait": "neuroticism", "reverse": False, "text": "Am often down in the dumps."},
    {"order": 12, "trait": "neuroticism", "reverse": False, "text": "Have a low opinion of myself."},
    {"order": 13, "trait": "neuroticism", "reverse": False, "text": "Find it difficult to approach others."},
    {"order": 14, "trait": "neuroticism", "reverse": False, "text": "Am easily intimidated."},
    {"order": 15, "trait": "neuroticism", "reverse": True,  "text": "Am not embarrassed easily."},
    {"order": 16, "trait": "neuroticism", "reverse": True,  "text": "Am able to stand up for myself."},
    {"order": 17, "trait": "neuroticism", "reverse": False, "text": "Often eat too much."},
    {"order": 18, "trait": "neuroticism", "reverse": False, "text": "Go on binges."},
    {"order": 19, "trait": "neuroticism", "reverse": True,  "text": "Rarely overindulge."},
    {"order": 20, "trait": "neuroticism", "reverse": True,  "text": "Am able to control my cravings."},
    {"order": 21, "trait": "neuroticism", "reverse": False, "text": "Feel that I'm unable to deal with things."},
    {"order": 22, "trait": "neuroticism", "reverse": True,  "text": "Remain calm under pressure."},
    {"order": 23, "trait": "neuroticism", "reverse": True,  "text": "Know how to cope."},
    {"order": 24, "trait": "neuroticism", "reverse": True,  "text": "Am calm even in tense situations."},

    # ── Extraversion (E) ──────────────────────────────────────────────────────
    {"order": 25, "trait": "extraversion", "reverse": False, "text": "Make friends easily."},
    {"order": 26, "trait": "extraversion", "reverse": False, "text": "Warm up quickly to others."},
    {"order": 27, "trait": "extraversion", "reverse": False, "text": "Feel comfortable around people."},
    {"order": 28, "trait": "extraversion", "reverse": False, "text": "Act comfortably with others."},
    {"order": 29, "trait": "extraversion", "reverse": False, "text": "Love large parties."},
    {"order": 30, "trait": "extraversion", "reverse": False, "text": "Talk to a lot of different people at parties."},
    {"order": 31, "trait": "extraversion", "reverse": True,  "text": "Don't like crowded events."},
    {"order": 32, "trait": "extraversion", "reverse": True,  "text": "Avoid crowds."},
    {"order": 33, "trait": "extraversion", "reverse": False, "text": "Take charge."},
    {"order": 34, "trait": "extraversion", "reverse": False, "text": "Try to lead others."},
    {"order": 35, "trait": "extraversion", "reverse": False, "text": "Take control of things."},
    {"order": 36, "trait": "extraversion", "reverse": True,  "text": "Wait for others to lead the way."},
    {"order": 37, "trait": "extraversion", "reverse": False, "text": "Am always busy."},
    {"order": 38, "trait": "extraversion", "reverse": False, "text": "Am always on the go."},
    {"order": 39, "trait": "extraversion", "reverse": False, "text": "Do a lot in my spare time."},
    {"order": 40, "trait": "extraversion", "reverse": False, "text": "Can manage many things at the same time."},
    {"order": 41, "trait": "extraversion", "reverse": False, "text": "Love excitement."},
    {"order": 42, "trait": "extraversion", "reverse": False, "text": "Seek adventure."},
    {"order": 43, "trait": "extraversion", "reverse": False, "text": "Love action."},
    {"order": 44, "trait": "extraversion", "reverse": False, "text": "Enjoy being reckless."},
    {"order": 45, "trait": "extraversion", "reverse": False, "text": "Radiate joy."},
    {"order": 46, "trait": "extraversion", "reverse": False, "text": "Have a lot of fun."},
    {"order": 47, "trait": "extraversion", "reverse": False, "text": "Love life."},
    {"order": 48, "trait": "extraversion", "reverse": False, "text": "Laugh aloud."},

    # ── Openness (O) ──────────────────────────────────────────────────────────
    {"order": 49, "trait": "openness", "reverse": False, "text": "Have a vivid imagination."},
    {"order": 50, "trait": "openness", "reverse": False, "text": "Enjoy wild flights of fantasy."},
    {"order": 51, "trait": "openness", "reverse": False, "text": "Love to daydream."},
    {"order": 52, "trait": "openness", "reverse": False, "text": "Like to get lost in thought."},
    {"order": 53, "trait": "openness", "reverse": False, "text": "See beauty in things that others might not notice."},
    {"order": 54, "trait": "openness", "reverse": True,  "text": "Do not like art."},
    {"order": 55, "trait": "openness", "reverse": True,  "text": "Do not like poetry."},
    {"order": 56, "trait": "openness", "reverse": True,  "text": "Do not enjoy going to art museums."},
    {"order": 57, "trait": "openness", "reverse": False, "text": "Experience my emotions intensely."},
    {"order": 58, "trait": "openness", "reverse": True,  "text": "Seldom get emotional."},
    {"order": 59, "trait": "openness", "reverse": True,  "text": "Am not easily affected by my emotions."},
    {"order": 60, "trait": "openness", "reverse": True,  "text": "Experience very few emotional highs and lows."},
    {"order": 61, "trait": "openness", "reverse": True,  "text": "Prefer to stick with things that I know."},
    {"order": 62, "trait": "openness", "reverse": True,  "text": "Dislike changes."},
    {"order": 63, "trait": "openness", "reverse": True,  "text": "Don't like the idea of change."},
    {"order": 64, "trait": "openness", "reverse": True,  "text": "Am attached to conventional ways."},
    {"order": 65, "trait": "openness", "reverse": True,  "text": "Am not interested in abstract ideas."},
    {"order": 66, "trait": "openness", "reverse": True,  "text": "Avoid philosophical discussions."},
    {"order": 67, "trait": "openness", "reverse": True,  "text": "Have difficulty understanding abstract ideas."},
    {"order": 68, "trait": "openness", "reverse": True,  "text": "Am not interested in theoretical discussions."},
    {"order": 69, "trait": "openness", "reverse": False, "text": "Tend to vote for liberal political candidates."},
    {"order": 70, "trait": "openness", "reverse": True,  "text": "Believe in one true religion."},
    {"order": 71, "trait": "openness", "reverse": True,  "text": "Tend to vote for conservative political candidates."},
    {"order": 72, "trait": "openness", "reverse": True,  "text": "Like to stand during the national anthem."},

    # ── Agreeableness (A) ─────────────────────────────────────────────────────
    {"order": 73, "trait": "agreeableness", "reverse": False, "text": "Trust others."},
    {"order": 74, "trait": "agreeableness", "reverse": False, "text": "Believe that others have good intentions."},
    {"order": 75, "trait": "agreeableness", "reverse": False, "text": "Trust what people say."},
    {"order": 76, "trait": "agreeableness", "reverse": True,  "text": "Distrust people."},
    {"order": 77, "trait": "agreeableness", "reverse": True,  "text": "Use flattery to get ahead."},
    {"order": 78, "trait": "agreeableness", "reverse": True,  "text": "Know how to get around the rules."},
    {"order": 79, "trait": "agreeableness", "reverse": True,  "text": "Cheat to get ahead."},
    {"order": 80, "trait": "agreeableness", "reverse": True,  "text": "Take advantage of others."},
    {"order": 81, "trait": "agreeableness", "reverse": False, "text": "Make people feel welcome."},
    {"order": 82, "trait": "agreeableness", "reverse": False, "text": "Love to help others."},
    {"order": 83, "trait": "agreeableness", "reverse": False, "text": "Am concerned about others."},
    {"order": 84, "trait": "agreeableness", "reverse": True,  "text": "Turn my back on others."},
    {"order": 85, "trait": "agreeableness", "reverse": True,  "text": "Love a good fight."},
    {"order": 86, "trait": "agreeableness", "reverse": True,  "text": "Yell at people."},
    {"order": 87, "trait": "agreeableness", "reverse": True,  "text": "Insult people."},
    {"order": 88, "trait": "agreeableness", "reverse": True,  "text": "Get back at others."},
    {"order": 89, "trait": "agreeableness", "reverse": True,  "text": "Believe that I am better than others."},
    {"order": 90, "trait": "agreeableness", "reverse": True,  "text": "Think highly of myself."},
    {"order": 91, "trait": "agreeableness", "reverse": True,  "text": "Have a high opinion of myself."},
    {"order": 92, "trait": "agreeableness", "reverse": True,  "text": "Make myself the center of attention."},
    {"order": 93, "trait": "agreeableness", "reverse": False, "text": "Sympathize with the homeless."},
    {"order": 94, "trait": "agreeableness", "reverse": False, "text": "Feel sympathy for those who are worse off than myself."},
    {"order": 95, "trait": "agreeableness", "reverse": False, "text": "Suffer from others' sorrows."},
    {"order": 96, "trait": "agreeableness", "reverse": True,  "text": "Am not interested in other people's problems."},

    # ── Conscientiousness (C) ─────────────────────────────────────────────────
    {"order": 97,  "trait": "conscientiousness", "reverse": False, "text": "Complete tasks successfully."},
    {"order": 98,  "trait": "conscientiousness", "reverse": False, "text": "Excel in what I do."},
    {"order": 99,  "trait": "conscientiousness", "reverse": False, "text": "Handle tasks smoothly."},
    {"order": 100, "trait": "conscientiousness", "reverse": False, "text": "Know how to get things done."},
    {"order": 101, "trait": "conscientiousness", "reverse": False, "text": "Like order."},
    {"order": 102, "trait": "conscientiousness", "reverse": False, "text": "Like to tidy up."},
    {"order": 103, "trait": "conscientiousness", "reverse": True,  "text": "Leave a mess in my room."},
    {"order": 104, "trait": "conscientiousness", "reverse": True,  "text": "Leave my belongings around."},
    {"order": 105, "trait": "conscientiousness", "reverse": False, "text": "Keep my promises."},
    {"order": 106, "trait": "conscientiousness", "reverse": False, "text": "Tell the truth."},
    {"order": 107, "trait": "conscientiousness", "reverse": True,  "text": "Break my promises."},
    {"order": 108, "trait": "conscientiousness", "reverse": True,  "text": "Get others to do my duties."},
    {"order": 109, "trait": "conscientiousness", "reverse": False, "text": "Work hard."},
    {"order": 110, "trait": "conscientiousness", "reverse": False, "text": "Do more than what's expected of me."},
    {"order": 111, "trait": "conscientiousness", "reverse": False, "text": "Set high standards for myself and others."},
    {"order": 112, "trait": "conscientiousness", "reverse": True,  "text": "Am not highly motivated to succeed."},
    {"order": 113, "trait": "conscientiousness", "reverse": False, "text": "Start tasks right away."},
    {"order": 114, "trait": "conscientiousness", "reverse": True,  "text": "Find it difficult to get down to work."},
    {"order": 115, "trait": "conscientiousness", "reverse": True,  "text": "Need a push to get started."},
    {"order": 116, "trait": "conscientiousness", "reverse": True,  "text": "Have difficulty starting tasks."},
    {"order": 117, "trait": "conscientiousness", "reverse": True,  "text": "Jump into things without thinking."},
    {"order": 118, "trait": "conscientiousness", "reverse": True,  "text": "Make rash decisions."},
    {"order": 119, "trait": "conscientiousness", "reverse": True,  "text": "Rush into things."},
    {"order": 120, "trait": "conscientiousness", "reverse": True,  "text": "Act without thinking."},
]

_CATALOGUE_NAME = "Harmony Big Five Inventory (IRT IPIP-120)"

async def seed_ipip120(db: AsyncSession) -> TestCatalogue:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [ipip120] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Inventaire des 5 grands traits de personnalité et leurs 30 facettes — 120 items IPIP-120 basés sur la théorie de la réponse à l'item (IRT) "
            "(Maples et al., 2014). Likert 1-5. "
            "Durée estimée : 15-20 minutes. "
            "Traits : Névrosisme, Extraversion, Ouverture, Agréabilité, Conscienciosité."
        ),
        instructions=(
            "Pour chaque affirmation, indiquez à quel point elle vous décrit de manière précise. "
            "Répondez spontanément en fonction de ce que vous êtes réellement, et non de ce que vous aimeriez être. "
            "1 = Pas du tout précis  5 = Très précis."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=120,
        is_active=True,
        status="VALIDATED",
        license="PUBLIC_DOMAIN",
        validation_notes=(
            "Items issus de l'IPIP-120 IRT-Based (Maples et al., 2014 — Psychological Assessment). "
            "Domaine public — Goldberg (1999) a explicitement libéré l'IPIP. "
            "⚠️ ALPHA HARMONY : non étalonné sur population maritime. "
            "Les percentiles du moteur sont calculés sur le pool candidats interne (Tukey). "
            "Normes validées requises à N ≥ 150 profils. "
            "Biais connu : items N en fin de passation exposés à la fatigue de réponse — "
            "randomiser l'ordre des modules entre candidats."
        ),
        modules_config=[
            {"index": 0, "name": "Stabilité émotionnelle", "trait": "neuroticism",
             "n_items": 24, "duration_min": 7, "priority": "SAFETY",
             "description": "Module prioritaire — alimente la safety barrier du moteur P-E Fit"},
            {"index": 1, "name": "Conscienciosité", "trait": "conscientiousness",
             "n_items": 24, "duration_min": 7, "priority": "SAFETY",
             "description": "Module prioritaire — alimente la safety barrier et le P-J D-A Fit"},
            {"index": 2, "name": "Agréabilité", "trait": "agreeableness",
             "n_items": 24, "duration_min": 7, "priority": "SAFETY",
             "description": "Module prioritaire — alimente la safety barrier et le P-T Fit"},
            {"index": 3, "name": "Extraversion", "trait": "extraversion",
             "n_items": 24, "duration_min": 7, "priority": "STANDARD"},
            {"index": 4, "name": "Ouverture", "trait": "openness",
             "n_items": 24, "duration_min": 7, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    _TRAIT_MODULE = {
        "neuroticism":       0,
        "conscientiousness": 1,
        "agreeableness":     2,
        "extraversion":      3,
        "openness":          4,
    }

    for q in IPIP120_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            text=q["text"],
            question_type="likert",
            trait=q["trait"],
            reverse=q["reverse"],
            order=q["order"],
            correct_answer=None,
            options=None,
            module_index=_TRAIT_MODULE.get(q["trait"]),
        ))
    await db.flush()
    print(f"  [ipip120] Créé (id={catalogue.id}, {len(IPIP120_QUESTIONS)} questions)")
    return catalogue

async def delete_ipip120(db: AsyncSession) -> None:
    print("  [ipip120] Deleting...")
    result = await db.execute(
        select(TestCatalogue.id).where(TestCatalogue.name == _CATALOGUE_NAME)
    )
    cat_id = result.scalar_one_or_none()
    if cat_id:
        await db.execute(delete(Question).where(Question.test_id == cat_id))
        await db.execute(delete(TestCatalogue).where(TestCatalogue.id == cat_id))
    await db.commit()
    print("  [ipip120] Done.")

async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_ipip120(db)
        await seed_ipip120(db)
        await db.commit()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(_main())