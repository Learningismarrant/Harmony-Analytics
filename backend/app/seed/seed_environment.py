# seeds/seed_environment.py
"""
Seed d'environnement — base de données de test complète.

Contenu :
    2 EmployerProfile (gestionnaires de flotte)
    4 Yachts (2 par employer, avec vessel_snapshot + JD-R params)
    14 Users + CrewProfile (profils variés — couvrent tous les buckets DNRE)
    8  CrewAssignments actifs (équipages constitués)
    2  Campaigns ouvertes (1 par employer)
    6  CampaignCandidate (candidats en pool, statuts variés)

Profils psychométriques couverts intentionnellement :
    ELITE        → Marcus Webb, Isabelle Moreau, Tom Bradley
    GOOD_FIT     → Sofia Reyes, Emma Larsen, Mei Zhang, Clara Dumont, Aisha Nkosi
    MODERATE     → Niko Papadis, Jake Torres, Lena Kovacs, Ryan Okafor
    HIGH_RISK    → Dimitri Volkov (ES=22, soft veto), Carlos Mendez (ES=18)
    DISQUALIFIED → Sam Adler (ES=10, hard veto)

Usage :
    python -m seeds.seed_environment
    (ou via alembic post-migration)
"""
import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
from app.shared.models import (
    User, CrewProfile, EmployerProfile,
    Yacht, CrewAssignment,
)
from app.shared.models import Campaign, CampaignCandidate, ModelVersion
from app.shared.enums import UserRole, YachtPosition, AvailabilityStatus, CampaignStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash(password: str) -> str:
    return pwd_context.hash(password)

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _ago(days: int) -> datetime:
    return _now() - timedelta(days=days)


# ── Psychometric snapshots ─────────────────────────────────────────────────────
# Format unifié v2 — utilisé par le DNRE + MLPSM

def _snapshot(
    agreeableness: float,
    conscientiousness: float,
    neuroticism: float,         # ES = 100 - neuroticism
    openness: float,
    extraversion: float,
    gca: float,
    resilience: float,
    autonomy: float = 0.5,
    feedback: float = 0.5,
    structure: float = 0.6,
) -> dict:
    es = round(100.0 - neuroticism, 1)
    return {
        "version": "2.0",
        "big_five": {
            "agreeableness":     {"score": agreeableness, "reliable": True},
            "conscientiousness": {"score": conscientiousness, "reliable": True},
            "neuroticism":       {"score": neuroticism, "reliable": True},
            "openness":          {"score": openness, "reliable": True},
            "extraversion":      {"score": extraversion, "reliable": True},
        },
        "emotional_stability": es,
        "cognitive": {
            "gca_score": gca,
            "n_tests": 2,
        },
        "resilience": resilience,
        "leadership_preferences": {
            "autonomy_preference": autonomy,
            "feedback_preference": feedback,
            "structure_preference": structure,
        },
        "onboarding_tips": {
            "first_week": ["Observer la dynamique avant d'initier des changements."],
            "month_1": ["Développer des routines de communication claire."],
        },
        "integration_risks": [],
        "management_advice": {},
        "test_history": [],
    }


# ── Snapshots des profils ──────────────────────────────────────────────────────

