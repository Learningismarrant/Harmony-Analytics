# modules/gateway/router.py
"""
Endpoints publics et semi-publics du système de liens Harmony.
Couvre : résolution universelle de tokens, embarquement yacht,
         vérification d'expériences par les capitaines (HTML).

Ce module est le seul à retourner des réponses HTML (vérification).
Tous les autres endpoints retournent du JSON.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
from app.modules.gateway.service import GatewayService
from app.modules.gateway.schemas import (
    TokenResolveOut,
    YachtJoinOut,
    YachtPublicInfoOut,
)

router = APIRouter(prefix="/gateway", tags=["Gateway"])
service = GatewayService()
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# RÉSOLUTION UNIVERSELLE DE TOKEN
# Point d'entrée unique pour tous les QR Codes Harmony
# ─────────────────────────────────────────────

@router.get(
    "/resolve/{token}",
    response_model=TokenResolveOut,
    summary="Identifier un QR Code Harmony",
    description=(
        "Résout n'importe quel token Harmony vers son entité cible. "
        "Retourne le type (yacht | campaign) et les infos associées. "
        "Le frontend route ensuite vers le bon écran."
    ),
)
def resolve_token(token: str, db: Session = Depends(get_db)):
    result = service.resolve_token(db, token=token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien invalide ou expiré."
        )
    return result


# ─────────────────────────────────────────────
# EMBARQUEMENT YACHT (QR Code boarding)
# ─────────────────────────────────────────────

@router.get(
    "/yacht/{token}",
    response_model=YachtPublicInfoOut,
    summary="Informations d'un yacht via son token d'embarquement",
)
def get_yacht_by_token(token: str, db: Session = Depends(get_db)):
    """
    Accessible sans authentification.
    Affiche les infos du yacht avant que le candidat confirme l'embarquement.
    """
    yacht = service.get_yacht_public_info(db, token=token)
    if not yacht:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien d'invitation invalide ou expiré."
        )
    return yacht


@router.post(
    "/yacht/{token}/join",
    response_model=YachtJoinOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Rejoindre un yacht via token d'embarquement",
)
def join_yacht(
    token: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Le candidat scanne le QR Code du yacht et confirme l'embarquement.
    Crée une CrewAssignment active.
    Déclenche le recalcul du vessel_snapshot en background.
    """
    try:
        return service.join_yacht(db, token=token, user_id=current_user.id)
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_ABOARD":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous êtes déjà dans cet équipage."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


# ─────────────────────────────────────────────
# TOKEN CAMPAIGN (candidature via lien)
# ─────────────────────────────────────────────

@router.post(
    "/campaign/{token}/apply",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate"]))],
    summary="Postuler à une campagne via token",
)
def apply_via_token(
    token: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.apply_to_campaign(db, token=token, user_id=current_user.id)
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_APPLIED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous avez déjà postulé à cette campagne."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


# ─────────────────────────────────────────────
# REFRESH TOKENS (client / admin)
# ─────────────────────────────────────────────

@router.post(
    "/yacht/{yacht_id}/token/refresh",
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Régénérer le boarding token d'un yacht",
)
def refresh_yacht_token(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """L'ancien token est immédiatement invalidé."""
    try:
        return service.refresh_yacht_token(
            db, yacht_id=yacht_id, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.post(
    "/campaign/{campaign_id}/token/refresh",
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Régénérer le token d'invitation d'une campagne",
)
def refresh_campaign_token(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.refresh_campaign_token(
            db, campaign_id=campaign_id, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# VÉRIFICATION D'EXPÉRIENCE (HTML — capitaines)
# ─────────────────────────────────────────────

@router.get(
    "/verify/{token}",
    response_class=HTMLResponse,
    summary="Page de vérification d'expérience (capitaine)",
    include_in_schema=False,
)
def get_verification_page(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
):
    """
    Page HTML envoyée par email au capitaine pour valider
    l'expérience déclarée par un candidat.
    """
    exp_data = service.get_experience_by_token(db, token=token)
    if not exp_data:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Lien invalide ou déjà utilisé."}
        )
    return templates.TemplateResponse(
        "verify_form.html",
        {
            "request": request,
            "candidate": exp_data["candidate_name"],
            "yacht": exp_data["yacht_name"],
        },
    )


@router.post(
    "/verify/{token}",
    response_class=HTMLResponse,
    summary="Soumettre la vérification d'expérience",
    include_in_schema=False,
)
def submit_verification(
    request: Request,
    token: str,
    comment: str = Form(None),
    db: Session = Depends(get_db),
):
    """
    Le capitaine valide (ou non) l'expérience.
    Le token est invalidé après usage (one-time use).
    """
    success = service.submit_experience_verification(
        db, token=token, comment=comment
    )
    if not success:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Lien expiré ou déjà utilisé."}
        )
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "status": "verified",
            "message": "Merci pour votre retour !",
        },
    )