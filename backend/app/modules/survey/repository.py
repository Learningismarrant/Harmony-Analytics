# modules/survey/repository.py
"""
Accès DB pour les surveys et réponses.

Changements v2 :
- SurveyResponse.crew_profile_id (était respondent_id)
- Survey.triggered_by_id → EmployerProfile FK (était user_id)
- target_crew_ids → liste de crew_profile_ids
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from datetime import datetime, timezone

from app.shared.models import Survey, SurveyResponse


class SurveyRepository:

    async def create_survey(self, db: AsyncSession, data: Dict) -> Survey:
        db_obj = Survey(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_survey(self, db: AsyncSession, survey_id: int) -> Optional[Survey]:
        r = await db.execute(select(Survey).where(Survey.id == survey_id))
        return r.scalar_one_or_none()

    async def get_pending_for_crew(
        self, db: AsyncSession, crew_profile_id: int   # v2
    ) -> List[Survey]:
        """
        Surveys ouverts ciblant ce crew_profile_id et sans réponse de sa part.
        v2 : target_crew_ids contient des crew_profile_ids.
        """
        r = await db.execute(
            select(SurveyResponse.survey_id)
            .where(SurveyResponse.crew_profile_id == crew_profile_id)
        )
        already_responded_ids = set(r.scalars().all())

        r = await db.execute(select(Survey).where(Survey.is_open == True))
        all_surveys = r.scalars().all()

        return [
            s for s in all_surveys
            if crew_profile_id in (s.target_crew_ids or [])
            and s.id not in already_responded_ids
        ]

    async def has_already_responded(
        self, db: AsyncSession, survey_id: int, crew_profile_id: int  # v2
    ) -> bool:
        r = await db.execute(
            select(SurveyResponse).where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.crew_profile_id == crew_profile_id,
            )
        )
        return r.scalar_one_or_none() is not None

    async def create_response(self, db: AsyncSession, data: Dict) -> SurveyResponse:
        db_obj = SurveyResponse(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_responses_for_survey(
        self, db: AsyncSession, survey_id: int
    ) -> List[SurveyResponse]:
        r = await db.execute(
            select(SurveyResponse).where(SurveyResponse.survey_id == survey_id)
        )
        return r.scalars().all()

    async def get_recent_responses(
        self, db: AsyncSession, yacht_id: int, limit: int = 20
    ) -> List[SurveyResponse]:
        r = await db.execute(
            select(SurveyResponse)
            .where(SurveyResponse.yacht_id == yacht_id)
            .order_by(SurveyResponse.submitted_at.desc())
            .limit(limit)
        )
        return r.scalars().all()

    async def get_yacht_survey_history(
        self, db: AsyncSession, yacht_id: int
    ) -> List[Survey]:
        r = await db.execute(
            select(Survey)
            .where(Survey.yacht_id == yacht_id)
            .order_by(Survey.created_at.desc())
        )
        return r.scalars().all()

    async def close_survey(self, db: AsyncSession, survey_id: int) -> None:
        survey = await self.get_survey(db, survey_id)
        if survey:
            survey.is_open = False
            survey.closed_at = datetime.now(timezone.utc)
            await db.commit()