SNAPSHOTS = {
    # ── ELITE ──────────────────────────────────────────────────────────────────
    "marcus_webb": _snapshot(
        agreeableness=72, conscientiousness=82, neuroticism=22,
        openness=68, extraversion=74, gca=80, resilience=78,
        autonomy=0.7, feedback=0.4, structure=0.8,
    ),
    "isabelle_moreau": _snapshot(
        agreeableness=70, conscientiousness=85, neuroticism=25,
        openness=72, extraversion=66, gca=77, resilience=76,
        autonomy=0.65, feedback=0.55, structure=0.75,
    ),
    "tom_bradley": _snapshot(   # Candidat STRONG_FIT
        agreeableness=74, conscientiousness=81, neuroticism=21,
        openness=70, extraversion=71, gca=78, resilience=80,
        autonomy=0.68, feedback=0.52, structure=0.78,
    ),

    # ── GOOD_FIT ────────────────────────────────────────────────────────────────
    "sofia_reyes": _snapshot(
        agreeableness=68, conscientiousness=79, neuroticism=29,
        openness=65, extraversion=60, gca=74, resilience=71,
        autonomy=0.6, feedback=0.5, structure=0.7,
    ),
    "emma_larsen": _snapshot(
        agreeableness=80, conscientiousness=68, neuroticism=34,
        openness=74, extraversion=78, gca=58, resilience=66,
        autonomy=0.4, feedback=0.65, structure=0.55,
    ),
    "mei_zhang": _snapshot(
        agreeableness=76, conscientiousness=65, neuroticism=31,
        openness=71, extraversion=69, gca=61, resilience=69,
        autonomy=0.5, feedback=0.6, structure=0.6,
    ),
    "clara_dumont": _snapshot(
        agreeableness=82, conscientiousness=62, neuroticism=27,
        openness=68, extraversion=76, gca=56, resilience=73,
        autonomy=0.45, feedback=0.7, structure=0.5,
    ),
    "aisha_nkosi": _snapshot(   # Candidat GOOD_FIT
        agreeableness=66, conscientiousness=77, neuroticism=32,
        openness=74, extraversion=62, gca=75, resilience=70,
        autonomy=0.62, feedback=0.48, structure=0.72,
    ),

    # ── MODERATE ────────────────────────────────────────────────────────────────
    "niko_papadis": _snapshot(
        agreeableness=74, conscientiousness=71, neuroticism=38,
        openness=62, extraversion=58, gca=65, resilience=62,
        autonomy=0.55, feedback=0.5, structure=0.65,
    ),
    "jake_torres": _snapshot(
        agreeableness=58, conscientiousness=73, neuroticism=45,
        openness=60, extraversion=52, gca=70, resilience=55,
        autonomy=0.6, feedback=0.45, structure=0.7,
    ),
    "lena_kovacs": _snapshot(
        agreeableness=62, conscientiousness=60, neuroticism=52,
        openness=58, extraversion=61, gca=52, resilience=50,
        autonomy=0.5, feedback=0.5, structure=0.55,
    ),
    "ryan_okafor": _snapshot(
        agreeableness=52, conscientiousness=64, neuroticism=56,
        openness=55, extraversion=55, gca=55, resilience=48,
        autonomy=0.5, feedback=0.55, structure=0.6,
    ),

    # ── HIGH_RISK (ES soft veto : 15-30) ────────────────────────────────────────
    "dimitri_volkov": _snapshot(
        agreeableness=35, conscientiousness=55, neuroticism=78,   # ES=22
        openness=45, extraversion=48, gca=48, resilience=28,
        autonomy=0.7, feedback=0.3, structure=0.4,
    ),
    "carlos_mendez": _snapshot(   # Candidat HIGH_RISK
        agreeableness=40, conscientiousness=52, neuroticism=82,   # ES=18
        openness=42, extraversion=44, gca=49, resilience=24,
        autonomy=0.65, feedback=0.35, structure=0.45,
    ),

    # ── DISQUALIFIED (ES hard veto : < 15) ──────────────────────────────────────
    "sam_adler": _snapshot(
        agreeableness=45, conscientiousness=50, neuroticism=90,   # ES=10
        openness=40, extraversion=42, gca=44, resilience=15,
        autonomy=0.6, feedback=0.4, structure=0.5,
    ),
}


# ── Vessel snapshots ───────────────────────────────────────────────────────────

def _vessel_snapshot(
    crew_snapshots: list,
    jdr_demands_level: float = 0.6,
    jdr_resources_level: float = 0.7,
    captain_autonomy: float = 0.5,
    captain_feedback: float = 0.6,
    captain_structure: float = 0.7,
) -> dict:
    """Snapshot précalculé pour éviter le recalcul au démarrage."""
    return {
        "crew_count": len(crew_snapshots),
        "jdr_params": {
            "demands_level": jdr_demands_level,
            "resources_level": jdr_resources_level,
            "workload_index": round(jdr_demands_level * 0.6 + (1 - jdr_resources_level) * 0.4, 2),
        },
        "captain_leadership_vector": {
            "autonomy": captain_autonomy,
            "feedback": captain_feedback,
            "structure": captain_structure,
        },
        "harmony_result": {
            "performance": 72.0,
            "cohesion": 68.0,
            "risk_factors": {
                "conscientiousness_divergence": 9.2,
                "weakest_link_stability": 44.0,
            }
        },
        "f_team_baseline_score": 72.0,
        "f_team_data_quality": 1.0,
        "f_team_flags": [],
    }


# ── Seed principal ─────────────────────────────────────────────────────────────

