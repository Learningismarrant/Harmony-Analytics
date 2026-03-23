# app/seed/tests/questions/mobility_profile.py
"""
Mobilité Maritime (MMFS) — Q7 Mobility Fit

16 items format mixte (Likert 5 / Oui-Non + intensité) évaluant la
compatibilité factuelle candidat ↔ contraintes de mobilité du poste.
4 domaines × 4 items chacun.

Nature : filtre éliminatoire non compensatoire — pas un instrument psychométrique prédictif.
Items critiques éliminatoires : D01, D02, D04 (réponse négative = flag administratif).

Domaines : disponibilite | geographie | contraintes_perso | administratif

Scoring :
  - Items Likert : score direct (1-5)
  - Items Oui/Non : 1 (compatible) / 0 (incompatible)
  - Item inversé (C01) : recoder (6 − valeur) avant agrégation
  - Items éliminatoires D01/D02/D04 : Non = flag automatique

    seed_mobility_profile(db)   → idempotent, retourne le TestCatalogue
    delete_mobility_profile(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.mobility_profile
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

_CATALOGUE_NAME = "Mobilité Maritime (MMFS)"

MMFS_QUESTIONS = [
    # ── Domaine A — Disponibilité calendaire ──────────────────────────────────
    {"order":  1, "trait": "disponibilite", "reverse": False,
     "text": "Êtes-vous disponible pour embarquer dans un délai de moins de 4 semaines ?",
     "options": [
         {"key": "oui_1sem", "text": "Oui — dans moins d'une semaine"},
         {"key": "oui_2sem", "text": "Oui — dans 1 à 2 semaines"},
         {"key": "oui_3sem", "text": "Oui — dans 2 à 3 semaines"},
         {"key": "oui_4sem", "text": "Oui — dans 3 à 4 semaines"},
         {"key": "non",      "text": "Non — pas disponible dans ce délai"},
     ]},
    {"order":  2, "trait": "disponibilite", "reverse": False,
     "text": "Dans quelle mesure êtes-vous disponible pour un contrat d'une durée supérieure à 6 mois sans interruption ?",
     "options": [
         {"key": "1", "text": "Pas du tout disponible"},
         {"key": "2", "text": "Peu disponible"},
         {"key": "3", "text": "Moyennement disponible"},
         {"key": "4", "text": "Disponible"},
         {"key": "5", "text": "Totalement disponible"},
     ]},
    {"order":  3, "trait": "disponibilite", "reverse": False,
     "text": "Dans quelle mesure pouvez-vous accepter une modification de votre planning d'embarquement à moins de deux semaines de préavis ?",
     "options": [
         {"key": "1", "text": "Pas du tout"},
         {"key": "2", "text": "Difficilement"},
         {"key": "3", "text": "Avec des difficultés"},
         {"key": "4", "text": "Facilement"},
         {"key": "5", "text": "Sans problème"},
     ]},
    {"order":  4, "trait": "disponibilite", "reverse": False,
     "text": "Avez-vous actuellement des engagements professionnels ou contractuels qui limiteraient votre disponibilité au cours des 3 prochains mois ?",
     "options": [
         {"key": "non", "text": "Non — je suis libre de tout engagement"},
         {"key": "oui", "text": "Oui — j'ai des engagements en cours (préciser)"},
     ]},

    # ── Domaine B — Restrictions géographiques ─────────────────────────────────
    {"order":  5, "trait": "geographie", "reverse": False,
     "text": "Existe-t-il des zones géographiques dans lesquelles vous ne pouvez pas naviguer (raisons légales, sécuritaires ou personnelles) ?",
     "options": [
         {"key": "non", "text": "Non — aucune restriction géographique"},
         {"key": "oui", "text": "Oui — des zones sont exclues (préciser)"},
     ]},
    {"order":  6, "trait": "geographie", "reverse": False,
     "text": "Dans quelle mesure êtes-vous à l'aise pour naviguer dans des zones géographiquement éloignées de votre pays de résidence (ex. Pacifique, Océan Indien, Arctique) ?",
     "options": [
         {"key": "1", "text": "Pas du tout à l'aise"},
         {"key": "2", "text": "Peu à l'aise"},
         {"key": "3", "text": "Modérément à l'aise"},
         {"key": "4", "text": "À l'aise"},
         {"key": "5", "text": "Totalement à l'aise"},
     ]},
    {"order":  7, "trait": "geographie", "reverse": False,
     "text": "Dans quelle mesure acceptez-vous que la destination de votre mission soit déterminée par l'armateur, sans votre participation au choix ?",
     "options": [
         {"key": "1", "text": "Je n'accepte pas"},
         {"key": "2", "text": "J'accepte difficilement"},
         {"key": "3", "text": "J'accepte avec réserves"},
         {"key": "4", "text": "J'accepte généralement"},
         {"key": "5", "text": "J'accepte pleinement"},
     ]},
    {"order":  8, "trait": "geographie", "reverse": False,
     "text": "Avez-vous des préférences géographiques fortes qui rendraient certaines zones rédhibitoires pour vous (ex. navigation polaire, zones de conflit) ?",
     "options": [
         {"key": "non", "text": "Non — pas de zone rédhibitoire"},
         {"key": "oui", "text": "Oui — certaines zones sont exclues (préciser)"},
     ]},

    # ── Domaine C — Contraintes familiales et personnelles ─────────────────────
    {"order":  9, "trait": "contraintes_perso", "reverse": True,
     "text": "Dans quelle mesure vos obligations familiales ou personnelles (enfants, aidant familial, etc.) limitent-elles votre capacité à effectuer de longs embarquements sans retour ?",
     "options": [
         {"key": "1", "text": "Elles ne limitent pas du tout"},
         {"key": "2", "text": "Elles limitent peu"},
         {"key": "3", "text": "Elles limitent modérément"},
         {"key": "4", "text": "Elles limitent beaucoup"},
         {"key": "5", "text": "Elles limitent significativement"},
     ]},
    {"order": 10, "trait": "contraintes_perso", "reverse": False,
     "text": "Avez-vous besoin de rentrer à votre domicile à intervalles réguliers (ex. toutes les 8 semaines) pour des raisons familiales ou personnelles ?",
     "options": [
         {"key": "non",   "text": "Non — pas de nécessité de retour régulier"},
         {"key": "4sem",  "text": "Oui — toutes les 4 semaines environ"},
         {"key": "6sem",  "text": "Oui — toutes les 6 semaines environ"},
         {"key": "8sem",  "text": "Oui — toutes les 8 semaines environ"},
         {"key": "6mois", "text": "Oui — toutes les 6 mois ou plus"},
     ]},
    {"order": 11, "trait": "contraintes_perso", "reverse": False,
     "text": "Dans quelle mesure êtes-vous en mesure de gérer à distance vos responsabilités personnelles (logement, finances, famille) sur une période d'embarquement longue ?",
     "options": [
         {"key": "1", "text": "Pas du tout en mesure"},
         {"key": "2", "text": "Peu en mesure"},
         {"key": "3", "text": "Modérément en mesure"},
         {"key": "4", "text": "En mesure"},
         {"key": "5", "text": "Totalement en mesure"},
     ]},
    {"order": 12, "trait": "contraintes_perso", "reverse": False,
     "text": "Dans quelle mesure votre entourage proche (partenaire, famille) soutient-il votre choix de travailler en mer sur de longues périodes ?",
     "options": [
         {"key": "1", "text": "Pas du tout"},
         {"key": "2", "text": "Peu"},
         {"key": "3", "text": "Modérément"},
         {"key": "4", "text": "Beaucoup"},
         {"key": "5", "text": "Pleinement"},
     ]},

    # ── Domaine D — Contraintes administratives (éliminatoires D01/D02/D04) ───
    {"order": 13, "trait": "administratif", "reverse": False,
     "text": "Possédez-vous un passeport valide pour au moins 12 mois ?",
     "options": [
         {"key": "oui", "text": "Oui — passeport valide 12 mois ou plus"},
         {"key": "non", "text": "Non — passeport expiré ou absent"},
     ]},
    {"order": 14, "trait": "administratif", "reverse": False,
     "text": "Possédez-vous un carnet de marin (Seaman's Book) ou un document équivalent reconnu internationalement ?",
     "options": [
         {"key": "oui",    "text": "Oui — document valide"},
         {"key": "cours",  "text": "Non — en cours d'obtention"},
         {"key": "non",    "text": "Non — absent"},
     ]},
    {"order": 15, "trait": "administratif", "reverse": False,
     "text": "Avez-vous des restrictions de visa qui vous empêchent d'entrer dans certains pays sans démarches administratives longues (ex. États-Unis, Russie, Australie) ?",
     "options": [
         {"key": "non", "text": "Non — aucune restriction de visa"},
         {"key": "oui", "text": "Oui — restrictions sur certains pays (préciser)"},
     ]},
    {"order": 16, "trait": "administratif", "reverse": False,
     "text": "Vos certifications professionnelles obligatoires (STCW de base, ENG1, certificats médicaux) sont-elles toutes à jour et valides pour les 12 prochains mois ?",
     "options": [
         {"key": "oui",    "text": "Oui — toutes à jour"},
         {"key": "partiel","text": "Partiellement — certaines expirent bientôt (préciser)"},
         {"key": "non",    "text": "Non — certifications expirées ou absentes"},
     ]},
]


async def seed_mobility_profile(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent du MMFS Mobilité Maritime."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [mobility_profile] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "Mobilité Maritime (MMFS) — 16 items format mixte évaluant la compatibilité "
            "factuelle candidat ↔ contraintes de mobilité du poste. "
            "4 domaines × 4 items : disponibilité calendaire, restrictions géographiques, "
            "contraintes personnelles, exigences administratives. "
            "Filtre non compensatoire : items D01/D02/D04 éliminatoires si réponse négative. "
            "Durée estimée : 5–7 minutes."
        ),
        instructions=(
            "Ces questions portent sur vos contraintes et disponibilités pratiques pour le travail en mer. "
            "Il n'y a pas de bonnes ou mauvaises réponses — répondez avec précision et honnêteté. "
            "Certaines questions déterminent votre éligibilité administrative."
        ),
        test_type="qcm",
        max_score_per_question=5,
        n_questions=16,
        is_active=True,
        status="ALPHA",
        license="RADIANT_PROPRIETARY",
        domain=CatalogueDomain.physical,
        validation_notes=(
            "⚠️ INSTRUMENT ALPHA — Items custom originaux Radiant Analytics (2026). "
            "Nature : filtre éliminatoire non compensatoire — pas un instrument psychométrique. "
            "Items éliminatoires : D01 (passeport), D02 (carnet marin), D04 (certifications STCW/ENG1). "
            "Une réponse négative sur ces items = flag automatique 'incompatibilité administrative'. "
            "Item C01 (contraintes perso) : inverser (6 − valeur) avant agrégation. "
            "Items Oui/Non : convertir en 0/1 pour score composite. "
            "Référence : Stuster, J. (2010). NASA Technical Report — ICE environments mobility constraints."
        ),
        modules_config=[
            {"index": 0, "name": "Disponibilité calendaire", "trait": "disponibilite",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Délai d'embarquement, durée de contrat, flexibilité de planning"},
            {"index": 1, "name": "Restrictions géographiques", "trait": "geographie",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Zones exclues, aisance zones éloignées, acceptation du choix armateur"},
            {"index": 2, "name": "Contraintes personnelles", "trait": "contraintes_perso",
             "n_items": 4, "duration_min": 2, "priority": "STANDARD",
             "description": "Obligations familiales, nécessité retours, gestion à distance"},
            {"index": 3, "name": "Contraintes administratives", "trait": "administratif",
             "n_items": 4, "duration_min": 2, "priority": "SAFETY",
             "description": "Passeport, carnet marin, restrictions visa, certifications STCW/ENG1 — éliminatoire"},
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in MMFS_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="qcm",
            trait=q["trait"],
            options=q.get("options"),
            correct_answer=None,
            reverse=q.get("reverse", False),
        ))

    await db.flush()
    print(f"  [mobility_profile] Seeded '{_CATALOGUE_NAME}' ({len(MMFS_QUESTIONS)} questions)")
    return catalogue


async def delete_mobility_profile(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [mobility_profile] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_mobility_profile(db)
        await seed_mobility_profile(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
