"""Attendance repository."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.attendance import Attendance
from app.repositories.base_repository import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance operations."""

    def __init__(self):
        super().__init__(Attendance)

    def get_by_class_instance(self, class_instance_id: UUID) -> List[Attendance]:
        """Get attendances by class instance."""
        stmt = select(Attendance).where(
            Attendance.class_instance_id == class_instance_id
        )
        return list(db.session.execute(stmt).scalars().all())

    def get_by_student(
        self,
        student_id: UUID,
        since: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attendance]:
        """Get attendances by student."""
        stmt = select(Attendance).where(Attendance.student_id == student_id)
        if since:
            stmt = stmt.where(Attendance.check_in_time >= since)
        stmt = stmt.order_by(Attendance.check_in_time.desc())
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_class_and_student(
        self,
        class_instance_id: UUID,
        student_id: UUID
    ) -> Optional[Attendance]:
        """Get attendance by class and student."""
        stmt = select(Attendance).where(
            Attendance.class_instance_id == class_instance_id,
            Attendance.student_id == student_id
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def exists_for_class_and_student(
        self,
        class_instance_id: UUID,
        student_id: UUID
    ) -> bool:
        """Check if attendance exists for class and student."""
        stmt = select(Attendance).where(
            Attendance.class_instance_id == class_instance_id,
            Attendance.student_id == student_id
        )
        return db.session.execute(stmt).first() is not None

    def count_by_class_instance(self, class_instance_id: UUID) -> int:
        """Count attendances for a class instance."""
        stmt = select(func.count()).where(
            Attendance.class_instance_id == class_instance_id
        )
        return db.session.execute(stmt).scalar()

    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attendance]:
        """Get attendances in a date range."""
        from app.models.class_instance import ClassInstance
        stmt = select(Attendance).join(ClassInstance).where(
            ClassInstance.date >= start_date,
            ClassInstance.date <= end_date
        ).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_with_student(self, attendance_id: UUID) -> Optional[Attendance]:
        """Get attendance with student loaded."""
        stmt = select(Attendance).options(
            joinedload(Attendance.student)
        ).where(Attendance.id == attendance_id)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_daily_summary(self, target_date: date) -> List[dict]:
        """Get daily attendance summary."""
        from app.models.class_instance import ClassInstance
        stmt = select(
            ClassInstance.id,
            ClassInstance.start_time,
            ClassInstance.end_time,
            ClassInstance.course_type,
            func.count(Attendance.id).label('attendance_count')
        ).join(
            Attendance,
            Attendance.class_instance_id == ClassInstance.id,
            isouter=True
        ).where(
            ClassInstance.date == target_date
        ).group_by(
            ClassInstance.id,
            ClassInstance.start_time,
            ClassInstance.end_time,
            ClassInstance.course_type
        )
        return list(db.session.execute(stmt).mappings().all())

    def get_student_attendance_stats(
        self,
        student_id: UUID,
        months: int = 1
    ) -> dict:
        """Get attendance statistics for a student."""
        from app.models.class_instance import ClassInstance
        from dateutil.relativedelta import relativedelta

        since = datetime.utcnow() - relativedelta(months=months)

        stmt = select(
            func.count(Attendance.id).label('total_attendances')
        ).join(ClassInstance).where(
            Attendance.student_id == student_id,
            Attendance.check_in_time >= since
        )
        result = db.session.execute(stmt).scalar()

        return {
            'total_attendances': result or 0,
            'period_months': months
        }
