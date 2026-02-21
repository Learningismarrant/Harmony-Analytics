# modules/crew/router.py
"""
Endpoints de gestion d'équipage et du Daily Pulse.
Couvre : assignation, retrait, dashboard, historique pulse.

Règle : zéro db.query ici. Tout passe par crew_service.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
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


# ─────────────────────────────────────────────
# AFFECTATION PERSONNELLE (candidat)
# ─────────────────────────────────────────────

@router.get(
    "/me/assignment",
    response_model=Optional[CrewMemberOut],
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Mon affectation active",
)
def get_my_assignment(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retourne l'affectation active du marin connecté, ou null."""
    return service.get_active_assignment(db, user_id=current_user.id)


# ─────────────────────────────────────────────
# GESTION ÉQUIPAGE (client / admin)
# ─────────────────────────────────────────────

@router.get(
    "/{yacht_id}/members",
    response_model=List[CrewMemberOut],
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Équipage actif d'un yacht",
)
def list_crew(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Liste les membres actifs d'un yacht.
    Le service vérifie la propriété du yacht.
    """
    crew = service.get_active_crew(db, yacht_id=yacht_id, requester_id=current_user.id)
    if crew is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yacht introuvable ou accès refusé."
        )
    return crew


@router.post(
    "/{yacht_id}/members",
    response_model=CrewMemberOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Ajouter un membre à l'équipage",
)
def add_crew_member(
    yacht_id: int,
    payload: CrewAssignIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Assigne un marin à un yacht.
    Déclenche le recalcul du vessel_snapshot en background.
    Le service vérifie : ownership, doublon d'affectation active.
    """
    try:
        return service.assign_member(
            db, yacht_id=yacht_id, payload=payload, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{yacht_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Retirer un membre (soft delete)",
)
def remove_crew_member(
    yacht_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Clôture le contrat du marin.
    Il passe en 'Past Crew' mais reste dans l'historique.
    Déclenche le recalcul du vessel_snapshot.
    """
    try:
        service.remove_member(
            db, yacht_id=yacht_id, user_id=user_id, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ─────────────────────────────────────────────
# DASHBOARD MANAGEMENT
# ─────────────────────────────────────────────

@router.get(
    "/{yacht_id}/dashboard",
    response_model=DashboardOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Dashboard complet d'un yacht",
)
def get_dashboard(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retourne :
    - Analyse harmony (performance + cohésion)
    - Team Volatility Index + Hidden Conflict Detector
    - Weather trend (pulse agrégé)
    - Diagnostic combiné + recommandations

    Alimenté par vessel_snapshot (cache) + pulse récent.
    """
    dashboard = service.get_full_dashboard(
        db, yacht_id=yacht_id, requester_id=current_user.id
    )
    if dashboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yacht introuvable ou accès refusé."
        )
    return dashboard


# ─────────────────────────────────────────────
# DAILY PULSE (candidat)
# ─────────────────────────────────────────────

@router.post(
    "/pulse",
    response_model=DailyPulseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Soumettre mon pulse du jour",
)
def submit_pulse(
    payload: DailyPulseIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Soumet l'humeur journalière du marin.
    Contraintes : assignation active requise, une seule soumission par jour.
    """
    try:
        return service.submit_daily_pulse(db, user=current_user, payload=payload)
    except ValueError as e:
        code = str(e)
        if code == "NO_ACTIVE_ASSIGNMENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous devez être assigné à un yacht actif."
            )
        if code == "ALREADY_SUBMITTED_TODAY":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Votre pulse a déjà été transmis aujourd'hui."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


@router.get(
    "/pulse/history",
    response_model=List[DailyPulseOut],
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Mon historique de pulses",
)
def get_pulse_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """30 derniers pulses du marin connecté."""
    return service.get_pulse_history(db, user_id=current_user.id)