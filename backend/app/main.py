# main.py
"""
Point d'entrée de l'API Harmony.
Enregistre tous les modules via leurs routers.

Architecture : modules verticaux quasi-autonomes + engine transversal.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.modules.auth.router        import router as auth_router
from app.modules.assessment.router  import router as assessment_router
from app.modules.identity.router    import router as identity_router
from app.modules.crew.router        import router as crew_router
from app.modules.vessel.router      import router as vessel_router
from app.modules.recruitment.router import router as recruitment_router
from app.modules.survey.router      import router as survey_router
from app.modules.gateway.router     import router as gateway_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(assessment_router)
app.include_router(identity_router)
app.include_router(crew_router)
app.include_router(vessel_router)
app.include_router(recruitment_router)
app.include_router(survey_router)
app.include_router(gateway_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}