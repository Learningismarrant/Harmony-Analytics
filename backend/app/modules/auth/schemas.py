# app/modules/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from app.shared.enums import UserRole, YachtPosition


# ── Register ──────────────────────────────────────────────

class RegisterCrewIn(BaseModel):
    """Inscription d'un marin / candidat."""
    email:    EmailStr
    password: str = Field(..., min_length=6)
    name:     str = Field(..., min_length=2)
    phone:    Optional[str] = None
    location: Optional[str] = None
    position_targeted: YachtPosition = YachtPosition.DECKHAND
    experience_years:  int = Field(0, ge=0)


class RegisterEmployerIn(BaseModel):
    """Inscription d'un client / owner / manager."""
    email:        EmailStr
    password:     str = Field(..., min_length=6)
    name:         str = Field(..., min_length=2)
    phone:        Optional[str] = None
    location:     Optional[str] = None
    company_name: Optional[str] = None


# ── Login ─────────────────────────────────────────────────

class LoginIn(BaseModel):
    email:    EmailStr
    password: str


# ── Tokens ───────────────────────────────────────────────

class TokenOut(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    role:          UserRole
    user_id:       int
    profile_id:    int   # crew_profile.id ou employer_profile.id


class RefreshIn(BaseModel):
    refresh_token: str


class AccessTokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ── Réponse post-register ─────────────────────────────────

class RegisterOut(BaseModel):
    message:    str
    user_id:    int
    role:       UserRole
    token:      TokenOut


# ── Mot de passe ──────────────────────────────────────────

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password:     str = Field(..., min_length=6)

    @model_validator(mode="after")
    def passwords_differ(self):
        if self.current_password == self.new_password:
            raise ValueError("Le nouveau mot de passe doit être différent.")
        return self


class ResetPasswordRequestIn(BaseModel):
    email: EmailStr


class ResetPasswordConfirmIn(BaseModel):
    token:        str
    new_password: str = Field(..., min_length=6)