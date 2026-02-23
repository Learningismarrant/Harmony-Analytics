# modules/crew/router.py
"""
Endpoints de gestion d'équipage et du Daily Pulse.

Changements v2 :
- Candidats : CrewDep (retourne CrewProfile directement)
- Clients   : EmployerDep (retourne EmployerProfile directement)
- crew_profile_id dans les paths au lieu de user_id
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional

from app.shared.deps import DbDep, CrewDep, EmployerDep
from app.modules.crew.service import CrewService
from app.modules.crew.schemas import (
    CrewAssignIn,
    CrewMemberOut,
    DailyPulseIn,
    DailyPulseOut,
    DashboardOut,
)

router = APIRouter(prefix="/crew", tags=["Crew"])
service = CrewService()


# ── Affectation personnelle (candidat) ─────────────────────

@router.get("/me/assignment", response_model=Optional[CrewMemberOut])
async def get_my_assignment(db: DbDep, current_crew: CrewDep):
    """Mon affectation active."""
    return await service.get_active_assignment(db, current_crew.id)


# ── Gestion équipage (client) ──────────────────────────────

@router.get("/{yacht_id}/members", response_model=List[CrewMemberOut])
async def list_crew(
    yacht_id: int,
    db: DbDep,
    current_employer: EmployerDep,   # v2
):
    crew = await service.get_active_crew(db, yacht_id=yacht_id, employer=current_employer)
    if crew is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Yacht introuvable ou accès refusé.")
    return crew


@router.post("/{yacht_id}/members", response_model=CrewMemberOut, status_code=201)
async def add_crew_member(
    yacht_id: int,
    payload: CrewAssignIn,
    db: DbDep,
    current_employer: EmployerDep,
):
    """
    Assigne un marin à un yacht.
    payload.crew_profile_id (v2) au lieu de payload.user_id.
    """
    try:
        return await service.assign_member(
            db, yacht_id=yacht_id, payload=payload, employer=current_employer
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/{yacht_id}/members/{crew_profile_id}", status_code=204)
async def remove_crew_member(
    yacht_id: int,
    crew_profile_id: int,       # v2 : était user_id dans l'URL
    db: DbDep,
    current_employer: EmployerDep,
):
    """Clôture le contrat du marin (soft delete)."""
    try:
        await service.remove_member(
            db,
            yacht_id=yacht_id,
            crew_profile_id=crew_profile_id,    # v2
            employer=current_employer,
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    except KeyError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


# ── Dashboard ──────────────────────────────────────────────

@router.get("/{yacht_id}/dashboard", response_model=DashboardOut)
async def get_dashboard(
    yacht_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    dashboard = await service.get_full_dashboard(
        db, yacht_id=yacht_id, employer=current_employer
    )
    if dashboard is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Yacht introuvable ou accès refusé.")
    return dashboard


# ── Daily Pulse (candidat) ─────────────────────────────────

@router.post("/pulse", response_model=DailyPulseOut, status_code=201)
async def submit_pulse(
    payload: DailyPulseIn,
    db: DbDep,
    current_crew: CrewDep,      # v2
):
    """
    Soumet le pulse du jour.
    Contraintes : assignation active requise, une soumission par jour.
    """
    try:
        return await service.submit_daily_pulse(db, crew=current_crew, payload=payload)
    except ValueError as e:
        code = str(e)
        if code == "NO_ACTIVE_ASSIGNMENT":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vous devez être assigné à un yacht actif.")
        if code == "ALREADY_SUBMITTED_TODAY":
            raise HTTPException(status.HTTP_409_CONFLICT, "Pulse déjà transmis aujourd'hui.")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, code)


@router.get("/pulse/history", response_model=List[DailyPulseOut])
async def get_pulse_history(db: DbDep, current_crew: CrewDep):
    """30 derniers pulses du marin connecté."""
    return await service.get_pulse_history(db, current_crew.id)