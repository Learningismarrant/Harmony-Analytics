# app/seed/tests/questions/ces_values.py
"""
Valeurs Professionnelles — Q5 PO Fit

32 items Likert 1-6 (sans point neutre) évaluant 4 valeurs professionnelles.
Ancre : "Dans quelle mesure cette affirmation vous représente-t-elle ?"
Échelle : 1 = "Pas du tout" → 6 = "Tout à fait"
8 items par valeur. Cible finale : 16 items (4/valeur) — banque : 32 items (8/valeur).

Ancrage : Rokeach (1973) + Ravlin & Meglino (1987) — wording custom Radiant.
Contexte : vie à bord / environnement superyacht.

    seed_ces_values(db)   → idempotent, retourne le TestCatalogue
    delete_ces_values(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.ces_values
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question

_CATALOGUE_NAME = "Professional Values Scale (CES)"

CES_VALUES_QUESTIONS = [
    # ── Achievement (ACH) — 8 items ───────────────────────────────────────────
    {"order":  1, "trait": "achievement", "reverse": False,
     "text": "Quand j'effectue une manœuvre ou une tâche technique, je cherche à la faire le mieux possible, même si personne ne regarde"},
    {"order":  2, "trait": "achievement", "reverse": False,
     "text": "Je ne suis pas satisfait(e) d'un travail réalisé à bord tant que je n'estime pas avoir donné le meilleur de moi-même"},
    {"order":  3, "trait": "achievement", "reverse": False,
     "text": "Je me fixe des standards de performance élevés, même lorsque la situation ne l'exige pas strictement"},
    {"order":  4, "trait": "achievement", "reverse": False,
     "text": "Je préfère me voir confier des missions difficiles plutôt que des tâches routinières, même si cela augmente le risque d'erreur"},
    {"order":  5, "trait": "achievement", "reverse": False,
     "text": "Je trouve que progresser dans mes compétences à bord est une source de fierté plus importante que la reconnaissance externe"},
    {"order":  6, "trait": "achievement", "reverse": False,
     "text": "Lorsqu'un problème survient à bord, je cherche activement à aller au-delà de la solution minimale"},
    {"order":  7, "trait": "achievement", "reverse": False,
     "text": "Je m'investis dans la maîtrise technique de mon poste même en dehors des heures de quart formellement requises"},
    {"order":  8, "trait": "achievement", "reverse": False,
     "text": "L'amélioration continue de ma pratique professionnelle est quelque chose qui compte sincèrement pour moi, pas une obligation formelle"},

    # ── Helping & Concern for Others (HCO) — 8 items ─────────────────────────
    {"order":  9, "trait": "helping", "reverse": False,
     "text": "Quand je vois un coéquipier en difficulté, j'interviens spontanément pour l'aider, même si ce n'est pas ma responsabilité directe"},
    {"order": 10, "trait": "helping", "reverse": False,
     "text": "Je prends soin de vérifier que les membres les plus récents de l'équipage s'adaptent correctement à la vie à bord"},
    {"order": 11, "trait": "helping", "reverse": False,
     "text": "Le bien-être général de l'équipage m'importe autant que ma propre performance individuelle"},
    {"order": 12, "trait": "helping", "reverse": False,
     "text": "Je partage volontiers mes connaissances techniques avec les autres membres de l'équipage, même si cela peut réduire mon avantage compétitif"},
    {"order": 13, "trait": "helping", "reverse": False,
     "text": "En cas de charge de travail inégalement répartie à bord, je prends l'initiative de soutenir ceux qui sont surchargés"},
    {"order": 14, "trait": "helping", "reverse": False,
     "text": "Je suis attentif(ve) aux signes de fatigue ou de stress chez mes collègues, et j'adapte mon comportement en conséquence"},
    {"order": 15, "trait": "helping", "reverse": False,
     "text": "La solidarité à bord n'est pas pour moi une obligation professionnelle, mais quelque chose que je pratique naturellement"},
    {"order": 16, "trait": "helping", "reverse": False,
     "text": "Je prends en compte l'impact de mes décisions ou de mon comportement sur le moral et le confort de l'équipage"},

    # ── Fairness (FAI) — 8 items ──────────────────────────────────────────────
    {"order": 17, "trait": "fairness", "reverse": False,
     "text": "Je m'assure que les tâches pénibles à bord sont réparties équitablement, sans favoritisme"},
    {"order": 18, "trait": "fairness", "reverse": False,
     "text": "Quand je prends une décision qui affecte l'équipage, je m'efforce d'appliquer les mêmes règles pour tout le monde"},
    {"order": 19, "trait": "fairness", "reverse": False,
     "text": "Je signale les situations injustes à bord, même quand cela peut créer des tensions"},
    {"order": 20, "trait": "fairness", "reverse": False,
     "text": "Je respecte les règles collectives à bord même lorsqu'elles me désavantagent personnellement"},
    {"order": 21, "trait": "fairness", "reverse": False,
     "text": "Je pense qu'un équipage ne peut fonctionner correctement que si chacun est traité avec la même impartialité"},
    {"order": 22, "trait": "fairness", "reverse": False,
     "text": "Je refuse d'accorder ou d'accepter des passe-droits, même lorsque cela pourrait m'arranger"},
    {"order": 23, "trait": "fairness", "reverse": False,
     "text": "Lorsque des ressources limitées doivent être partagées à bord (temps libre, matériel, espace), je veille à ce que la distribution soit juste"},
    {"order": 24, "trait": "fairness", "reverse": False,
     "text": "Je défends l'idée que les efforts et les contributions de chaque membre d'équipage doivent être reconnus de manière proportionnelle"},

    # ── Honesty & Integrity (HON) — 8 items ───────────────────────────────────
    {"order": 25, "trait": "honesty", "reverse": False,
     "text": "Je rapporte fidèlement la réalité d'une situation à mes supérieurs, même si ce n'est pas ce qu'ils veulent entendre"},
    {"order": 26, "trait": "honesty", "reverse": False,
     "text": "Je reconnais ouvertement mes erreurs à bord plutôt que de les minimiser ou de les attribuer à d'autres"},
    {"order": 27, "trait": "honesty", "reverse": False,
     "text": "Ma parole à bord est fiable — quand je m'engage sur quelque chose, je l'honore"},
    {"order": 28, "trait": "honesty", "reverse": False,
     "text": "Je ne dissimule pas d'informations importantes à mes collègues ou supérieurs, même quand cela pourrait me compliquer la vie"},
    {"order": 29, "trait": "honesty", "reverse": False,
     "text": "J'agis de la même façon qu'on me voit ou non — la cohérence entre mes valeurs et mes actes à bord est importante pour moi"},
    {"order": 30, "trait": "honesty", "reverse": False,
     "text": "Je refuse de souscrire à des pratiques que je considère malhonnêtes, même sous pression hiérarchique"},
    {"order": 31, "trait": "honesty", "reverse": False,
     "text": "Quand je ne suis pas d'accord avec une décision prise à bord, je l'exprime directement plutôt que de me plaindre en coulisse"},
    {"order": 32, "trait": "honesty", "reverse": False,
     "text": "La transparence dans mes interactions à bord est pour moi un principe de comportement, pas simplement une contrainte professionnelle"},
]


async def seed_ces_values(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du CES valeurs professionnelles."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [ces_values] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Valeurs Professionnelles — 32 items Likert 1-6 (sans point neutre). "
            "Évalue 4 dimensions : Achievement (excellence), Helping & Concern for Others (entraide), "
            "Fairness (équité), Honesty & Integrity (honnêteté). "
            "8 items par valeur. Contexte vie à bord / superyacht. "
            "Ancrage : Rokeach (1973) + Ravlin & Meglino (1987). "
            "Durée estimée : 10–14 minutes."
        ),
        instructions=(
            "Dans quelle mesure chaque affirmation vous représente-t-elle ? "
            "Répondez en pensant à votre comportement réel à bord ou à la façon dont vous agiriez. "
            "1 = Pas du tout  →  6 = Tout à fait. "
            "Il n'y a pas de bonnes ou mauvaises réponses — répondez honnêtement."
        ),
        test_type="likert",
        max_score_per_question=6,
        n_questions=32,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Wording distinct de la CES Ravlin & Meglino. "
            "Ancrage : Rokeach (1973). The Nature of Human Values. Free Press. "
            "Ravlin, E.C., & Meglino, B.M. (1987). Journal of Applied Psychology, 72(4), 666–673. "
            "Biais de désirabilité sociale fort sur HON et FAI — surveiller l'effet plafond. "
            "α Cronbach cible : ≥ 0.75 par valeur. "
            "ACP : 4 facteurs attendus. Surveiller la contamination ACH–FAI (items comportementaux similaires). "
            "Non étalonné sur population maritime. "
            "Recommandation : calibrer les seuils PSI sur données réelles avant usage décisionnel."
        ),
        modules_config=[
            {"index": 0, "name": "Achievement", "trait": "achievement",
             "n_items": 8, "duration_min": 3, "priority": "STANDARD",
             "description": "Excellence personnelle, dépassement de soi, standards élevés"},
            {"index": 1, "name": "Helping & Concern for Others", "trait": "helping",
             "n_items": 8, "duration_min": 3, "priority": "STANDARD",
             "description": "Aide active, soutien, entraide — orientation vers le bien-être collectif"},
            {"index": 2, "name": "Fairness", "trait": "fairness",
             "n_items": 8, "duration_min": 3, "priority": "STANDARD",
             "description": "Équité, impartialité, respect des règles collectives à bord"},
            {"index": 3, "name": "Honesty & Integrity", "trait": "honesty",
             "n_items": 8, "duration_min": 3, "priority": "STANDARD",
             "description": "Honnêteté, transparence, fiabilité dans les relations à bord"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in CES_VALUES_QUESTIONS:
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
    print(f"  [ces_values] Seeded '{_CATALOGUE_NAME}' ({len(CES_VALUES_QUESTIONS)} questions)")
    return catalogue


async def delete_ces_values(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [ces_values] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_ces_values(db)
        await seed_ces_values(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
