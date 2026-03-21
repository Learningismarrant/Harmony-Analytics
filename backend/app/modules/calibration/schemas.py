# app/modules/calibration/schemas.py
"""
Schémas Pydantic pour le module d'étalonnage psychométrique.

Tous les inputs sont validés (longueurs, ranges, format email).
Aucune dépendance vers les schémas de production.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


# ── Catalogues ────────────────────────────────────────────────────────────────

class CatalogueInfoOut(BaseModel):
    id: int
    name: str
    description: str
    test_type: str
    n_questions: int
    status: str
    license: str

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
