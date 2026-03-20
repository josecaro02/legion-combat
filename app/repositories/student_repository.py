"""Student repository."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.student import CourseType, Student
from app.repositories.base_repository import BaseRepository


class StudentRepository(BaseRepository[Student]):
    """Repository for Student operations."""

    def __init__(self):
        super().__init__(Student)

    def get_by_name(self, first_name: str, last_name: str) -> List[Student]:
        """Get students by name."""
        stmt = select(Student).where(
            Student.first_name.ilike(f"%{first_name}%"),
            Student.last_name.ilike(f"%{last_name}%")
        )
        return list(db.session.execute(stmt).scalars().all())

    def search_by_name(self, query: str) -> List[Student]:
        """Search students by name."""
        stmt = select(Student).where(
            (Student.first_name.ilike(f"%{query}%")) |
            (Student.last_name.ilike(f"%{query}%"))
        )
        return list(db.session.execute(stmt).scalars().all())

    def get_by_course(
        self,
        course: CourseType,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Student]:
        """Get students by course."""
        stmt = select(Student).where(Student.course == course)
        if is_active is not None:
            stmt = stmt.where(Student.is_active == is_active)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_active_students(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """Get active students."""
        stmt = select(Student).where(Student.is_active == True).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def count_by_course(self, course: Optional[CourseType] = None) -> int:
        """Count students by course."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Student)
        if course:
            stmt = stmt.where(Student.course == course)
        return db.session.execute(stmt).scalar()

    def get_with_payments(self, student_id: UUID) -> Optional[Student]:
        """Get student with payments loaded."""
        stmt = select(Student).options(
            joinedload(Student.payments)
        ).where(Student.id == student_id)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_with_attendances(self, student_id: UUID) -> Optional[Student]:
        """Get student with attendances loaded."""
        stmt = select(Student).options(
            joinedload(Student.attendances)
        ).where(Student.id == student_id)
        return db.session.execute(stmt).scalar_one_or_none()
