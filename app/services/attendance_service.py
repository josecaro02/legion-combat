"""Attendance service."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from dateutil.relativedelta import relativedelta

from app.exceptions.custom_exceptions import BusinessError, NotFoundError, ValidationError
from app.models.attendance import Attendance
from app.models.class_instance import ClassInstance, ClassStatus
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.class_repository import ClassRepository
from app.repositories.student_repository import StudentRepository


class AttendanceService:
    """Service for attendance operations."""

    def __init__(
        self,
        attendance_repo: Optional[AttendanceRepository] = None,
        class_repo: Optional[ClassRepository] = None,
        student_repo: Optional[StudentRepository] = None
    ):
        self.attendance_repo = attendance_repo or AttendanceRepository()
        self.class_repo = class_repo or ClassRepository()
        self.student_repo = student_repo or StudentRepository()

    def register_attendance(
        self,
        class_instance_id: UUID,
        student_ids: List[UUID]
    ) -> List[Attendance]:
        """Register attendance for multiple students.

        Args:
            class_instance_id: Class instance ID
            student_ids: List of student IDs

        Returns:
            List of created attendances
        """
        # Get class instance
        class_instance = self.class_repo.get_by_id(class_instance_id)
        if not class_instance:
            raise NotFoundError("Class instance")

        # Check class status
        if class_instance.status == ClassStatus.CANCELLED:
            raise BusinessError("Cannot register attendance for cancelled class")

        if class_instance.status not in [ClassStatus.SCHEDULED, ClassStatus.IN_PROGRESS]:
            raise BusinessError("Class is not open for attendance")

        attendances = []
        for student_id in student_ids:
            # Check if student exists
            student = self.student_repo.get_by_id(student_id)
            if not student:
                raise NotFoundError(f"Student {student_id}")

            if not student.is_active:
                continue  # Skip inactive students

            # Check if already registered
            if self.attendance_repo.exists_for_class_and_student(
                class_instance_id, student_id
            ):
                continue  # Skip duplicates

            attendance = Attendance(
                class_instance_id=class_instance_id,
                student_id=student_id
            )
            attendances.append(self.attendance_repo.create(attendance))

        return attendances

    def remove_attendance(
        self,
        class_instance_id: UUID,
        student_id: UUID
    ) -> None:
        """Remove attendance for a student.

        Args:
            class_instance_id: Class instance ID
            student_id: Student ID
        """
        attendance = self.attendance_repo.get_by_class_and_student(
            class_instance_id, student_id
        )
        if not attendance:
            raise NotFoundError("Attendance record")

        self.attendance_repo.delete(attendance)

    def get_attendance(self, attendance_id: UUID) -> Attendance:
        """Get attendance by ID.

        Args:
            attendance_id: Attendance ID

        Returns:
            Attendance
        """
        attendance = self.attendance_repo.get_by_id(attendance_id)
        if not attendance:
            raise NotFoundError("Attendance")
        return attendance

    def get_class_attendances(self, class_instance_id: UUID) -> List[Attendance]:
        """Get all attendances for a class.

        Args:
            class_instance_id: Class instance ID

        Returns:
            List of attendances
        """
        return self.attendance_repo.get_by_class_instance(class_instance_id)

    def get_student_attendances(
        self,
        student_id: UUID,
        months: int = 1,
        page: int = 1,
        per_page: int = 50
    ) -> dict:
        """Get attendance history for a student.

        Args:
            student_id: Student ID
            months: Number of months to look back
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        # Validate student exists
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError("Student")

        if months not in [1, 2, 3]:
            raise ValidationError("Months must be 1, 2, or 3")

        skip = (page - 1) * per_page
        since = datetime.utcnow() - relativedelta(months=months)

        attendances = self.attendance_repo.get_by_student(student_id, since, skip, per_page)
        total = len(attendances)
        pages = (total + per_page - 1) // per_page

        return {
            'items': attendances,
            'total': total,
            'pages': pages,
            'current_page': page
        }

    def get_daily_attendance(self, target_date: date) -> List[dict]:
        """Get daily attendance summary.

        Args:
            target_date: Date to get summary for

        Returns:
            List of class summaries with attendance counts
        """
        summary = self.attendance_repo.get_daily_summary(target_date)
        result = []
        for item in summary:
            result.append({
                'class_id': str(item['id']),
                'time': f"{item['start_time']}-{item['end_time']}",
                'course': item['course_type'].value if hasattr(item['course_type'], 'value') else item['course_type'],
                'attendance_count': item['attendance_count']
            })
        return result

    def get_attendance_stats(
        self,
        student_id: UUID,
        months: int = 1
    ) -> dict:
        """Get attendance statistics for a student.

        Args:
            student_id: Student ID
            months: Number of months to analyze

        Returns:
            Dictionary with statistics
        """
        # Validate student exists
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError("Student")

        if months not in [1, 2, 3]:
            raise ValidationError("Months must be 1, 2, or 3")

        stats = self.attendance_repo.get_student_attendance_stats(student_id, months)
        return stats

    def is_student_attending(
        self,
        class_instance_id: UUID,
        student_id: UUID
    ) -> bool:
        """Check if a student is attending a class.

        Args:
            class_instance_id: Class instance ID
            student_id: Student ID

        Returns:
            True if attending, False otherwise
        """
        return self.attendance_repo.exists_for_class_and_student(
            class_instance_id, student_id
        )

    def get_class_attendance_count(self, class_instance_id: UUID) -> int:
        """Get attendance count for a class.

        Args:
            class_instance_id: Class instance ID

        Returns:
            Number of attendances
        """
        return self.attendance_repo.count_by_class_instance(class_instance_id)
