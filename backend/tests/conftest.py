# tests/conftest.py
"""
Fixtures et factories partagées sur l'ensemble de la suite de tests.

Trois couches :
    1. Engine  — fonctions pures, aucun mock nécessaire (factories de snapshots)
    2. Service — mocks AsyncSession + repos via pytest-mock
    3. Router  — httpx.AsyncClient + dependency_overrides FastAPI
"""
import pytest
from types import SimpleNamespace
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.shared.deps import get_current_user, get_current_crew, get_current_employer
from app.shared.enums import UserRole, YachtPosition, CampaignStatus, ApplicationStatus


# ── Snapshot psychométrique (input principal des engines) ─────────────────────

def snapshot_full() -> dict:
    """Snapshot complet — tous les traits requis par l'engine."""
    return {
        "big_five": {
            "conscientiousness": 75.0,
            "agreeableness": 70.0,
            "neuroticism": 35.0,
            "emotional_stability": 65.0,
            "openness": 60.0,
            "extraversion": 55.0,
        },
        "cognitive": {
            "gca_score": 72.0,
            "logical": 74.0,
            "numerical": 70.0,
            "verbal": 72.0,
        },
        "motivation": {
            "intrinsic": 80.0,
            "identified": 70.0,
            "amotivation": 15.0,
        },
        "leadership_preferences": {
            "autonomy_preference": 0.6,
            "feedback_preference": 0.5,
            "structure_preference": 0.7,
        },
        "resilience": {"global": 65.0},
        "meta": {
            "completeness": 0.90,
            "last_updated": datetime.utcnow().isoformat(),
            "tests_taken": ["big_five_v1", "gca_v1"],
        },
    }


def snapshot_partial() -> dict:
    """Snapshot partiel — big_five seulement, cognitive absent."""
    return {
        "big_five": {
            "agreeableness": 60.0,
            "conscientiousness": 55.0,
        },
    }


def snapshot_empty() -> dict:
    """Snapshot vide — aucune donnée psychométrique."""
    return {}


def snapshot_jerk(agreeableness: float = 25.0) -> dict:
    """Snapshot avec agréabilité sous le seuil JERK_FILTER_DANGER (35)."""
    snap = snapshot_full()
    snap["big_five"]["agreeableness"] = agreeableness
    return snap


def snapshot_high_neuroticism(neuroticism: float = 75.0) -> dict:
    """Snapshot avec névrosisme élevé → ES faible."""
    snap = snapshot_full()
    snap["big_five"]["neuroticism"] = neuroticism
    snap["big_five"]["emotional_stability"] = round(100 - neuroticism, 1)
    return snap


# ── Factories de modèles ORM (SimpleNamespace — léger, sans ORM) ──────────────

