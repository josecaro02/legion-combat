"""Schedule repository."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select

from app.extensions import db
from app.models.schedule import DayOfWeek, ScheduleTemplate
from app.repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository[ScheduleTemplate]):
    """Repository for Schedule operations."""

    def __init__(self):
        super().__init__(ScheduleTemplate)

    def get_active_templates(
        self,
        target_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScheduleTemplate]:
        """Get active schedule templates."""
        stmt = select(ScheduleTemplate).where(ScheduleTemplate.is_active == True)
        if target_date:
            stmt = stmt.where(
                ScheduleTemplate.valid_from <= target_date,
                (ScheduleTemplate.valid_to.is_(None)) | (ScheduleTemplate.valid_to >= target_date)
            )
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_day_of_week(
        self,
        day: DayOfWeek,
        target_date: Optional[date] = None
    ) -> List[ScheduleTemplate]:
        """Get templates by day of week."""
        stmt = select(ScheduleTemplate).where(
            ScheduleTemplate.day_of_week == day,
            ScheduleTemplate.is_active == True
        )
        if target_date:
            stmt = stmt.where(
                ScheduleTemplate.valid_from <= target_date,
                (ScheduleTemplate.valid_to.is_(None)) | (ScheduleTemplate.valid_to >= target_date)
            )
        return list(db.session.execute(stmt).scalars().all())

    def get_by_course_type(
        self,
        course_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScheduleTemplate]:
        """Get templates by course type."""
        stmt = select(ScheduleTemplate).where(
            ScheduleTemplate.course_type == course_type
        ).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_professor(
        self,
        professor_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScheduleTemplate]:
        """Get templates by professor."""
        stmt = select(ScheduleTemplate).where(
            ScheduleTemplate.professor_id == professor_id
        ).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_valid_for_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[ScheduleTemplate]:
        """Get templates valid for a date range."""
        stmt = select(ScheduleTemplate).where(
            ScheduleTemplate.is_active == True,
            ScheduleTemplate.valid_from <= end_date,
            (ScheduleTemplate.valid_to.is_(None)) | (ScheduleTemplate.valid_to >= start_date)
        )
        return list(db.session.execute(stmt).scalars().all())
