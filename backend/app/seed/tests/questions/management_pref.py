# app/seed/tests/questions/management_pref.py
"""
Préférence de Management — Q6 PS Fit

18 items Likert 1-7 évaluant les préférences de style de management.
3 dimensions × 6 items chacune (banque) — cible finale : 9 items (3/dimension).
Ancre : "Avec quel superviseur préférez-vous travailler ?"

Ancrage théorique : Graen & Uhl-Bien (1995) LMX +
dimensions captain_vector (autonomy_given, feedback_style, structure_imposed).
Items custom originaux — wording distinct du LMX-7 (copyright Elsevier/JAI Press).

    seed_management_pref(db)   → idempotent, retourne le TestCatalogue
    delete_management_pref(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.management_pref
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

_CATALOGUE_NAME = "Préférence de Management"

MANAGEMENT_PREF_QUESTIONS = [
    # ── Autonomy (AUT) — 6 items ───────────────────────────────────────────────
    # Items [R] recodés (8 − valeur) avant calcul du score
    {"order":  1, "trait": "autonomy", "reverse": False,
     "text": "Je préfère travailler avec un capitaine qui me donne de la liberté dans la façon dont j'organise mes tâches quotidiennes à bord"},
    {"order":  2, "trait": "autonomy", "reverse": False,
     "text": "Je me sens plus efficace quand mon responsable me fixe un objectif clair et me laisse décider comment l'atteindre"},
    {"order":  3, "trait": "autonomy", "reverse": True,
     "text": "Je préfère que mon capitaine me dise précisément ce que je dois faire et dans quel ordre, plutôt que de devoir le décider moi-même"},
    {"order":  4, "trait": "autonomy", "reverse": False,
     "text": "Un superviseur qui me fait confiance pour gérer mes responsabilités sans contrôle constant me motive davantage qu'un superviseur directif"},
    {"order":  5, "trait": "autonomy", "reverse": False,
     "text": "Je m'épanouis quand j'ai la latitude de prendre des initiatives à bord, même sur des décisions mineures"},
    {"order":  6, "trait": "autonomy", "reverse": True,
     "text": "Je me sens plus à l'aise à bord quand toutes les décisions importantes sont prises par le capitaine — cela me libère des dilemmes"},

    # ── Feedback (FBK) — 6 items ───────────────────────────────────────────────
    {"order":  7, "trait": "feedback", "reverse": False,
     "text": "J'apprécie un capitaine qui me donne régulièrement son avis sur la qualité de mon travail, même en dehors des évaluations formelles"},
    {"order":  8, "trait": "feedback", "reverse": False,
     "text": "Un retour direct et honnête sur mes erreurs à bord m'aide davantage que des commentaires vagues ou trop ménagés"},
    {"order":  9, "trait": "feedback", "reverse": True,
     "text": "Je préfère que mon responsable me laisse évaluer moi-même ma performance plutôt qu'il me donne son opinion fréquemment"},
    {"order": 10, "trait": "feedback", "reverse": False,
     "text": "Je me développe mieux professionnellement quand mon capitaine prend le temps de m'expliquer ce qui a bien ou moins bien fonctionné après une manœuvre complexe"},
    {"order": 11, "trait": "feedback", "reverse": False,
     "text": "Un supérieur qui reconnaît explicitement les efforts bien faits à bord m'aide à maintenir mon niveau d'engagement"},
    {"order": 12, "trait": "feedback", "reverse": True,
     "text": "Les retours fréquents de mon capitaine sur mon travail me stressent plus qu'ils ne m'aident"},

    # ── Structure (STR) — 6 items ──────────────────────────────────────────────
    {"order": 13, "trait": "structure", "reverse": False,
     "text": "Je me sens plus en sécurité à bord quand les procédures sont clairement définies et respectées de manière stricte"},
    {"order": 14, "trait": "structure", "reverse": False,
     "text": "Je préfère un capitaine qui établit des règles claires sur le fonctionnement à bord plutôt qu'un capitaine qui laisse les choses s'organiser naturellement"},
    {"order": 15, "trait": "structure", "reverse": True,
     "text": "Je travaille mieux quand le cadre est souple et que les règles peuvent être adaptées selon les situations"},
    {"order": 16, "trait": "structure", "reverse": False,
     "text": "Un capitaine qui anticipe et planifie de façon détaillée me rassure et me permet d'être plus efficace"},
    {"order": 17, "trait": "structure", "reverse": False,
     "text": "Une hiérarchie clairement définie à bord me permet de savoir à qui m'adresser et réduit les ambiguïtés qui me pèsent"},
    {"order": 18, "trait": "structure", "reverse": True,
     "text": "Je préfère les environnements à bord où la prise d'initiative individuelle prime sur le respect strict des procédures établies"},
]

_TRAIT_MODULE = {
    "autonomy": 0,
    "feedback": 1,
    "structure": 2,
}


async def seed_management_pref(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du questionnaire Préférence de Management."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [management_pref] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Préférence de Management — 18 items Likert 1-7 évaluant les préférences "
            "de style de management dans le contexte maritime embarqué. "
            "3 dimensions : Autonomie, Feedback, Structure. "
            "Alimente captain_vector (autonomy_given, feedback_style, structure_imposed) "
            "pour le calcul du PS Fit (Q6). "
            "Durée estimée : 6–8 minutes."
        ),
        instructions=(
            "Pour chaque affirmation, indiquez dans quelle mesure elle décrit votre préférence "
            "pour un style de management à bord. "
            "1 = Pas du tout d'accord  →  7 = Tout à fait d'accord."
        ),
        test_type="likert",
        max_score_per_question=7,
        n_questions=18,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        domain=CatalogueDomain.person_team,
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Wording distinct du LMX-7 (Graen & Uhl-Bien 1995, copyright Elsevier/JAI Press). "
            "Items [R] : recoder (8 − valeur) avant calcul des scores. "
            "Proportion items inversés : 2/6 par dimension (1/3 — acceptable). "
            "Corrélation AUT–STR attendue négative modérée (r ≈ −0.35 à −0.50). "
            "Corrélation AUT–FBK attendue faible à nulle (constructs orthogonaux). "
            "Alignement engine : score par dimension → distance euclidienne avec captain_vector "
            "dans ps_fit/f_lmx.py. "
            "Références : Graen, G.B., & Uhl-Bien, M. (1995). The Leadership Quarterly, 6(2), 219–247. "
            "Tett & Burnett (2003). Journal of Applied Psychology, 88(3), 500–517."
        ),
        modules_config=[
            {"index": 0, "name": "Autonomie", "trait": "autonomy",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Degré d'autonomie souhaité → captain_vector.autonomy_given"},
            {"index": 1, "name": "Feedback", "trait": "feedback",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Fréquence et style de retour souhaités → captain_vector.feedback_style"},
            {"index": 2, "name": "Structure", "trait": "structure",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Degré de cadrage procédural souhaité → captain_vector.structure_imposed"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in MANAGEMENT_PREF_QUESTIONS:
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
    print(f"  [management_pref] Seeded '{_CATALOGUE_NAME}' ({len(MANAGEMENT_PREF_QUESTIONS)} questions)")
    return catalogue


async def delete_management_pref(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [management_pref] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_management_pref(db)
        await seed_management_pref(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
