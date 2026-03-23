# app/seed/tests/questions/etalons/hexaco60.py
"""
IPIP-HEXACO-60 — Big Six Personality Inventory

60 items Likert 1-5 évaluant les 6 dimensions du modèle HEXACO.
Instrument de référence (étalon) — domaine public IPIP.

Source : Ashton, M.C., Lee, K., & Goldberg, L.R. (2007).
    The IPIP-HEXACO scales: An alternative, public-domain measure of the
    personality constructs in the HEXACO model. Personality and Individual
    Differences, 42(8), 1515–1526.

Clé de scoring : ipip.ori.org/newHEXACO_PI_key.htm

⚠️ ÉTALON R&D — Ne pas déployer en production commerciale.
   Usage calibration interne uniquement. Domaine public IPIP.

    seed_hexaco60(db)   → idempotent, retourne le TestCatalogue
    delete_hexaco60(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.etalons.hexaco60
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

HEXACO60_QUESTIONS = [
    # ── Honesty-Humility (H) — 10 items ──────────────────────────────────────
    # Facettes : Sincerity (H:Sinc) | Fairness (H:Fair) | Greed-Avoidance (H:Gree) | Modesty (H:Mode)
    # Source exacte : ipip.ori.org/newHEXACO_PI_key.htm
    {"order":  1, "trait": "H", "reverse": False,
     "text": "Don't pretend to be more than I am."},
    {"order":  2, "trait": "H", "reverse": True,
     "text": "Use flattery to get ahead."},
    {"order":  3, "trait": "H", "reverse": True,
     "text": "Put on a show to impress people."},
    {"order":  4, "trait": "H", "reverse": False,
     "text": "Would never take things that aren't mine."},
    {"order":  5, "trait": "H", "reverse": True,
     "text": "Cheat to get ahead."},
    {"order":  6, "trait": "H", "reverse": False,
     "text": "Try to follow the rules."},
    {"order":  7, "trait": "H", "reverse": True,
     "text": "Love luxury."},
    {"order":  8, "trait": "H", "reverse": True,
     "text": "Am mainly interested in money."},
    {"order":  9, "trait": "H", "reverse": False,
     "text": "Don't think that I'm better than other people."},
    {"order": 10, "trait": "H", "reverse": True,
     "text": "Believe that I am better than others."},

    # ── Emotionality (E) — 10 items ───────────────────────────────────────────
    # Facettes : Fearfulness (E:Fear) | Anxiety (E:Anxi) | Dependence (E:Depe) | Sentimentality (E:Sent)
    {"order": 11, "trait": "E", "reverse": False,
     "text": "Am a physical coward."},
    {"order": 12, "trait": "E", "reverse": False,
     "text": "Begin to panic when there is danger."},
    {"order": 13, "trait": "E", "reverse": True,
     "text": "Like to do frightening things."},
    {"order": 14, "trait": "E", "reverse": False,
     "text": "Worry about things."},
    {"order": 15, "trait": "E", "reverse": True,
     "text": "Rarely worry."},
    {"order": 16, "trait": "E", "reverse": False,
     "text": "Need reassurance."},
    {"order": 17, "trait": "E", "reverse": False,
     "text": "Need the approval of others."},
    {"order": 18, "trait": "E", "reverse": False,
     "text": "Feel others' emotions."},
    {"order": 19, "trait": "E", "reverse": False,
     "text": "Immediately feel sad when hearing of an unhappy event."},
    {"order": 20, "trait": "E", "reverse": True,
     "text": "Seldom get emotional."},

    # ── eXtraversion (X) — 10 items ───────────────────────────────────────────
    # Facettes : Expressiveness (X:Expr) | Social Boldness (X:SocB) | Sociability (X:Soci) | Liveliness (X:Live)
    {"order": 21, "trait": "X", "reverse": False,
     "text": "Talk a lot."},
    {"order": 22, "trait": "X", "reverse": True,
     "text": "Don't talk a lot."},
    {"order": 23, "trait": "X", "reverse": True,
     "text": "Say little."},
    {"order": 24, "trait": "X", "reverse": False,
     "text": "Am good at making impromptu speeches."},
    {"order": 25, "trait": "X", "reverse": True,
     "text": "Would be afraid to give a speech in public."},
    {"order": 26, "trait": "X", "reverse": False,
     "text": "Usually like to spend my free time with people."},
    {"order": 27, "trait": "X", "reverse": True,
     "text": "Rarely enjoy being with people."},
    {"order": 28, "trait": "X", "reverse": False,
     "text": "Am usually active and full of energy."},
    {"order": 29, "trait": "X", "reverse": True,
     "text": "Tire out quickly."},
    {"order": 30, "trait": "X", "reverse": False,
     "text": "Smile a lot."},

    # ── Agreeableness (A) — 10 items ──────────────────────────────────────────
    # Facettes : Forgiveness (A:Forg) | Gentleness (A:Gent) | Flexibility (A:Flex) | Patience (A:Pati)
    {"order": 31, "trait": "A", "reverse": False,
     "text": "Am inclined to forgive others."},
    {"order": 32, "trait": "A", "reverse": True,
     "text": "Hold a grudge."},
    {"order": 33, "trait": "A", "reverse": True,
     "text": "Get back at people who insult me."},
    {"order": 34, "trait": "A", "reverse": False,
     "text": "Accept people as they are."},
    {"order": 35, "trait": "A", "reverse": True,
     "text": "Find fault with everything."},
    {"order": 36, "trait": "A", "reverse": False,
     "text": "Adjust easily."},
    {"order": 37, "trait": "A", "reverse": True,
     "text": "React strongly to criticism."},
    {"order": 38, "trait": "A", "reverse": True,
     "text": "Am hard to reason with."},
    {"order": 39, "trait": "A", "reverse": False,
     "text": "Am usually a patient person."},
    {"order": 40, "trait": "A", "reverse": True,
     "text": "Get angry easily."},

    # ── Conscientiousness (C) — 10 items ──────────────────────────────────────
    # Facettes : Organization (C:Orga) | Diligence (C:Dili) | Perfectionism (C:Perf) | Prudence (C:Prud)
    {"order": 41, "trait": "C", "reverse": False,
     "text": "Keep things tidy."},
    {"order": 42, "trait": "C", "reverse": True,
     "text": "Leave a mess in my room."},
    {"order": 43, "trait": "C", "reverse": False,
     "text": "Work hard."},
    {"order": 44, "trait": "C", "reverse": False,
     "text": "Get started quickly on doing a job."},
    {"order": 45, "trait": "C", "reverse": True,
     "text": "Do just enough work to get by."},
    {"order": 46, "trait": "C", "reverse": False,
     "text": "Pay attention to details."},
    {"order": 47, "trait": "C", "reverse": False,
     "text": "Continue until everything is perfect."},
    {"order": 48, "trait": "C", "reverse": True,
     "text": "Pay too little attention to details."},
    {"order": 49, "trait": "C", "reverse": False,
     "text": "Make plans and stick to them."},
    {"order": 50, "trait": "C", "reverse": True,
     "text": "Jump into things without thinking."},

    # ── Openness to Experience (O) — 10 items ─────────────────────────────────
    # Facettes : Aesthetic Appreciation (O:AesA) | Inquisitiveness (O:Inqu) | Creativity (O:Crea) | Unconventionality (O:Unco)
    {"order": 51, "trait": "O", "reverse": False,
     "text": "Believe in the importance of art."},
    {"order": 52, "trait": "O", "reverse": False,
     "text": "See beauty in things that others might not notice."},
    {"order": 53, "trait": "O", "reverse": True,
     "text": "Do not like art."},
    {"order": 54, "trait": "O", "reverse": False,
     "text": "Am interested in science."},
    {"order": 55, "trait": "O", "reverse": False,
     "text": "Love to read challenging material."},
    {"order": 56, "trait": "O", "reverse": False,
     "text": "Have a vivid imagination."},
    {"order": 57, "trait": "O", "reverse": False,
     "text": "Am full of ideas."},
    {"order": 58, "trait": "O", "reverse": True,
     "text": "Do not have a good imagination."},
    {"order": 59, "trait": "O", "reverse": False,
     "text": "Am considered to be kind of eccentric."},
    {"order": 60, "trait": "O", "reverse": True,
     "text": "Would hate to be considered odd or strange."},
]

_CATALOGUE_NAME = "IPIP-HEXACO-60"

_TRAIT_MODULE = {
    "H": 0,
    "E": 1,
    "X": 2,
    "A": 3,
    "C": 4,
    "O": 5,
}


async def seed_hexaco60(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent de l'IPIP-HEXACO-60."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [hexaco60] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "IPIP-HEXACO-60 — 60 items évaluant les 6 dimensions du modèle HEXACO : "
            "Honesty-Humility (H), Emotionality (E), eXtraversion (X), Agreeableness (A), "
            "Conscientiousness (C), Openness to Experience (O). "
            "10 items par dimension. Likert 1-5. "
            "Remplace l'IPIP-120 Big Five pour la version alpha Radiant Analytics. "
            "Durée estimée : 8–12 minutes."
        ),
        instructions=(
            "For each statement, indicate how accurately it describes you. "
            "Answer spontaneously based on who you really are, not who you would like to be. "
            "1 = Strongly Disagree  →  5 = Strongly Agree."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=60,
        is_active=True,
        status="ETALON",
        license="IPIP_PUBLIC_DOMAIN",
        domain=CatalogueDomain.personality,
        validation_notes=(
            "IPIP-HEXACO-60 — Ashton, M.C., Lee, K., & Goldberg, L.R. (2007). "
            "The IPIP-HEXACO scales: An alternative, public-domain measure of the personality "
            "constructs in the HEXACO model. Personality and Individual Differences, 42(8), 1515–1526. "
            "Domaine public — IPIP (Goldberg, 1999). Utilisation libre sans restriction. "
            "Clé de scoring : ipip.ori.org/newHEXACO_PI_key.htm. "
            "⚠️ ÉTALON R&D UNIQUEMENT — ne pas déployer en production commerciale. "
            "Non étalonné sur population maritime. "
            "Alphas attendus : H 0.74–0.79 | E 0.78–0.83 | X 0.76–0.82 | "
            "A 0.71–0.76 | C 0.77–0.82 | O 0.75–0.80 (Ashton & Lee, 2009). "
            "Score 0–100 par dimension : (mean − 1) / 4 * 100 après recodage items [R]. "
            "Items [R] recodés : 6 − valeur (échelle 1-5 → 5→1, 4→2, 3→3, 2→4, 1→5)."
        ),
        modules_config=[
            {"index": 0, "name": "Honesty-Humility", "trait": "H",
             "n_items": 10, "duration_min": 2, "priority": "SAFETY",
             "description": "Sincérité, équité, modestie — détection comportements contre-productifs (CWB)"},
            {"index": 1, "name": "Emotionality", "trait": "E",
             "n_items": 10, "duration_min": 2, "priority": "SAFETY",
             "description": "Peur, anxiété, dépendance émotionnelle — vigilance ICE (E modéré optimal)"},
            {"index": 2, "name": "eXtraversion", "trait": "X",
             "n_items": 10, "duration_min": 2, "priority": "STANDARD",
             "description": "Estime sociale, sociabilité, vivacité"},
            {"index": 3, "name": "Agreeableness", "trait": "A",
             "n_items": 10, "duration_min": 2, "priority": "SAFETY",
             "description": "Indulgence, douceur, patience — min(A) utilisé dans formule Bell (2007)"},
            {"index": 4, "name": "Conscientiousness", "trait": "C",
             "n_items": 10, "duration_min": 2, "priority": "SAFETY",
             "description": "Organisation, diligence, prudence — meilleur prédicteur performance contextuelle"},
            {"index": 5, "name": "Openness to Experience", "trait": "O",
             "n_items": 10, "duration_min": 2, "priority": "STANDARD",
             "description": "Curiosité, créativité, adaptabilité cognitive"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in HEXACO60_QUESTIONS:
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
    print(f"  [hexaco60] Seeded '{_CATALOGUE_NAME}' ({len(HEXACO60_QUESTIONS)} questions)")
    return catalogue


async def delete_hexaco60(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [hexaco60] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_hexaco60(db)
        await seed_hexaco60(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
