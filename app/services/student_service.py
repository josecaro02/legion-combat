"""Student service."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from app.exceptions.custom_exceptions import NotFoundError, ValidationError
from app.models.student import CourseType, Student
from app.repositories.student_repository import StudentRepository


class StudentService:
    """Service for student operations."""

    def __init__(self, student_repo: Optional[StudentRepository] = None):
        self.student_repo = student_repo or StudentRepository()

    def create_student(
        self,
        first_name: str,
        last_name: str,
        course: str,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        enrollment_date: Optional[date] = None
    ) -> Student:
        """Create a new student.

        Args:
            first_name: First name
            last_name: Last name
            course: Course type (boxing, kickboxing, both)
            address: Optional address
            phone: Optional phone
            enrollment_date: Optional enrollment date (defaults to today)

        Returns:
            Created student
        """
        # Validate course type
        try:
            course_type = CourseType(course)
        except ValueError:
            raise ValidationError(f"Invalid course type: {course}")

        student = Student(
            first_name=first_name,
            last_name=last_name,
            course=course_type,
            address=address,
            phone=phone,
            enrollment_date=enrollment_date or date.today()
        )
        return self.student_repo.create(student)

    def get_student(self, student_id: UUID) -> Student:
        """Get student by ID.

        Args:
            student_id: Student ID

        Returns:
            Student

        Raises:
            NotFoundError: If student not found
        """
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError("Student")
        return student

    def get_student_with_payments(self, student_id: UUID) -> Student:
        """Get student with payments.

        Args:
            student_id: Student ID

        Returns:
            Student with payments loaded
        """
        student = self.student_repo.get_with_payments(student_id)
        if not student:
            raise NotFoundError("Student")
        return student

    def list_students(
        self,
        course: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """List students with pagination.

        Args:
            course: Filter by course type
            is_active: Filter by active status
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        skip = (page - 1) * per_page

        if course:
            try:
                course_type = CourseType(course)
            except ValueError:
                raise ValidationError(f"Invalid course type: {course}")
            students = self.student_repo.get_by_course(course_type, is_active, skip, per_page)
            total = self.student_repo.count_by_course(course_type)
        else:
            if is_active is not None:
                students = self.student_repo.get_active_students(skip, per_page)
            else:
                students = self.student_repo.get_all(skip, per_page)
            total = self.student_repo.count()

        pages = (total + per_page - 1) // per_page

        return {
            'items': students,
            'total': total,
            'pages': pages,
            'current_page': page
        }

    def search_students(self, query: str) -> List[Student]:
        """Search students by name.

        Args:
            query: Search query

        Returns:
            List of matching students
        """
        return self.student_repo.search_by_name(query)

    def update_student(
        self,
        student_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        course: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Student:
        """Update student.

        Args:
            student_id: Student ID
            first_name: New first name
            last_name: New last name
            address: New address
            phone: New phone
            course: New course type
            is_active: New active status

        Returns:
            Updated student
        """
        student = self.get_student(student_id)

        if first_name is not None:
            student.first_name = first_name
        if last_name is not None:
            student.last_name = last_name
        if address is not None:
            student.address = address
        if phone is not None:
            student.phone = phone
        if course is not None:
            try:
                student.course = CourseType(course)
            except ValueError:
                raise ValidationError(f"Invalid course type: {course}")
        if is_active is not None:
            student.is_active = is_active

        return self.student_repo.update(student)

    def deactivate_student(self, student_id: UUID) -> Student:
        """Deactivate a student.

        Args:
            student_id: Student ID

        Returns:
            Deactivated student
        """
        return self.update_student(student_id, is_active=False)

    def activate_student(self, student_id: UUID) -> Student:
        """Activate a student.

        Args:
            student_id: Student ID

        Returns:
            Activated student
        """
        return self.update_student(student_id, is_active=True)

    def delete_student(self, student_id: UUID) -> None:
        """Delete student.

        Args:
            student_id: Student ID
        """
        student = self.get_student(student_id)
        self.student_repo.delete(student)
