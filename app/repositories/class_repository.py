"""Class instance repository."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.class_instance import ClassInstance, ClassStatus
from app.models.student import CourseType
from app.repositories.base_repository import BaseRepository


class ClassRepository(BaseRepository[ClassInstance]):
    """Repository for ClassInstance operations."""

    def __init__(self):
        super().__init__(ClassInstance)

    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        course_type: Optional[CourseType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassInstance]:
        """Get classes in a date range."""
        stmt = select(ClassInstance).where(
            ClassInstance.date >= start_date,
            ClassInstance.date <= end_date
        )
        if course_type:
            stmt = stmt.where(ClassInstance.course_type == course_type)
        stmt = stmt.order_by(ClassInstance.date, ClassInstance.start_time)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_date(self, target_date: date) -> List[ClassInstance]:
        """Get classes for a specific date."""
        stmt = select(ClassInstance).where(
            ClassInstance.date == target_date
        ).order_by(ClassInstance.start_time)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_template_and_date(
        self,
        template_id: UUID,
        target_date: date
    ) -> Optional[ClassInstance]:
        """Get class instance by template and date."""
        stmt = select(ClassInstance).where(
            ClassInstance.template_id == template_id,
            ClassInstance.date == target_date
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def get_by_professor(
        self,
        professor_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassInstance]:
        """Get classes by professor."""
        stmt = select(ClassInstance).where(
            ClassInstance.professor_id == professor_id
        )
        if start_date:
            stmt = stmt.where(ClassInstance.date >= start_date)
        if end_date:
            stmt = stmt.where(ClassInstance.date <= end_date)
        stmt = stmt.order_by(ClassInstance.date, ClassInstance.start_time)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_status(
        self,
        status: ClassStatus,
        start_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClassInstance]:
        """Get classes by status."""
        stmt = select(ClassInstance).where(ClassInstance.status == status)
        if start_date:
            stmt = stmt.where(ClassInstance.date >= start_date)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_with_attendances(self, class_id: UUID) -> Optional[ClassInstance]:
        """Get class with attendances loaded."""
        stmt = select(ClassInstance).options(
            joinedload(ClassInstance.attendances)
        ).where(ClassInstance.id == class_id)
        return db.session.execute(stmt).scalar_one_or_none()

    def exists_for_template_and_date(self, template_id: UUID, target_date: date) -> bool:
        """Check if class instance exists for template and date."""
        stmt = select(ClassInstance).where(
            ClassInstance.template_id == template_id,
            ClassInstance.date == target_date
        )
        return db.session.execute(stmt).first() is not None
