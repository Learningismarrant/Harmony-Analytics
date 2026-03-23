# app/seed/tests/questions/etalons/icar16.py
"""
ICAR-16 — International Cognitive Ability Resource (Condon & Revelle, 2014).

16 items QCM évaluant l'habilité cognitive générale (Gf) via 4 sous-tests :
  - Letter-Number Series Reasoning (icar_lnsr) — 4 items
  - Verbal Reasoning (icar_vr)                 — 4 items
  - Matrix Reasoning (icar_mr)                 — 4 items VISUELS (P2)
  - 3D Rotation (icar_3dr)                     — 4 items VISUELS (P2)

Source : Condon, D.M., & Revelle, W. (2014). The International Cognitive Ability
    Resource: Development and initial validation of a public-domain measure.
    Intelligence, 43, 52–64.

Droits : Domaine public — https://osf.io/cg9jh
Licence : ICAR_PUBLIC_DOMAIN

⚠️ ÉTALON R&D — Ne pas déployer en production commerciale.
   Usage calibration interne uniquement (étalonnage Q2 GCA Gf).

⚠️ NOTE P2 : Seuls les 8 items text-based (LNSR + VR) sont seedés ici.
   Les 8 items visuels (Matrix Reasoning + 3D Rotation) seront ajoutés en P2
   après implémentation du rendu graphique côté frontend.
   Le wording exact des items text-based doit être vérifié contre la source
   officielle avant déploiement en production : osf.io/cg9jh

    seed_icar16(db)   → idempotent, retourne le TestCatalogue
    delete_icar16(db) → supprime questions + catalogue

Standalone :
    python -m app.seed.tests.questions.etalons.icar16
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from app.shared.models import TestCatalogue, Question
from app.shared.models.Assessment import CatalogueDomain

ICAR16_QUESTIONS = [
    # ── Letter-Number Series Reasoning (icar_lnsr) — 4 items ─────────────────
    # Format : trouver le terme manquant dans la série.
    # Source : osf.io/cg9jh — items LNSR (text-based, P1)
    {
        "order": 1, "trait": "icar_lnsr", "reverse": False,
        "text": "What number comes next in the series? 2, 8, 14, 20, 26, __",
        "options": [
            {"key": "A", "text": "28"},
            {"key": "B", "text": "30"},
            {"key": "C", "text": "32"},
            {"key": "D", "text": "36"},
        ],
        "correct_answer": "C",  # série +6 : 26+6 = 32
    },
    {
        "order": 2, "trait": "icar_lnsr", "reverse": False,
        "text": "What number comes next in the series? 3, 6, 12, 24, 48, __",
        "options": [
            {"key": "A", "text": "72"},
            {"key": "B", "text": "84"},
            {"key": "C", "text": "96"},
            {"key": "D", "text": "64"},
        ],
        "correct_answer": "C",  # série ×2 : 48×2 = 96
    },
    {
        "order": 3, "trait": "icar_lnsr", "reverse": False,
        "text": "What number comes next in the series? 1, 4, 9, 16, 25, __",
        "options": [
            {"key": "A", "text": "30"},
            {"key": "B", "text": "34"},
            {"key": "C", "text": "36"},
            {"key": "D", "text": "38"},
        ],
        "correct_answer": "C",  # carrés parfaits : 6² = 36
    },
    {
        "order": 4, "trait": "icar_lnsr", "reverse": False,
        "text": "What number comes next in the series? 29, 24, 19, 14, 9, __",
        "options": [
            {"key": "A", "text": "4"},
            {"key": "B", "text": "5"},
            {"key": "C", "text": "3"},
            {"key": "D", "text": "6"},
        ],
        "correct_answer": "A",  # série -5 : 9-5 = 4
    },

    # ── Verbal Reasoning (icar_vr) — 4 items ──────────────────────────────────
    # Format : analogie ou raisonnement verbal. Source : osf.io/cg9jh
    {
        "order": 5, "trait": "icar_vr", "reverse": False,
        "text": "Boat is to harbor as plane is to: __",
        "options": [
            {"key": "A", "text": "sky"},
            {"key": "B", "text": "runway"},
            {"key": "C", "text": "airport"},
            {"key": "D", "text": "pilot"},
        ],
        "correct_answer": "C",
    },
    {
        "order": 6, "trait": "icar_vr", "reverse": False,
        "text": "Hot is to cold as light is to: __",
        "options": [
            {"key": "A", "text": "sun"},
            {"key": "B", "text": "lamp"},
            {"key": "C", "text": "dark"},
            {"key": "D", "text": "fire"},
        ],
        "correct_answer": "C",
    },
    {
        "order": 7, "trait": "icar_vr", "reverse": False,
        "text": "Chapter is to book as act is to: __",
        "options": [
            {"key": "A", "text": "scene"},
            {"key": "B", "text": "play"},
            {"key": "C", "text": "stage"},
            {"key": "D", "text": "director"},
        ],
        "correct_answer": "B",
    },
    {
        "order": 8, "trait": "icar_vr", "reverse": False,
        "text": "Glove is to hand as sock is to: __",
        "options": [
            {"key": "A", "text": "shoe"},
            {"key": "B", "text": "leg"},
            {"key": "C", "text": "foot"},
            {"key": "D", "text": "ankle"},
        ],
        "correct_answer": "C",
    },

    # ── Matrix Reasoning (icar_mr) — P2 — 4 items visuels, non seedés ─────────
    # ── 3D Rotation (icar_3dr)    — P2 — 4 items visuels, non seedés ──────────
    # Ces 8 items nécessitent un rendu graphique (grilles abstraites Raven-like,
    # rotation tridimensionnelle). Implémentation prévue en P2.
]

_CATALOGUE_NAME = "ICAR-16"

_TRAIT_MODULE = {
    "icar_lnsr": 0,
    "icar_vr":   1,
    "icar_mr":   2,
    "icar_3dr":  3,
}


async def seed_icar16(db: AsyncSession) -> TestCatalogue:
    """Seed idempotent de l'ICAR-16 (8 items text-based — P2 pour items visuels)."""
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()

    if existing:
        print(f"  [icar16] Already present (id={existing.id}) — skip")
        return existing

    catalogue = TestCatalogue(
        name=_CATALOGUE_NAME,
        description=(
            "ICAR-16 — International Cognitive Ability Resource. "
            "16 items QCM évaluant l'habilité cognitive générale (Gf) via 4 sous-tests : "
            "Letter-Number Series Reasoning, Verbal Reasoning, Matrix Reasoning, 3D Rotation. "
            "4 items par sous-test. "
            "Instrument de référence (étalon) pour la calibration du GCA propriétaire Radiant Analytics. "
            "Note : 8 items visuels (Matrix Reasoning + 3D Rotation) seront ajoutés en P2. "
            "Durée estimée (8 items P1) : 5–8 minutes."
        ),
        instructions=(
            "For each question, select the answer that best completes the series or analogy. "
            "Work as quickly and accurately as you can. "
            "There is only one correct answer per question."
        ),
        test_type="qcm",
        max_score_per_question=1,
        n_questions=8,  # 16 total quand P2 sera implémenté
        is_active=True,
        status="ETALON",
        license="ICAR_PUBLIC_DOMAIN",
        domain=CatalogueDomain.cognitive,
        validation_notes=(
            "ICAR-16 — Condon, D.M., & Revelle, W. (2014). "
            "The International Cognitive Ability Resource: Development and initial validation "
            "of a public-domain measure. Intelligence, 43, 52–64. "
            "Domaine public — https://osf.io/cg9jh. Utilisation libre sans restriction. "
            "⚠️ ÉTALON R&D UNIQUEMENT — ne pas déployer en production commerciale. "
            "Étalon de calibration pour Q2 GCA (construct Gf — Fluid Intelligence). "
            "Alphas attendus (16 items complets) : LNSR α ≈ .69 | VR α ≈ .62 | "
            "MR α ≈ .71 | 3DR α ≈ .73 (Condon & Revelle, 2014). "
            "Scoring : 1 point par bonne réponse, 0 sinon. "
            "Score total /16 (ou /8 pour version P1 text-only). "
            "⚠️ NOTE P2 : items Matrix Reasoning et 3D Rotation non seedés — "
            "nécessitent rendu graphique frontend. Vérifier le wording exact des items "
            "text-based contre la source officielle avant production (osf.io/cg9jh)."
        ),
        modules_config=[
            {
                "index": 0,
                "name": "Letter-Number Series Reasoning",
                "trait": "icar_lnsr",
                "n_items": 4,
                "duration_min": 2,
                "priority": "STANDARD",
                "description": "Raisonnement inductif sur séries — Gf (fluid intelligence)",
            },
            {
                "index": 1,
                "name": "Verbal Reasoning",
                "trait": "icar_vr",
                "n_items": 4,
                "duration_min": 2,
                "priority": "STANDARD",
                "description": "Analogies et raisonnement verbal — Gc (crystallized intelligence)",
            },
            {
                "index": 2,
                "name": "Matrix Reasoning",
                "trait": "icar_mr",
                "n_items": 0,  # P2 — items visuels non encore seedés
                "duration_min": 0,
                "priority": "STANDARD",
                "description": "Raisonnement abstrait matriciel (Raven-like) — P2, items visuels",
                "p2_note": "Nécessite rendu graphique frontend (grilles abstraites 3×3).",
            },
            {
                "index": 3,
                "name": "3D Rotation",
                "trait": "icar_3dr",
                "n_items": 0,  # P2 — items visuels non encore seedés
                "duration_min": 0,
                "priority": "STANDARD",
                "description": "Rotation mentale tridimensionnelle — P2, items visuels",
                "p2_note": "Nécessite rendu Three.js/WebGL côté frontend.",
            },
        ],
    )
    db.add(catalogue)
    await db.flush()

    for q in ICAR16_QUESTIONS:
        db.add(Question(
            test_id=catalogue.id,
            order=q["order"],
            text=q["text"],
            question_type="qcm",
            trait=q["trait"],
            options=q["options"],
            correct_answer=q["correct_answer"],
            reverse=q["reverse"],
            module_index=_TRAIT_MODULE.get(q["trait"]),
        ))

    await db.flush()
    print(f"  [icar16] Seeded '{_CATALOGUE_NAME}' ({len(ICAR16_QUESTIONS)} questions — P2: +8 visual items)")
    return catalogue


async def delete_icar16(db: AsyncSession) -> None:
    existing = (await db.execute(
        select(TestCatalogue).where(TestCatalogue.name == _CATALOGUE_NAME)
    )).scalar_one_or_none()
    if existing:
        await db.execute(delete(Question).where(Question.test_id == existing.id))
        await db.delete(existing)
        await db.flush()
        print(f"  [icar16] Deleted '{_CATALOGUE_NAME}'")


async def _main() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.core.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        await delete_icar16(db)
        await seed_icar16(db)
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
