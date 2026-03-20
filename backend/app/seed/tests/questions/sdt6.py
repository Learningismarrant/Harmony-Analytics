# app/seed/tests/questions/sdt6.py
"""
SDT-6 Motivation Maritime — Q3

36 items Likert 1-7 évaluant les 6 régulations motivationnelles (SDT).
Ancré : "Pourquoi faites-vous ou feriez-vous ce travail en mer ?"
Format complétion : "Parce que..."
6 sous-échelles × 6 items chacune.

Ancrage théorique : Deci & Ryan (2000).
Items custom originaux — wording distinct du MWMS Gagné (2015).

    seed_sdt6(db)   → idempotent, retourne le TestCatalogue
    delete_sdt6(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.sdt6
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

_CATALOGUE_NAME = "SDT-6 Motivation Maritime"

SDT6_QUESTIONS = [
    # ── Amotivation (AMO) — 6 items ───────────────────────────────────────────
    {"order":  1, "trait": "amotivation", "reverse": False,
     "text": "Parce que franchement, je ne vois pas vraiment ce que ce travail m'apporte"},
    {"order":  2, "trait": "amotivation", "reverse": False,
     "text": "Parce que je n'ai pas de raison précise — c'est une situation dans laquelle je me retrouve"},
    {"order":  3, "trait": "amotivation", "reverse": False,
     "text": "Parce que je ne saurais pas expliquer pourquoi je fais ce métier plutôt qu'un autre"},
    {"order":  4, "trait": "amotivation", "reverse": False,
     "text": "Parce que je me demande parfois si ce travail a vraiment un sens pour moi"},
    {"order":  5, "trait": "amotivation", "reverse": False,
     "text": "Parce que je ne peux pas dire que je suis motivé(e) — j'y vais parce que c'est ce que je fais"},
    {"order":  6, "trait": "amotivation", "reverse": False,
     "text": "Parce que les raisons pour lesquelles je fais ce travail me semblent floues, même à moi"},

    # ── Régulation externe (EXT) — 6 items ────────────────────────────────────
    {"order":  7, "trait": "external", "reverse": False,
     "text": "Parce que ce travail est bien payé par rapport aux alternatives disponibles pour moi"},
    {"order":  8, "trait": "external", "reverse": False,
     "text": "Parce que ma situation financière m'y oblige — je n'ai pas vraiment le choix"},
    {"order":  9, "trait": "external", "reverse": False,
     "text": "Parce que les personnes de mon entourage s'attendent à ce que je continue dans ce type de travail"},
    {"order": 10, "trait": "external", "reverse": False,
     "text": "Parce que perdre ce poste aurait des conséquences matérielles que je ne peux pas me permettre"},
    {"order": 11, "trait": "external", "reverse": False,
     "text": "Parce que la rémunération et les avantages concrets (logement, nourriture à bord) représentent une opportunité réelle"},
    {"order": 12, "trait": "external", "reverse": False,
     "text": "Parce qu'on me l'a proposé et que refuser n'était pas envisageable dans ma situation à ce moment-là"},

    # ── Introjection (INJ) — 6 items ──────────────────────────────────────────
    {"order": 13, "trait": "introjected", "reverse": False,
     "text": "Parce que je me sentirais mal de ne pas donner le meilleur de moi-même à bord"},
    {"order": 14, "trait": "introjected", "reverse": False,
     "text": "Parce que je veux que l'équipage et les supérieurs aient une bonne opinion de moi"},
    {"order": 15, "trait": "introjected", "reverse": False,
     "text": "Parce que j'aurais honte de me montrer peu fiable dans un environnement où les autres comptent sur moi"},
    {"order": 16, "trait": "introjected", "reverse": False,
     "text": "Parce que la pression de ne pas décevoir ceux qui m'ont fait confiance me pousse à m'investir"},
    {"order": 17, "trait": "introjected", "reverse": False,
     "text": "Parce que me prouver à moi-même que je suis capable de tenir dans des conditions difficiles compte pour mon amour-propre"},
    {"order": 18, "trait": "introjected", "reverse": False,
     "text": "Parce que je ressentirais de la culpabilité si je ne faisais pas correctement mon travail alors que l'équipe dépend de moi"},

    # ── Identification (IDE) — 6 items ────────────────────────────────────────
    {"order": 19, "trait": "identified", "reverse": False,
     "text": "Parce que ce travail me permet d'acquérir des compétences qui comptent vraiment pour mon avenir"},
    {"order": 20, "trait": "identified", "reverse": False,
     "text": "Parce que travailler en mer est un moyen important d'avancer dans la direction que je veux pour ma carrière"},
    {"order": 21, "trait": "identified", "reverse": False,
     "text": "Parce que les expériences vécues à bord font partie d'un projet professionnel qui a du sens pour moi"},
    {"order": 22, "trait": "identified", "reverse": False,
     "text": "Parce que même si ce n'est pas toujours agréable, je reconnais la valeur de ce que je construis dans ce métier"},
    {"order": 23, "trait": "identified", "reverse": False,
     "text": "Parce que les responsabilités que ce travail m'offre correspondent à ce que j'attends d'une activité professionnelle sérieuse"},
    {"order": 24, "trait": "identified", "reverse": False,
     "text": "Parce que je pense que maîtriser les savoir-faire de ce métier est quelque chose de précieux à long terme"},

    # ── Intégration (ITG) — 6 items ───────────────────────────────────────────
    {"order": 25, "trait": "integrated", "reverse": False,
     "text": "Parce que travailler en mer fait partie intégrante de qui je suis — c'est cohérent avec mes valeurs profondes"},
    {"order": 26, "trait": "integrated", "reverse": False,
     "text": "Parce que ce mode de vie et ce métier correspondent à la personne que je veux être"},
    {"order": 27, "trait": "integrated", "reverse": False,
     "text": "Parce que je ne conçois pas vraiment ma vie professionnelle autrement — la mer est une composante centrale de mon identité"},
    {"order": 28, "trait": "integrated", "reverse": False,
     "text": "Parce que ce travail prolonge naturellement les engagements et les valeurs qui me définissent en dehors du cadre professionnel"},
    {"order": 29, "trait": "integrated", "reverse": False,
     "text": "Parce qu'il y a une cohérence profonde entre les exigences de ce métier et ce qui guide mes choix de vie en général"},
    {"order": 30, "trait": "integrated", "reverse": False,
     "text": "Parce que les sacrifices que ce travail implique — éloignement, isolement, contraintes — s'inscrivent dans un projet de vie qui me ressemble pleinement"},

    # ── Motivation intrinsèque (MIX) — 6 items ────────────────────────────────
    {"order": 31, "trait": "intrinsic", "reverse": False,
     "text": "Parce que les activités quotidiennes de ce travail m'intéressent genuinement — je les trouve stimulantes"},
    {"order": 32, "trait": "intrinsic", "reverse": False,
     "text": "Parce que je ressens du plaisir à naviguer, à manœuvrer, à travailler avec la mer — pas pour ce que ça m'apporte, mais pour ce que c'est en soi"},
    {"order": 33, "trait": "intrinsic", "reverse": False,
     "text": "Parce que la curiosité que j'ai pour les aspects techniques et humains de ce métier suffit à me faire avancer au quotidien"},
    {"order": 34, "trait": "intrinsic", "reverse": False,
     "text": "Parce que je me perds dans ce travail — le temps passe sans que je le voie quand je suis absorbé(e) par une tâche à bord"},
    {"order": 35, "trait": "intrinsic", "reverse": False,
     "text": "Parce que la complexité des défis que ce métier pose — qu'ils soient techniques, météorologiques ou relationnels — me passionne sincèrement"},
    {"order": 36, "trait": "intrinsic", "reverse": False,
     "text": "Parce que même dans les moments difficiles, je trouve dans le travail lui-même une satisfaction que peu d'autres contextes professionnels m'offriraient"},
]

_TRAIT_MODULE = {
    "amotivation": 0,
    "external":    1,
    "introjected": 2,
    "identified":  3,
    "integrated":  4,
    "intrinsic":   5,
}


async def seed_sdt6(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du SDT-6 Motivation Maritime."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [sdt6] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "SDT-6 Motivation Maritime — 36 items Likert 1-7 évaluant les 6 régulations "
            "motivationnelles dans le contexte du travail en mer. "
            "Ancre : 'Pourquoi faites-vous ou feriez-vous ce travail en mer ?' "
            "6 sous-échelles : amotivation, régulation externe, introjection, "
            "identification, intégration, motivation intrinsèque. "
            "Durée estimée : 8–12 minutes."
        ),
        instructions=(
            "Les énoncés suivants décrivent des raisons pour lesquelles vous faites "
            "ou feriez ce travail en mer. Complétez chaque phrase commençant par 'Parce que...' "
            "en indiquant dans quelle mesure cette raison correspond à votre cas. "
            "1 = Pas du tout pour cette raison  →  7 = Exactement pour cette raison."
        ),
        test_type="likert",
        max_score_per_question=7,
        n_questions=36,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Wording distinct du MWMS Gagné (2015). Ancrage théorique : Deci & Ryan (2000). "
            "Pattern simplex attendu en ACP : corrélations décroissantes au fur et à mesure "
            "de l'éloignement des sous-échelles sur le continuum AMO → MIX (Pelletier et al. 1995). "
            "α Cronbach cible : ≥ 0.70 par sous-échelle. "
            "Biais de désirabilité sociale sur INJ — surveiller l'asymétrie des distributions. "
            "⚠️ Q3 indicatif jusqu'au Temps 2 (non compensatoire dans global_score). "
            "Références : Deci & Ryan (2000). Psychological Inquiry, 11(4), 227–268 ; "
            "Gagné et al. (2015). European Journal of Work and Organizational Psychology, 24(2), 178–196."
        ),
        modules_config=[
            {"index": 0, "name": "Amotivation", "trait": "amotivation",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Absence de régulation intentionnelle — absence de sens"},
            {"index": 1, "name": "Régulation externe", "trait": "external",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Contingences externes — salaire, contraintes, pression sociale"},
            {"index": 2, "name": "Introjection", "trait": "introjected",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Régulation interne non intégrée — culpabilité, fierté, approbation"},
            {"index": 3, "name": "Identification", "trait": "identified",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Valeur instrumentale reconnue — important sans être plaisir intrinsèque"},
            {"index": 4, "name": "Intégration", "trait": "integrated",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Cohérence avec l'identité centrale et les valeurs fondamentales"},
            {"index": 5, "name": "Motivation intrinsèque", "trait": "intrinsic",
             "n_items": 6, "duration_min": 2, "priority": "STANDARD",
             "description": "Intérêt et plaisir inhérents à l'activité — forme la plus autonome"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in SDT6_QUESTIONS:
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
    print(f"  [sdt6] Seeded '{_CATALOGUE_NAME}' ({len(SDT6_QUESTIONS)} questions)")
    return catalogue


async def delete_sdt6(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [sdt6] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_sdt6(db)
        await seed_sdt6(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
