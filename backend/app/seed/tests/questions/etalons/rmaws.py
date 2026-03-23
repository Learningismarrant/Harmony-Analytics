# app/seed/tests/questions/etalons/rmaws.py
"""
Work Motivation Scale — R-MAWS (Gagné et al., 2010 / 2015).

19 items Likert 1-7. Self-Determination Theory (Deci & Ryan).
6 sous-échelles : extrinsic_social, extrinsic_material, introjected,
                  identified, intrinsic, amotivation.
Correction : 1 item extrinsic_material remplacé (sécurité → rémunération).

    seed_rmaws(db)   → idempotent, retourne le TestCatalogue
    delete_rmaws(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.etalons.rmaws
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

RMAWS_QUESTIONS = [
    # ── Extrinsic Social ──────────────────────────────────────────────────────
    {"order": 1,  "trait": "extrinsic_social",   "reverse": False, "text": "To get others' approval."},
    {"order": 2,  "trait": "extrinsic_social",   "reverse": False, "text": "Because others will respect me more."},
    {"order": 3,  "trait": "extrinsic_social",   "reverse": False, "text": "To avoid being criticized by others."},

    # ── Extrinsic Material ────────────────────────────────────────────────────
    {"order": 4,  "trait": "extrinsic_material", "reverse": False, "text": "Because others will reward me financially only if I put enough effort."},
    {"order": 5,  "trait": "extrinsic_material", "reverse": False, "text": "Because the financial compensation I receive is important to me."},
    {"order": 6,  "trait": "extrinsic_material", "reverse": False, "text": "Because I risk losing my job if I don't put enough effort in it."},

    # ── Introjected ───────────────────────────────────────────────────────────
    {"order": 7,  "trait": "introjected",        "reverse": False, "text": "Because I have to prove to myself that I can."},
    {"order": 8,  "trait": "introjected",        "reverse": False, "text": "Because it makes me feel proud of myself."},
    {"order": 9,  "trait": "introjected",        "reverse": False, "text": "Because otherwise I will feel ashamed of myself."},
    {"order": 10, "trait": "introjected",        "reverse": False, "text": "Because otherwise I will feel bad about myself."},

    # ── Identified ────────────────────────────────────────────────────────────
    {"order": 11, "trait": "identified",         "reverse": False, "text": "Because I personally consider it important to put efforts in this job."},
    {"order": 12, "trait": "identified",         "reverse": False, "text": "Because putting efforts in this job aligns with my personal values."},
    {"order": 13, "trait": "identified",         "reverse": False, "text": "Because putting efforts in this job has personal significance to me."},

    # ── Intrinsic ─────────────────────────────────────────────────────────────
    {"order": 14, "trait": "intrinsic",          "reverse": False, "text": "Because I have fun doing my job."},
    {"order": 15, "trait": "intrinsic",          "reverse": False, "text": "Because what I do in my work is exciting."},
    {"order": 16, "trait": "intrinsic",          "reverse": False, "text": "Because the work I do is interesting."},

    # ── Amotivation ───────────────────────────────────────────────────────────
    {"order": 17, "trait": "amotivation",        "reverse": False, "text": "I don't, because I really feel that I'm wasting my time at work."},
    {"order": 18, "trait": "amotivation",        "reverse": False, "text": "I do little because I don't think this work is worth putting efforts into."},
    {"order": 19, "trait": "amotivation",        "reverse": False, "text": "I don't know why I'm doing this job, it's pointless work."},
]

_CATALOGUE_NAME = "Work Motivation Scale (R-MAWS)"


async def seed_rmaws(db: AsyncSession) -> TestCatalogue:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [rmaws] Déjà présent (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Échelle de motivation au travail — 19 items Likert 1-7. "
            "Basée sur la Self-Determination Theory (Deci & Ryan) et validée par "
            "Gagné et al. (2010, 2015). "
            "6 sous-échelles : motivation extrinsèque sociale, matérielle, "
            "introjectée, identifiée, intrinsèque, et amotivation. "
            "Durée estimée : 8-12 minutes."
        ),
        instructions=(
            "Les énoncés suivants décrivent des raisons pour lesquelles vous "
            "mettez des efforts dans votre travail actuel ou visé. "
            "Pour chaque raison, indiquez dans quelle mesure elle correspond à votre cas. "
            "1 = Pas du tout   7 = Exactement."
        ),
        test_type="likert",
        max_score_per_question=7,
        n_questions=19,
        is_active=True,
        status="ETALON",
        license="COPYRIGHT_RESEARCH_ONLY",
        domain=CatalogueDomain.motivation,
        validation_notes=(
            "⚠️ R-MAWS (Gagné et al. 2010) — Copyright CSDT. Usage autorisé R&D interne uniquement. "
            "Ne pas déployer en production commerciale sans accord de licence. "
            "Étalon de calibration pour SDT-6 propriétaire. "
            "R-MAWS — Gagné, M., Forest, J., Gilbert, M.-H., Aubé, C., Morin, E., & Malorni, A. (2010). "
            "The Motivation at Work Scale. Educational and Psychological Measurement, 70(4), 628-646. "
            "⚠️ ALPHA RADIANT : profils idéaux par poste calibrés par jugement SME Phase 0, "
            "non validés empiriquement. Pondération motivation_score = 0.15 dans pj_aggregate "
            "jusqu'à N ≥ 150 profils (recommandation head-of-science 2026-03). "
            "Validité discriminante introjected/identified à surveiller (r ≈ .40-.60)."
        ),
        modules_config=[
            {"index": 0, "name": "Régulations contrôlées",
             "traits": ["extrinsic_social", "extrinsic_material", "introjected"],
             "n_items": 10, "duration_min": 4, "priority": "STANDARD"},
            {"index": 1, "name": "Régulations autonomes",
             "traits": ["identified", "intrinsic", "amotivation"],
             "n_items": 9, "duration_min": 4, "priority": "STANDARD"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    _TRAIT_MODULE = {
        "extrinsic_social":   0,
        "extrinsic_material": 0,
        "introjected":        0,
        "identified":         1,
        "intrinsic":          1,
        "amotivation":        1,
    }

    for q in RMAWS_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            text=q["text"],
            question_type="likert_7",
            trait=q["trait"],
            reverse=q["reverse"],
            order=q["order"],
            correct_answer=None,
            options=None,
            module_index=_TRAIT_MODULE.get(q["trait"]),
        ))
    await db.flush()
    print(f"  [rmaws] Créé (id={catalogue.id}, {len(RMAWS_QUESTIONS)} questions)")
    return catalogue


async def delete_rmaws(db: AsyncSession) -> None:
    print("  [rmaws] Deleting...")
    result = await db.execute(
        select(TestCatalogue.id).where(TestCatalogue.name == _CATALOGUE_NAME)
    )
    cat_id = result.scalar_one_or_none()
    if cat_id:
        await db.execute(delete(Question).where(Question.test_id == cat_id))
        await db.execute(delete(TestCatalogue).where(TestCatalogue.id == cat_id))
    await db.commit()
    print("  [rmaws] Done.")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_rmaws(db)
        await seed_rmaws(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
