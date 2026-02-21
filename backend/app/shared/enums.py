# app/shared/enums.py
"""
Toutes les énumérations du projet Harmony.

Source unique de vérité pour les statuts, rôles et types.
Importé par les modèles, schemas, services et engine.
"""

from enum import Enum

class UserRole(str, Enum):
    CANDIDATE = "candidate"
    CLIENT    = "client"    # Cap / Owner / Manager
    ADMIN     = "admin"


class YachtPosition(str, Enum):
    CAPTAIN          = "Captain"
    FIRST_MATE       = "First Mate"
    BOSUN            = "Bosun"
    DECKHAND         = "Deckhand"
    CHIEF_ENGINEER   = "Chief Engineer"
    SECOND_ENGINEER  = "2nd Engineer"
    CHIEF_STEWARDESS = "Chief Stewardess"
    STEWARDESS       = "Stewardess"
    CHEF             = "Chef"


class AvailabilityStatus(str, Enum):
    AVAILABLE   = "available"
    ON_BOARD    = "on_board"
    UNAVAILABLE = "unavailable"
    SOON        = "soon"


class CampaignStatus(str, Enum):
    OPEN   = "open"
    CLOSED = "closed"
    DRAFT  = "draft"


class ApplicationStatus(str, Enum):
    PENDING  = "pending"
    HIRED    = "hired"
    REJECTED = "rejected"
    JOINED   = "joined"     # Marin embarqué → déclenche mode onboarding


class FeedbackTarget(str, Enum):
    CANDIDATE  = "candidate"   # Auto-consultation
    RECRUITER  = "recruiter"   # Client en phase recrutement
    MANAGER    = "manager"     # Client avec marin actif dans l'équipage
    ONBOARDING = "onboarding"  # Client avec marin hired → embarquement imminent


class SurveyTriggerType(str, Enum):
    POST_CHARTER   = "post_charter"    # Après un charter
    POST_SEASON    = "post_season"     # Fin de saison
    MONTHLY_PULSE  = "monthly_pulse"   # Pulse enrichi mensuel
    CONFLICT_EVENT = "conflict_event"  # Manuel, après incident
    EXIT_INTERVIEW = "exit_interview"  # Départ d'un marin (Y_actual définitif)


class DepartureReason(str, Enum):
    PERFORMANCE    = "performance"
    TEAM_CONFLICT  = "team_conflict"
    ENVIRONMENT    = "environment"
    LEADERSHIP     = "leadership"
    EXTERNAL       = "external"       # Raison hors contrôle (santé, famille)
    UNKNOWN        = "unknown"