def make_user(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "email": "user@test.com",
        "name": "Test User",
        "hashed_password": "hashed_password",
        "role": UserRole.CANDIDATE,
        "is_active": True,
        "is_harmony_verified": False,
        "phone": None,
        "location": None,
        "avatar_url": None,
        "crew_profile": None,
        "employer_profile": None,
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 1),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_crew_profile(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "user_id": 1,
        "position_targeted": YachtPosition.DECKHAND,
        "experience_years": 2,
        "availability_status": "available",
        "psychometric_snapshot": None,
        "snapshot_updated_at": None,
        "trust_score": None,
        # Propriétés calculées sur le modèle ORM
        "name": "Test User",
        "email": "user@test.com",
        "avatar_url": None,
        "is_harmony_verified": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_employer_profile(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "user_id": 2,
        "company_name": "Test Yacht Co",
        "is_billing_active": True,
        "fleet_snapshot": None,
        "fleet_updated_at": None,
        "name": "Employer User",
        "fleet_size": 1,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_yacht(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "employer_profile_id": 1,
        "name": "Lady Aurora",
        "type": "Motor",
        "length": 45.0,
        "boarding_token": "test-token-abc",
        "vessel_snapshot": None,
        "snapshot_updated_at": None,
        "captain_leadership_vector": None,
        "toxicity_flag": False,
        "required_es_minimum": None,
        "created_at": datetime(2025, 1, 1),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_test_catalogue(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "name": "Big Five v1",
        "description": "Test de personnalité",
        "instructions": "Répondez sincèrement.",
        "test_type": "likert",
        "n_questions": 30,
        "max_score_per_question": 5,
        "is_active": True,
        "created_at": datetime(2025, 1, 1),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_question(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "test_id": 1,
        "text": "J'aime travailler en équipe.",
        "question_type": "likert",
        "options": None,
        "trait": "agreeableness",
        "correct_answer": None,
        "reverse": False,
        "order": 1,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_test_result(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "crew_profile_id": 1,
        "test_id": 1,
        "global_score": 75.0,
        "test_name": "big_five_v1",
        "created_at": datetime(2025, 1, 15, 10, 0, 0),
        "scores": {
            "traits": {
                "agreeableness": {"score": 75.0, "niveau": "Élevé"},
                "conscientiousness": {"score": 72.0, "niveau": "Élevé"},
                "neuroticism": {"score": 35.0, "niveau": "Moyen"},
                "openness": {"score": 60.0, "niveau": "Moyen"},
                "extraversion": {"score": 55.0, "niveau": "Moyen"},
            },
            "reliability": {"is_reliable": True, "reasons": []},
            "global_score": 75.0,
            "meta": {"total_time_seconds": 300, "avg_seconds_per_question": 10.0},
        },
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_campaign(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "employer_profile_id": 1,
        "yacht_id": 1,
        "title": "Chef de pont recherché",
        "position": "bosun",
        "description": "Poste CDI Méditerranée.",
        "status": CampaignStatus.OPEN,
        "is_archived": False,
        "invite_token": "invite-abc123",
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 1),
        "yacht_name": "Lady Aurora",
        "candidate_count": 0,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_crew_assignment(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "crew_profile_id": 1,
        "yacht_id": 1,
        "role": YachtPosition.BOSUN,
        "is_active": True,
        "start_date": datetime(2025, 1, 1),
        "end_date": None,
        "external_yacht_name": None,
        "contract_type": "CDI",
        "candidate_comment": None,
        "reference_comment": None,
        "is_harmony_approved": False,
        "reference_contact_email": None,
        "verification_token": None,
        "yacht_name": "Lady Aurora",
        "name": "Test User",
        "avatar_url": None,
        "is_harmony_verified": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_daily_pulse(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "crew_profile_id": 1,
        "yacht_id": 1,
        "score": 4,
        "comment": None,
        "created_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_survey(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "title": "Bilan post-charter",
        "yacht_id": 1,
        "triggered_by_id": 1,
        "trigger_type": "post_charter",
        "target_crew_ids": [1, 2],
        "is_open": True,
        "created_at": datetime(2025, 1, 1),
        "closed_at": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_survey_response(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "survey_id": 1,
        "crew_profile_id": 1,
        "yacht_id": 1,
        "trigger_type": "post_charter",
        "team_cohesion_observed": 70.0,
        "workload_felt": 60.0,
        "leadership_fit_felt": 75.0,
        "individual_performance_self": 80.0,
        "intent_to_stay": 80.0,
        "free_text": None,
        "submitted_at": datetime.utcnow(),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── DB mock factory ───────────────────────────────────────────────────────────

def make_async_db() -> AsyncMock:
    """
    AsyncMock simulant une AsyncSession SQLAlchemy.
    Fournit une side_effect sur refresh() pour simuler le SET d'ID par le DB.
    """
    db = AsyncMock(spec=AsyncSession)
    added_objects: list = []

    def capture_add(obj):
        added_objects.append(obj)

    db.add = MagicMock(side_effect=capture_add)

    async def flush_side_effect():
        for i, obj in enumerate(added_objects):
            if not getattr(obj, "id", None):
                object.__setattr__(obj, "id", i + 1) if hasattr(obj, "__dict__") else None
                try:
                    obj.id = i + 1
                except (AttributeError, TypeError):
                    pass

    db.flush = AsyncMock(side_effect=flush_side_effect)

    async def refresh_side_effect(obj):
        if not getattr(obj, "id", None):
            try:
                obj.id = 1
            except (AttributeError, TypeError):
                pass

    db.refresh = AsyncMock(side_effect=refresh_side_effect)
    db.commit = AsyncMock()
    db.close = AsyncMock()

    return db


# ── Fixtures HTTP (httpx.AsyncClient + dependency_overrides) ─────────────────

@pytest.fixture
async def client():
    """Client sans auth — pour endpoints publics ou mocker le service entier."""
    mock_db = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def crew_client():
    """Client authentifié comme CrewProfile (rôle CANDIDATE)."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_crew = make_crew_profile()
    mock_user = make_user(crew_profile=mock_crew)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_crew] = lambda: mock_crew
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def employer_client():
    """Client authentifié comme EmployerProfile (rôle CLIENT)."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_employer = make_employer_profile()
    mock_user = make_user(id=2, role=UserRole.CLIENT, employer_profile=mock_employer)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_employer] = lambda: mock_employer
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
