# modules/gateway/router.py
"""
Endpoints publics et semi-publics du système de liens Harmony.
"""
from fastapi import APIRouter, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.shared.deps import DbDep, CrewDep, EmployerDep
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
# ─────────────────────────────────────────────

@router.get(
    "/resolve/{token}",
    response_model=TokenResolveOut,
    summary="Identifier un QR Code Harmony",
)
async def resolve_token(token: str, db: DbDep):
    result = await service.resolve_token(db, token=token)
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
async def get_yacht_by_token(token: str, db: DbDep):
    """Accessible sans authentification pour prévisualisation."""
    yacht = await service.get_yacht_public_info(db, token=token)
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
    summary="Rejoindre un yacht via token d'embarquement",
)
async def join_yacht(
    token: str,
    db: DbDep,
    crew: CrewDep, # Exige un profil marin
):
    try:
        return await service.join_yacht(db, token=token, user_id=crew.user_id)
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
    summary="Postuler à une campagne via token",
)
async def apply_via_token(
    token: str,
    db: DbDep,
    crew: CrewDep,
):
    try:
        return await service.apply_to_campaign(db, token=token, user_id=crew.user_id)
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_APPLIED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous avez déjà postulé à cette campagne."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


# ─────────────────────────────────────────────
# REFRESH TOKENS (réservé Employeurs / Admins)
# ─────────────────────────────────────────────

@router.post(
    "/yacht/{yacht_id}/token/refresh",
    summary="Régénérer le boarding token d'un yacht",
)
async def refresh_yacht_token(
    yacht_id: int,
    db: DbDep,
    employer: EmployerDep,
):
    try:
        return await service.refresh_yacht_token(
            db, yacht_id=yacht_id, requester_id=employer.user_id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.post(
    "/campaign/{campaign_id}/token/refresh",
    summary="Régénérer le token d'invitation d'une campagne",
)
async def refresh_campaign_token(
    campaign_id: int,
    db: DbDep,
    employer: EmployerDep,
):
    try:
        return await service.refresh_campaign_token(
            db, campaign_id=campaign_id, requester_id=employer.user_id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# VÉRIFICATION D'EXPÉRIENCE (HTML)
# ─────────────────────────────────────────────

@router.get(
    "/verify/{token}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def get_verification_page(
    request: Request,
    token: str,
    db: DbDep,
):
    exp_data = await service.get_experience_by_token(db, token=token)
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
async def submit_verification(
    request: Request,
    token: str,
    db: DbDep,              
    comment: str = Form(None), 
):
    """
    Le capitaine valide (ou non) l'expérience.
    Le token est invalidé après usage (one-time use).
    """
    success = await service.submit_experience_verification(
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