# app/modules/calibration/schemas.py
"""
Schémas Pydantic pour le module d'étalonnage psychométrique.

Tous les inputs sont validés (longueurs, ranges, format email).
Aucune dépendance vers les schémas de production.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.models.Assessment import CatalogueDomain


# ── Auth calibrateur ───────────────────────────────────────────────────────────

class CalibratorRegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    cohort: str | None = Field(default=None, max_length=100)


class CalibratorLoginIn(BaseModel):
    email: EmailStr
    password: str


class CalibratorTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    calibrator_id: int
    name: str


# ── Démographiques ────────────────────────────────────────────────────────────
# Collectés séparément (PATCH /calibration/me) pour ne pas surcharger l'inscription.
# Ces données permettent l'analyse DIF (Differential Item Functioning) :
# vérifier qu'aucun item n'avantage systématiquement un groupe démographique.

class CalibratorDemographicsIn(BaseModel):
    gender: Literal["male", "female", "non_binary", "prefer_not_to_say"] | None = None
    birth_year: int | None = Field(
        default=None, ge=1940, le=2010,
        description="Année de naissance (pas l'âge — stable dans le temps)"
    )
    education_level: Literal[
        "below_bac", "bac", "bac_plus_2", "bac_plus_3", "bac_plus_5", "phd"
    ] | None = None
    native_language: Literal["french", "english", "other"] | None = Field(
        default=None,
        description="Langue maternelle — critique pour items en anglais (HEXACO-60, ICAR)"
    )
    years_at_sea: int | None = Field(
        default=None, ge=0, le=60,
        description="Années d'expérience maritime (0 = aucune)"
    )
    maritime_role: Literal[
        "captain", "officer", "bosun", "deckhand", "steward", "engineer", "other", "none"
    ] | None = None
    nationality: str | None = Field(default=None, max_length=100)


class CalibratorMeOut(BaseModel):
    id: int
    email: str
    name: str
    cohort: str | None = None
    gender: str | None = None
    birth_year: int | None = None
    education_level: str | None = None
    native_language: str | None = None
    years_at_sea: int | None = None
    maritime_role: str | None = None
    nationality: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Catalogues ────────────────────────────────────────────────────────────────

class CatalogueInfoOut(BaseModel):
    id: int
    name: str
    description: str
    test_type: str
    n_questions: int
    status: str
    license: str
    domain: CatalogueDomain

    model_config = ConfigDict(from_attributes=True)


# ── Questions ─────────────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    id: int
    order: int
    text: str
    question_type: str
    trait: str | None = None
    options: list[Any] | None = None
    reverse: bool

    model_config = ConfigDict(from_attributes=True)


# ── Sessions ──────────────────────────────────────────────────────────────────

class StartSessionIn(BaseModel):
    catalogue_id: int = Field(..., gt=0)
    device_info: dict[str, Any] | None = None


class SessionOut(BaseModel):
    id: int
    calibrator_id: int
    catalogue_id: int
    started_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionListOut(BaseModel):
    sessions: list[SessionOut]


# ── Réponses ──────────────────────────────────────────────────────────────────

class ResponseItemIn(BaseModel):
    question_id: int = Field(..., gt=0)
    value: int = Field(..., ge=0, le=10)        # 0-10 couvre Likert 1-7 et QCM binaire
    seconds_spent: float | None = Field(default=None, ge=0.0, le=3600.0)


class SubmitResponsesIn(BaseModel):
    responses: list[ResponseItemIn] = Field(..., min_length=1)


class SubmitResponsesOut(BaseModel):
    session_id: int
    n_responses: int
    completed: bool


# ── Score CTT ─────────────────────────────────────────────────────────────────

class TraitScoreOut(BaseModel):
    trait: str
    label: str
    raw_mean: float = Field(..., description="Moyenne brute non normalisée")
    score: float = Field(..., ge=0.0, le=100.0, description="Score normalisé 0-100")
    n_items: int


class SessionScoreOut(BaseModel):
    session_id: int
    catalogue_id: int
    catalogue_name: str
    test_type: str
    overall_score: float = Field(..., ge=0.0, le=100.0)
    traits: list[TraitScoreOut]
    n_responses: int
    completed: bool = True
    disclaimer: str = "Résultat indicatif — normes non établies sur l'ensemble des calibrateurs."
