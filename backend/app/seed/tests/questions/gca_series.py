# app/seed/tests/questions/gca_series.py
"""
GCA Séries Numériques — Q2 Raisonnement Quantitatif

30 items QCM évaluant le raisonnement quantitatif (Gq — modèle CHC, Carroll 1993).
Format : série de nombres, trouver le terme suivant. 4 choix (A/B/C/D).
Difficulté progressive : items 1–10 faciles, 11–20 moyens, 21–30 difficiles.
Temps cible : ~16 secondes par item (~8 min pour 30 items).

⚠️ NOTE P2 : Les instruments QCM visuels (matrices et rotation 3D) sont en attente
d'implémentation graphique côté frontend :
  - gca_matrices.py (HMR-24 visuospatial 2D) : rendu Raven-like, P2
  - gca_rotation.py (rotation 3D) : rendu Three.js/WebGL, P2
Ces fichiers NE SONT PAS créés dans cette version — uniquement les séries numériques
sont seedées, qui n'ont pas besoin de rendu graphique spécifique.

    seed_gca_series(db)   → idempotent, retourne le TestCatalogue
    delete_gca_series(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.gca_series
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

_CATALOGUE_NAME = "GCA Séries Numériques"

GCA_SERIES_QUESTIONS = [
    # ── Niveau Facile (Items 01–10) ────────────────────────────────────────────
    {
        "order": 1, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 5, 8, 11, __",
        "options": [{"key": "A", "text": "13"}, {"key": "B", "text": "14"}, {"key": "C", "text": "15"}, {"key": "D", "text": "12"}],
        "correct_answer": "B",
    },
    {
        "order": 2, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 3, 10, 17, 24, __",
        "options": [{"key": "A", "text": "29"}, {"key": "B", "text": "30"}, {"key": "C", "text": "31"}, {"key": "D", "text": "32"}],
        "correct_answer": "C",
    },
    {
        "order": 3, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 40, 36, 32, 28, __",
        "options": [{"key": "A", "text": "22"}, {"key": "B", "text": "25"}, {"key": "C", "text": "26"}, {"key": "D", "text": "24"}],
        "correct_answer": "D",
    },
    {
        "order": 4, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 2, 4, 8, __",
        "options": [{"key": "A", "text": "12"}, {"key": "B", "text": "14"}, {"key": "C", "text": "16"}, {"key": "D", "text": "18"}],
        "correct_answer": "C",
    },
    {
        "order": 5, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 6, 18, 54, __",
        "options": [{"key": "A", "text": "108"}, {"key": "B", "text": "144"}, {"key": "C", "text": "162"}, {"key": "D", "text": "180"}],
        "correct_answer": "C",
    },
    {
        "order": 6, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 4, 9, 16, __",
        "options": [{"key": "A", "text": "20"}, {"key": "B", "text": "23"}, {"key": "C", "text": "25"}, {"key": "D", "text": "27"}],
        "correct_answer": "C",
    },
    {
        "order": 7, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 5, 10, 15, 20, 25, __",
        "options": [{"key": "A", "text": "28"}, {"key": "B", "text": "29"}, {"key": "C", "text": "30"}, {"key": "D", "text": "31"}],
        "correct_answer": "C",
    },
    {
        "order": 8, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 60, 54, 48, 42, __",
        "options": [{"key": "A", "text": "34"}, {"key": "B", "text": "35"}, {"key": "C", "text": "36"}, {"key": "D", "text": "38"}],
        "correct_answer": "C",
    },
    {
        "order": 9, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 1, 2, 3, 5, __",
        "options": [{"key": "A", "text": "6"}, {"key": "B", "text": "7"}, {"key": "C", "text": "8"}, {"key": "D", "text": "9"}],
        "correct_answer": "C",
    },
    {
        "order": 10, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 64, 32, 16, 8, __",
        "options": [{"key": "A", "text": "2"}, {"key": "B", "text": "3"}, {"key": "C", "text": "4"}, {"key": "D", "text": "6"}],
        "correct_answer": "C",
    },

    # ── Niveau Moyen (Items 11–20) ─────────────────────────────────────────────
    {
        "order": 11, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 2, 4, 7, 11, __",
        "options": [{"key": "A", "text": "14"}, {"key": "B", "text": "15"}, {"key": "C", "text": "16"}, {"key": "D", "text": "17"}],
        "correct_answer": "C",
    },
    {
        "order": 12, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 2, 4, 6, 7, 10, 10, __",
        "options": [{"key": "A", "text": "12"}, {"key": "B", "text": "13"}, {"key": "C", "text": "14"}, {"key": "D", "text": "15"}],
        "correct_answer": "C",
    },
    {
        "order": 13, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 0, 3, 9, 18, 30, __",
        "options": [{"key": "A", "text": "42"}, {"key": "B", "text": "44"}, {"key": "C", "text": "45"}, {"key": "D", "text": "48"}],
        "correct_answer": "C",
    },
    {
        "order": 14, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 5, 7, 12, 19, __",
        "options": [{"key": "A", "text": "28"}, {"key": "B", "text": "30"}, {"key": "C", "text": "31"}, {"key": "D", "text": "33"}],
        "correct_answer": "C",
    },
    {
        "order": 15, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 3, 6, 9, 18, 21, __",
        "options": [{"key": "A", "text": "24"}, {"key": "B", "text": "38"}, {"key": "C", "text": "42"}, {"key": "D", "text": "44"}],
        "correct_answer": "C",
    },
    {
        "order": 16, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 5, 10, 17, 26, __",
        "options": [{"key": "A", "text": "33"}, {"key": "B", "text": "35"}, {"key": "C", "text": "37"}, {"key": "D", "text": "39"}],
        "correct_answer": "C",
    },
    {
        "order": 17, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, −2, 4, −8, 16, __",
        "options": [{"key": "A", "text": "−24"}, {"key": "B", "text": "−30"}, {"key": "C", "text": "−32"}, {"key": "D", "text": "32"}],
        "correct_answer": "C",
    },
    {
        "order": 18, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 3, 4, 6, 9, 13, __",
        "options": [{"key": "A", "text": "16"}, {"key": "B", "text": "17"}, {"key": "C", "text": "18"}, {"key": "D", "text": "19"}],
        "correct_answer": "C",
    },
    {
        "order": 19, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 1, 2, 3, 4, 9, 8, __",
        "options": [{"key": "A", "text": "16"}, {"key": "B", "text": "24"}, {"key": "C", "text": "27"}, {"key": "D", "text": "32"}],
        "correct_answer": "C",
    },
    {
        "order": 20, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 0.5, 2, 3.5, 5, 6.5, __",
        "options": [{"key": "A", "text": "7"}, {"key": "B", "text": "7.5"}, {"key": "C", "text": "8"}, {"key": "D", "text": "8.5"}],
        "correct_answer": "C",
    },

    # ── Niveau Difficile (Items 21–30) ─────────────────────────────────────────
    {
        "order": 21, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 0, 1, 4, 10, 20, 35, __",
        "options": [{"key": "A", "text": "50"}, {"key": "B", "text": "52"}, {"key": "C", "text": "56"}, {"key": "D", "text": "60"}],
        "correct_answer": "C",
    },
    {
        "order": 22, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 20, 19, 21, 16, 24, 11, __",
        "options": [{"key": "A", "text": "26"}, {"key": "B", "text": "27"}, {"key": "C", "text": "29"}, {"key": "D", "text": "32"}],
        "correct_answer": "C",
    },
    {
        "order": 23, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 1, 2, 4, 4, 9, 8, 16, __",
        "options": [{"key": "A", "text": "12"}, {"key": "B", "text": "16"}, {"key": "C", "text": "25"}, {"key": "D", "text": "32"}],
        "correct_answer": "B",
    },
    {
        "order": 24, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 4, 8, 11, 33, 37, __",
        "options": [{"key": "A", "text": "74"}, {"key": "B", "text": "148"}, {"key": "C", "text": "185"}, {"key": "D", "text": "222"}],
        "correct_answer": "C",
    },
    {
        "order": 25, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 3, 5, 7, 9, 11, __",
        "options": [{"key": "A", "text": "12"}, {"key": "B", "text": "13"}, {"key": "C", "text": "14"}, {"key": "D", "text": "15"}],
        "correct_answer": "B",
    },
    {
        "order": 26, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : −15, −12, −8, −3, 3, __",
        "options": [{"key": "A", "text": "8"}, {"key": "B", "text": "9"}, {"key": "C", "text": "10"}, {"key": "D", "text": "12"}],
        "correct_answer": "C",
    },
    {
        "order": 27, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 4, 14, 6, 24, 9, 34, 13.5, __",
        "options": [{"key": "A", "text": "40"}, {"key": "B", "text": "42"}, {"key": "C", "text": "44"}, {"key": "D", "text": "46"}],
        "correct_answer": "C",
    },
    {
        "order": 28, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 2, 2, 4, 8, 2, __",
        "options": [{"key": "A", "text": "4"}, {"key": "B", "text": "6"}, {"key": "C", "text": "8"}, {"key": "D", "text": "16"}],
        "correct_answer": "B",
    },
    {
        "order": 29, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 1, 2, 5, 14, 41, __",
        "options": [{"key": "A", "text": "100"}, {"key": "B", "text": "113"}, {"key": "C", "text": "122"}, {"key": "D", "text": "128"}],
        "correct_answer": "C",
    },
    {
        "order": 30, "trait": "GCA_Gf", "reverse": False,
        "text": "Quelle est la valeur suivante dans la série : 2, 3, 7, 14, 25, 42, __",
        "options": [{"key": "A", "text": "58"}, {"key": "B", "text": "61"}, {"key": "C", "text": "65"}, {"key": "D", "text": "70"}],
        "correct_answer": "C",
    },
]


async def seed_gca_series(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent des GCA Séries Numériques."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [gca_series] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "GCA Séries Numériques — 30 items QCM évaluant le raisonnement quantitatif (Gq). "
            "Format : série de nombres, trouver le terme suivant. 4 choix (A/B/C/D). "
            "Difficulté progressive : items 1–10 faciles, 11–20 moyens, 21–30 difficiles. "
            "Ancré sur le modèle CHC (Carroll 1993). "
            "Temps cible : ~8 minutes (16 s/item en moyenne)."
        ),
        instructions=(
            "Pour chaque série de nombres, trouvez la valeur qui devrait suivre logiquement. "
            "Choisissez la réponse correcte parmi les 4 options proposées. "
            "Travaillez rapidement mais avec précision — chaque seconde compte."
        ),
        test_type="qcm",
        max_score_per_question=1,
        n_questions=30,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Non dérivés d'instruments propriétaires tiers. "
            "α Cronbach cible : ≥ 0.80 sur 30 items, ≥ 0.65 par niveau (10 items). "
            "Calibration temps : prévoir prétest n=30–50 pour ajuster les limites par item. "
            "Référence : Carroll, J.B. (1993). Human cognitive abilities. Cambridge University Press."
        ),
        modules_config=[
            {"index": 0, "name": "Niveau Facile", "trait": "GCA_Gf",
             "n_items": 10, "duration_min": 3, "priority": "STANDARD",
             "description": "Items 1–10 : progressions arithmétiques, géométriques simples, carrés"},
            {"index": 1, "name": "Niveau Moyen", "trait": "GCA_Gf",
             "n_items": 10, "duration_min": 3, "priority": "STANDARD",
             "description": "Items 11–20 : différences de second ordre, alternances, suites entrelacées"},
            {"index": 2, "name": "Niveau Difficile", "trait": "GCA_Gf",
             "n_items": 10, "duration_min": 4, "priority": "STANDARD",
             "description": "Items 21–30 : structures complexes, nombres triangulaires, progressions géométriques des différences"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in GCA_SERIES_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="qcm",
            trait=q["trait"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            reverse=False,
        ))

    await db.flush()
    print(f"  [gca_series] Seeded '{_CATALOGUE_NAME}' ({len(GCA_SERIES_QUESTIONS)} questions)")
    return catalogue


async def delete_gca_series(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [gca_series] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_gca_series(db)
        await seed_gca_series(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
