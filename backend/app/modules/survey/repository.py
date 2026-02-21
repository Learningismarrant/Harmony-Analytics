# modules/survey/repository.py
"""
Accès DB pour les surveys et les réponses.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from app.models.survey import Survey, SurveyResponse


class SurveyRepository:

    def create_survey(self, db: Session, data: Dict) -> Survey:
        db_obj = Survey(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_survey(self, db: Session, survey_id: int) -> Optional[Survey]:
        return db.query(Survey).filter(Survey.id == survey_id).first()

    def get_pending_for_user(self, db: Session, user_id: int) -> List[Survey]:
        """
        Surveys ouverts qui ciblent cet utilisateur
        et auxquels il n'a pas encore répondu.
        """
        responded_ids = (
            db.query(SurveyResponse.survey_id)
            .filter(SurveyResponse.respondent_id == user_id)
            .subquery()
        )
        all_surveys = db.query(Survey).filter(Survey.is_open == True).all()
        return [
            s for s in all_surveys
            if user_id in (s.target_crew_ids or [])
            and s.id not in [r for (r,) in db.query(responded_ids).all()]
        ]

    def has_already_responded(
        self, db: Session, survey_id: int, respondent_id: int
    ) -> bool:
        return db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.respondent_id == respondent_id,
        ).first() is not None

    def create_response(self, db: Session, data: Dict) -> SurveyResponse:
        db_obj = SurveyResponse(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_responses_for_survey(
        self, db: Session, survey_id: int
    ) -> List[SurveyResponse]:
        return db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id
        ).all()

    def get_recent_responses(
        self, db: Session, yacht_id: int, limit: int = 20
    ) -> List[SurveyResponse]:
        return (
            db.query(SurveyResponse)
            .filter(SurveyResponse.yacht_id == yacht_id)
            .order_by(SurveyResponse.submitted_at.desc())
            .limit(limit)
            .all()
        )

    def get_yacht_survey_history(
        self, db: Session, yacht_id: int
    ) -> List[Survey]:
        return (
            db.query(Survey)
            .filter(Survey.yacht_id == yacht_id)
            .order_by(Survey.created_at.desc())
            .all()
        )

    def close_survey(self, db: Session, survey_id: int) -> None:
        survey = self.get_survey(db, survey_id)
        if survey:
            survey.is_open = False
            survey.closed_at = datetime.utcnow()
            db.commit()