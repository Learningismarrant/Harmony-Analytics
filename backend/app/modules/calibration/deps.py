# app/modules/calibration/deps.py
"""
Dépendances d'authentification spécifiques au module calibration.

Totalement isolé du système de rôles principal (UserDep/CrewDep/EmployerDep).
Le JWT calibrateur porte {"sub": "<calibrator_id>", "role": "calibrator"}.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.shared.models.Calibration import CalibratorUser

_bearer = HTTPBearer()


async def get_current_calibrator(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CalibratorUser:
    """
    Décode le JWT et retourne le CalibratorUser correspondant.
    Lève 401 si le token est invalide, expiré, ou ne porte pas role=calibrator.
    Lève 401 si le calibrateur est introuvable ou inactif.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": True,
            "message": "Token invalide ou expiré.",
            "code": "INVALID_TOKEN",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        calibrator_id: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if calibrator_id is None or role != "calibrator":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(CalibratorUser).where(CalibratorUser.id == int(calibrator_id))
    )
    calibrator = result.scalar_one_or_none()

    if not calibrator or not calibrator.is_active:
        raise credentials_exception

    return calibrator


# Alias Annotated pour injection dans les routers
CalibDep = Annotated[CalibratorUser, Depends(get_current_calibrator)]
