# app/seed/tests/questions/maritime_tolerance.py
"""
Tolérance ICE Physique — Q7 Physical Fit

24 items Likert 1-5 évaluant la self-efficacy perçue face aux exigences
physiques et environnementales d'un environnement ICE maritime.
6 domaines × 4 items chacun.

Construct : capacité PERÇUE (Bandura 1997) — NON la capacité réelle (ENG1).
Ancre : "Dans quelle mesure êtes-vous confiant(e) dans votre capacité à..."
Échelle : 1 = "Pas du tout confiant(e)" → 5 = "Totalement confiant(e)"

Domaines : houle | sommeil | climat | confinement | mal_de_mer | isolement

    seed_maritime_tolerance(db)   → idempotent, retourne le TestCatalogue
    delete_maritime_tolerance(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.maritime_tolerance
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

_CATALOGUE_NAME = "Tolérance ICE Physique"

METS_QUESTIONS = [
    # ── Domaine A — Endurance physique en conditions de houle ─────────────────
    {"order":  1, "trait": "houle", "reverse": False,
     "text": "...maintenir votre efficacité physique lors d'une traversée de plusieurs jours en mer formée ou agitée ?"},
    {"order":  2, "trait": "houle", "reverse": False,
     "text": "...continuer à exécuter vos tâches techniques correctement lorsque le bateau gîte fortement ou roule de manière continue ?"},
    {"order":  3, "trait": "houle", "reverse": False,
     "text": "...récupérer physiquement assez vite entre deux quarts pour rester pleinement opérationnel(le) dans des conditions de mer difficiles ?"},
    {"order":  4, "trait": "houle", "reverse": False,
     "text": "...rester physiquement actif(ve) et réactif(ve) pendant plusieurs heures de quart consécutives lorsque les conditions météorologiques sont mauvaises ?"},

    # ── Domaine B — Tolérance au manque de sommeil / quarts de nuit ───────────
    {"order":  5, "trait": "sommeil", "reverse": False,
     "text": "...maintenir votre vigilance et votre précision lors d'un quart de nuit après plusieurs nuits de sommeil fragmenté ?"},
    {"order":  6, "trait": "sommeil", "reverse": False,
     "text": "...accomplir des tâches qui requièrent de la concentration après avoir dormi moins de cinq heures consécutives ?"},
    {"order":  7, "trait": "sommeil", "reverse": False,
     "text": "...vous adapter rapidement à une rotation de quarts modifiée (par exemple, passage d'un quart de jour à un quart de nuit) sans que cela affecte significativement vos performances ?"},
    {"order":  8, "trait": "sommeil", "reverse": False,
     "text": "...maintenir votre sécurité et celle des autres à bord dans des situations où vous n'avez pas pu dormir suffisamment pendant plusieurs jours consécutifs ?"},

    # ── Domaine C — Résistance aux conditions climatiques extrêmes ────────────
    {"order":  9, "trait": "climat", "reverse": False,
     "text": "...travailler efficacement sur le pont exposé par températures froides (moins de 5°C) avec du vent et de la pluie ?"},
    {"order": 10, "trait": "climat", "reverse": False,
     "text": "...maintenir votre niveau de performance physique lors de missions en zone tropicale par forte chaleur et humidité élevée ?"},
    {"order": 11, "trait": "climat", "reverse": False,
     "text": "...effectuer des tâches de pont ou de maintenance en extérieur dans des conditions climatiques difficiles (pluie, vent fort, mer agitée) pendant plusieurs heures ?"},
    {"order": 12, "trait": "climat", "reverse": False,
     "text": "...vous adapter rapidement à des écarts importants de température entre l'intérieur du navire et l'extérieur lors de navigations en zones climatiquement contrastées ?"},

    # ── Domaine D — Performance en environnement confiné ─────────────────────
    {"order": 13, "trait": "confinement", "reverse": False,
     "text": "...rester efficace et concentré(e) après plusieurs semaines passées dans un espace de vie réduit partagé avec l'équipage ?"},
    {"order": 14, "trait": "confinement", "reverse": False,
     "text": "...maintenir votre niveau de performance professionnelle dans un environnement où vous disposez de peu d'espace personnel ?"},
    {"order": 15, "trait": "confinement", "reverse": False,
     "text": "...gérer la promiscuité permanente avec vos coéquipiers (partage de cabine, repas collectifs, absence d'intimité) sans que cela affecte votre efficacité au travail ?"},
    {"order": 16, "trait": "confinement", "reverse": False,
     "text": "...rester productif(ve) et créatif(ve) dans la résolution de problèmes à bord même après plusieurs semaines sans sortir du navire ?"},

    # ── Domaine E — Gestion du mal de mer ────────────────────────────────────
    {"order": 17, "trait": "mal_de_mer", "reverse": False,
     "text": "...continuer à travailler de façon sûre et efficace même lorsque vous vous sentez nauséeux(se) en mer formée ?"},
    {"order": 18, "trait": "mal_de_mer", "reverse": False,
     "text": "...gérer les symptômes du mal de mer (nausées, vertiges) sans que cela compromette votre sécurité à bord ?"},
    {"order": 19, "trait": "mal_de_mer", "reverse": False,
     "text": "...récupérer rapidement d'un épisode de mal de mer et reprendre vos fonctions dans un délai raisonnable ?"},
    {"order": 20, "trait": "mal_de_mer", "reverse": False,
     "text": "...maintenir votre niveau d'efficacité lors de longues traversées en mer agitée, même si vous êtes sujet(te) aux inconforts du roulis ?"},

    # ── Domaine F — Tolérance à l'isolement physique prolongé ─────────────────
    {"order": 21, "trait": "isolement", "reverse": False,
     "text": "...rester psychologiquement stable lors de traversées ou de missions impliquant plusieurs semaines sans escale ni contact avec la terre ?"},
    {"order": 22, "trait": "isolement", "reverse": False,
     "text": "...maintenir votre bien-être mental dans une situation où les communications avec votre famille et vos amis sont limitées ou intermittentes ?"},
    {"order": 23, "trait": "isolement", "reverse": False,
     "text": "...garder votre équilibre personnel lors d'un embarquement long (plusieurs mois) éloigné de votre environnement habituel ?"},
    {"order": 24, "trait": "isolement", "reverse": False,
     "text": "...continuer à fonctionner efficacement à bord même en l'absence de stimulations extérieures variées (sorties, loisirs, contact social élargi) pendant une période prolongée ?"},
]


async def seed_maritime_tolerance(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent de la Tolérance ICE Physique."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [maritime_tolerance] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Tolérance ICE Physique — 24 items Likert 1-5 évaluant la self-efficacy perçue "
            "face aux exigences physiques et environnementales d'un environnement ICE maritime. "
            "6 domaines × 4 items : endurance en houle, tolérance sommeil/quarts, résistance climat, "
            "performance en confinement, gestion mal de mer, isolement prolongé. "
            "Ancre : confiance dans sa capacité à... (Bandura 1997). "
            "Durée estimée : 8–10 minutes."
        ),
        instructions=(
            "Dans quelle mesure êtes-vous confiant(e) dans votre capacité à... "
            "Pour chaque situation, indiquez votre niveau de confiance. "
            "1 = Pas du tout confiant(e)  →  5 = Totalement confiant(e). "
            "Répondez en pensant à votre expérience réelle ou à la façon dont vous vous comporteriez."
        ),
        test_type="likert",
        max_score_per_question=5,
        n_questions=24,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Construct : self-efficacy (Bandura 1997) — ancre standardisée obligatoire. "
            "Ancrage : Bandura, A. (1997). Self-Efficacy: The Exercise of Control. Freeman. "
            "Stuster, J. (2010). NASA Technical Report — Behavioral Issues, Long-Duration Expeditions. "
            "Effet plafond attendu sur population maritime active — comparer avec ENG1 si disponible. "
            "α Cronbach cible : ≥ 0.78 global. Par domaine : ≥ 0.65 (acceptable pour 4 items). "
            "Validation contenu : soumettre à experts maritimes (n ≥ 5 capitaines/chief officers). "
            "Non étalonné sur population maritime."
        ),
        modules_config=[
            {"index": 0, "name": "Endurance en houle", "trait": "houle",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Efficacité physique en conditions de mer formée ou agitée"},
            {"index": 1, "name": "Manque de sommeil", "trait": "sommeil",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Vigilance et performance lors de quarts de nuit / sommeil fragmenté"},
            {"index": 2, "name": "Conditions climatiques", "trait": "climat",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Résistance aux extrêmes thermiques (froid, chaleur tropicale)"},
            {"index": 3, "name": "Environnement confiné", "trait": "confinement",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Performance en espace réduit partagé sur durée longue"},
            {"index": 4, "name": "Gestion mal de mer", "trait": "mal_de_mer",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Maintien de la capacité opérationnelle malgré les symptômes"},
            {"index": 5, "name": "Isolement prolongé", "trait": "isolement",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Stabilité psychologique lors d'embarquements longs sans escale"},
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
    print(f"  [maritime_tolerance] Seeded '{_CATALOGUE_NAME}' ({len(METS_QUESTIONS)} questions)")
    return catalogue


async def delete_maritime_tolerance(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [maritime_tolerance] Deleted '{_CATALOGUE_NAME}'")


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
