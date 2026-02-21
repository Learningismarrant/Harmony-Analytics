# app/models/__init__.py
"""
Point d'entrée unique pour tous les modèles SQLAlchemy.

TOUJOURS importer les modèles depuis ce fichier :
  from app.models import User, Yacht, TestResult, ...

Jamais directement depuis app.models.user, etc.
→ Garantit que tous les modèles sont enregistrés dans Base.metadata
  avant la création des tables (Alembic, create_all).

Ordre d'import : pas de dépendances circulaires car
les FKs sont déclarées dans les migrations, pas dans les modèles.
"""

from User       import User, CrewProfile, EmployerProfile, UserDocument
from Yacht      import Yacht, CrewAssignment
from Assessment import TestCatalogue, Question, TestResult
from Campaign   import Campaign, CampaignCandidate
from Pulse      import DailyPulse
from Survey     import Survey, SurveyResponse, RecruitmentEvent, ModelVersion

__all__ = [
    # User
    "User", "CrewProfile", "EmployerProfile", "UserDocument",
    # Yacht
    "Yacht","CrewAssignment",
    # Assessment
    "TestCatalogue",
    "Question",
    "TestResult",
    # Recruitment
    "Campaign",
    "CampaignCandidate",
    # Pulse
    "DailyPulse",
    # Survey + ML Pipeline
    "Survey",
    "SurveyResponse",
    "RecruitmentEvent",
    "ModelVersion",
]