async def seed(db: AsyncSession) -> None:
    print("🌱 Seed environnement démarré...")

    

    # ────────────────────────────────────────────────────────────────────────────
    # 2. Employers
    # ────────────────────────────────────────────────────────────────────────────
    user_thomas = User(
        email="thomas.laurent@azure-maritime.com",
        name="Thomas Laurent",
        hashed_password=_hash("testpassword123"),
        role=UserRole.CLIENT,
        is_active=True,
        location="Monaco",
        created_at=_ago(60),
    )
    db.add(user_thomas)
    await db.flush()

    employer_azure = EmployerProfile(
        user_id=user_thomas.id,
        company_name="Azure Maritime Management",
        is_billing_active=True,
    )
    db.add(employer_azure)

    user_diana = User(
        email="diana.chen@pacific-yachting.com",
        name="Diana Chen",
        hashed_password=_hash("testpassword123"),
        role=UserRole.CLIENT,
        is_active=True,
        location="Antibes",
        created_at=_ago(45),
    )
    db.add(user_diana)
    await db.flush()

    employer_pacific = EmployerProfile(
        user_id=user_diana.id,
        company_name="Pacific Yachting Group",
        is_billing_active=True,
    )
    db.add(employer_pacific)
    await db.flush()

    print(f"  ✓ Employers : Azure Maritime (id={employer_azure.id}), Pacific Yachting (id={employer_pacific.id})")

    # ────────────────────────────────────────────────────────────────────────────
    # 3. Yachts
    # ────────────────────────────────────────────────────────────────────────────
    crew_snaps_aurora = [
        SNAPSHOTS["marcus_webb"],
        SNAPSHOTS["sofia_reyes"],
        SNAPSHOTS["niko_papadis"],
        SNAPSHOTS["emma_larsen"],
    ]

    yacht_aurora = Yacht(
        name="Lady Aurora",
        length=55,
        type="Motor",
        employer_profile_id=employer_azure.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            crew_snaps_aurora,
            jdr_demands_level=0.7,   # Charter med intense
            jdr_resources_level=0.75,
            captain_autonomy=0.7, captain_feedback=0.4, captain_structure=0.8,
        ),
        captain_leadership_vector={
        "autonomy_given": 0.7,
        "feedback_style": 0.4,
        "structure_imposed": 0.8,
    },
        created_at=_ago(50),
    )
    db.add(yacht_aurora)

    yacht_nomad = Yacht(
        name="Nomad Spirit",
        length=42,
        type="Sail",
        employer_profile_id=employer_azure.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["isabelle_moreau"], SNAPSHOTS["jake_torres"], SNAPSHOTS["lena_kovacs"]],
            jdr_demands_level=0.55,  # Croisières tranquilles
            jdr_resources_level=0.8,
            captain_autonomy=0.65, captain_feedback=0.55, captain_structure=0.75,
        ),
        captain_leadership_vector={
        "autonomy_given": 0.3,
        "feedback_style": 0.6,
        "structure_imposed": 0.2,
    },
        created_at=_ago(40),
    )
    db.add(yacht_nomad)

    yacht_stella = Yacht(
        name="Stella Maris",
        length=68,
        type="Motor",
        employer_profile_id=employer_pacific.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["mei_zhang"], SNAPSHOTS["ryan_okafor"], SNAPSHOTS["clara_dumont"]],
            jdr_demands_level=0.8,   # Grand yacht — exigences élevées
            jdr_resources_level=0.7,
            captain_autonomy=0.5, captain_feedback=0.6, captain_structure=0.7,
        ),
        captain_leadership_vector={
        "autonomy_given": 0.3,
        "feedback_style": 0.6,
        "structure_imposed": 0.5,
    },
        created_at=_ago(35),
    )
    db.add(yacht_stella)

    yacht_blue = Yacht(
        name="Blue Horizon",
        length=38,
        type="Motor",
        employer_profile_id=employer_pacific.id,
        boarding_token=secrets.token_urlsafe(16),
        vessel_snapshot=_vessel_snapshot(
            [SNAPSHOTS["dimitri_volkov"]],   # Équipe incomplète
            jdr_demands_level=0.5,
            jdr_resources_level=0.65,
        ),
        captain_leadership_vector={
        "autonomy_given": 0.1,
        "feedback_style": 0.2,
        "structure_imposed": 0.1,
    },
        created_at=_ago(20),
    )
    db.add(yacht_blue)
    await db.flush()

    print(f"  ✓ Yachts : Lady Aurora ({yacht_aurora.id}), Nomad Spirit ({yacht_nomad.id}), Stella Maris ({yacht_stella.id}), Blue Horizon ({yacht_blue.id})")

    # ────────────────────────────────────────────────────────────────────────────
    # 4. Crew Members (Users + CrewProfile)
    # ────────────────────────────────────────────────────────────────────────────
    crew_data = [
        # id_key, email, name, location, position, exp_years, snapshot_key
        # ── Lady Aurora ──
        ("marcus_webb",    "marcus.webb@gmail.com",      "Marcus Webb",    "UK",      "Captain",       18, "marcus_webb"),
        ("sofia_reyes",    "sofia.reyes@gmail.com",      "Sofia Reyes",    "Spain",   "First Mate",  9, "sofia_reyes"),
        ("niko_papadis",   "niko.papadis@gmail.com",     "Niko Papadis",   "Greece",  "Chef",           7, "niko_papadis"),
        ("emma_larsen",    "emma.larsen@gmail.com",      "Emma Larsen",    "Denmark", "Stewardess",     4, "emma_larsen"),
        # ── Nomad Spirit ──
        ("isabelle_moreau","isabelle.moreau@gmail.com",  "Isabelle Moreau","France",  "First Mate", 11, "isabelle_moreau"),
        ("jake_torres",    "jake.torres@gmail.com",      "Jake Torres",    "USA",     "Chief Engineer",       6, "jake_torres"),
        ("lena_kovacs",    "lena.kovacs@gmail.com",      "Lena Kovacs",    "Hungary", "Deckhand",       2, "lena_kovacs"),
        # ── Stella Maris ──
        ("mei_zhang",      "mei.zhang@gmail.com",        "Mei Zhang",      "China",   "Stewardess",        5, "mei_zhang"),
        ("ryan_okafor",    "ryan.okafor@gmail.com",      "Ryan Okafor",    "Nigeria", "Bosun",          4, "ryan_okafor"),
        ("clara_dumont",   "clara.dumont@gmail.com",     "Clara Dumont",   "France",  "Stewardess",     3, "clara_dumont"),
        # ── Blue Horizon (équipage réduit — pour tester dashboard incomplet) ──
        ("dimitri_volkov", "dimitri.volkov@gmail.com",   "Dimitri Volkov", "Russia",  "Deckhand",       2, "dimitri_volkov"),  # HIGH_RISK
        # ── Sam Adler — DISQUALIFIED — pas assigné (pour test safety barrier) ──
        ("sam_adler",      "sam.adler@gmail.com",        "Sam Adler",      "USA",     "Deckhand",       1, "sam_adler"),
        # ── Candidats non assignés ──
        ("tom_bradley",    "tom.bradley@gmail.com",      "Tom Bradley",    "UK",      "First Mate", 12, "tom_bradley"),    # STRONG_FIT
        ("aisha_nkosi",    "aisha.nkosi@gmail.com",      "Aisha Nkosi",    "Kenya",   "Captain",       14, "aisha_nkosi"),    # GOOD_FIT
        ("carlos_mendez",  "carlos.mendez@gmail.com",    "Carlos Mendez",  "Mexico",  "Deckhand",       1, "carlos_mendez"),  # HIGH_RISK
    ]

    crew_users:    dict = {}
    crew_profiles: dict = {}

    for key, email, name, location, position, exp_years, snap_key in crew_data:
        u = User(
            email=email,
            name=name,
            hashed_password=_hash("testpassword123"),
            role=UserRole.CANDIDATE,
            is_active=True,
            location=location,
            avatar_url=f"https://i.pravatar.cc/150?u={email}",
            is_harmony_verified=True,
            created_at=_ago(40),
        )
        db.add(u)
        await db.flush()

        cp = CrewProfile(
            user_id=u.id,
            position_targeted=YachtPosition(position),
            experience_years=exp_years,
            availability_status=AvailabilityStatus.AVAILABLE,
            psychometric_snapshot=SNAPSHOTS[snap_key],
            snapshot_updated_at=_now(),
        )
        db.add(cp)
        await db.flush()

        crew_users[key]    = u
        crew_profiles[key] = cp

    print(f"  ✓ Crew members : {len(crew_users)} profils créés")

    # ────────────────────────────────────────────────────────────────────────────
    # 5. CrewAssignments actifs
    # ────────────────────────────────────────────────────────────────────────────
    assignments = [
        # Lady Aurora
        (crew_profiles["marcus_webb"],    yacht_aurora.id, "Captain",       _ago(45)),
        (crew_profiles["sofia_reyes"],    yacht_aurora.id, "First Mate",    _ago(40)),
        (crew_profiles["niko_papadis"],   yacht_aurora.id, "Chef",          _ago(38)),
        (crew_profiles["emma_larsen"],    yacht_aurora.id, "Stewardess",    _ago(30)),
        # Nomad Spirit
        (crew_profiles["isabelle_moreau"],yacht_nomad.id,  "First Mate",      _ago(35)),
        (crew_profiles["jake_torres"],    yacht_nomad.id,  "Chief Engineer",  _ago(32)),
        (crew_profiles["lena_kovacs"],    yacht_nomad.id,  "Deckhand",        _ago(20)),
        # Stella Maris
        (crew_profiles["mei_zhang"],      yacht_stella.id, "Stewardess",    _ago(28)),
        (crew_profiles["ryan_okafor"],    yacht_stella.id, "Bosun",         _ago(25)),
        (crew_profiles["clara_dumont"],   yacht_stella.id, "Stewardess",    _ago(22)),
        # Blue Horizon — volontairement réduit
        (crew_profiles["dimitri_volkov"], yacht_blue.id,   "Deckhand",      _ago(10)),
    ]

    for cp, yacht_id, role, start in assignments:
        a = CrewAssignment(
            crew_profile_id=cp.id,
            yacht_id=yacht_id,
            role=YachtPosition(role),
            is_active=True,
            start_date=start,
        )
        db.add(a)

    await db.flush()
    print(f"  ✓ Assignments : {len(assignments)} actifs")

    # ────────────────────────────────────────────────────────────────────────────
    # 6. Campaigns
    # ────────────────────────────────────────────────────────────────────────────
    campaign_aurora = Campaign(
        title="Chief Officer — Lady Aurora (Saison 2025)",
        position="Chief Officer",
        yacht_id=yacht_aurora.id,
        employer_profile_id=employer_azure.id,
        status=CampaignStatus.OPEN,
        invite_token=secrets.token_urlsafe(16),
        description="Remplacement Chief Officer pour saison Méditerranée juillet-septembre.",
        created_at=_ago(15),
    )
    db.add(campaign_aurora)

    campaign_stella = Campaign(
        title="Captain — Stella Maris",
        position="Captain",
        yacht_id=yacht_stella.id,
        employer_profile_id=employer_pacific.id,
        status=CampaignStatus.OPEN,
        invite_token=secrets.token_urlsafe(16),
        description="Recherche capitaine expérimenté pour grand yacht 68m.",
        created_at=_ago(10),
    )
    db.add(campaign_stella)
    await db.flush()

    print(f"  ✓ Campaigns : Aurora ({campaign_aurora.id}), Stella ({campaign_stella.id})")

    # ────────────────────────────────────────────────────────────────────────────
    # 7. CampaignCandidates (pool de matching)
    # ────────────────────────────────────────────────────────────────────────────
    from app.shared.enums import ApplicationStatus

    # Campaign Lady Aurora — Chief Officer
    for key, status in [
        ("tom_bradley",   ApplicationStatus.PENDING),   # STRONG_FIT — à recruter
        ("aisha_nkosi",   ApplicationStatus.PENDING),   # GOOD_FIT
        ("carlos_mendez", ApplicationStatus.PENDING),   # HIGH_RISK — pour tester le filtre
        ("sam_adler",     ApplicationStatus.PENDING),   # DISQUALIFIED — pour tester le veto hard
    ]:
        cc = CampaignCandidate(
            campaign_id=campaign_aurora.id,
            crew_profile_id=crew_profiles[key].id,
            status=status,
            joined_at=_ago(8),
        )
        db.add(cc)

    # Campaign Stella Maris — Captain
    for key, status in [
        ("aisha_nkosi",   ApplicationStatus.PENDING),
        ("marcus_webb",   ApplicationStatus.PENDING),   # Déjà assigné ailleurs — test edge case
    ]:
        cc = CampaignCandidate(
            campaign_id=campaign_stella.id,
            crew_profile_id=crew_profiles[key].id,
            status=status,
            joined_at=_ago(5),
        )
        db.add(cc)

    await db.commit()
    print(f"  ✓ CampaignCandidates créés")
    print("✅ Seed environnement terminé.")
    print()
    print("📋 Résumé pour les tests :")
    print(f"   Employer Azure  : {user_thomas.email} / testpassword123 (id={employer_azure.id})")
    print(f"   Employer Pacific: {user_diana.email} / testpassword123 (id={employer_pacific.id})")
    print(f"   Captain ELITE   : {crew_users['marcus_webb'].email} (crew_profile_id={crew_profiles['marcus_webb'].id})")
    print(f"   HIGH_RISK       : {crew_users['dimitri_volkov'].email} (crew_profile_id={crew_profiles['dimitri_volkov'].id})")
    print(f"   DISQUALIFIED    : {crew_users['sam_adler'].email} (crew_profile_id={crew_profiles['sam_adler'].id})")
    print(f"   Campaign Aurora : id={campaign_aurora.id}, token={campaign_aurora.invite_token}")
    print(f"   Campaign Stella : id={campaign_stella.id}, token={campaign_stella.invite_token}")


async def main():
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())