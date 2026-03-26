"""Student service."""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.exceptions.custom_exceptions import NotFoundError, ValidationError
from app.extensions import db
from app.models.payment import Payment, PaymentStatus
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

    def get_students_with_upcoming_payment_due(
        self,
        days: int = 5
    ) -> List[dict]:
        """Get active students whose last paid payment is approaching one month.

        This method finds students where the last payment (status='paid') was made
        and payment_date + 1 month falls within the next N days from today.

        Uses a subquery to get the latest payment per student efficiently,
        avoiding N+1 query problems.

        Args:
            days: Number of days to look ahead (default: 5)

        Returns:
            List of dictionaries with student, last_payment_date, and due_soon_date
        """
        from sqlalchemy import and_, text

        today = date.today()
        target_max = today + timedelta(days=days)
        
        # Subquery: Get the latest payment_date for each student with status='paid'
        # This is more efficient than querying payments separately for each student
        latest_payment_subq = (
            select(
                Payment.student_id.label('student_id'),
                func.max(Payment.payment_date).label('max_payment_date')
            )
            .where(
                Payment.status == PaymentStatus.PAID,
                Payment.payment_date.isnot(None)
            )
            .group_by(Payment.student_id)
            .subquery()
        )
        # Main query: Join students with their latest payment
        # Filter: today <= (payment_date + 1 month) <= today + days
        # We use PostgreSQL's date arithmetic: payment_date + INTERVAL '1 month'
        stmt = (
            select(
                Student,
                Payment.payment_date.label('last_payment_date')
            )
            .join(
                latest_payment_subq,
                Student.id == latest_payment_subq.c.student_id
            )
            .join(
                Payment,
                and_(
                    Payment.student_id == latest_payment_subq.c.student_id,
                    Payment.payment_date == latest_payment_subq.c.max_payment_date,
                    Payment.status == PaymentStatus.PAID
                )
            )
            .where(
                Student.is_active == True,
                # Calculate due_soon_date = payment_date + 1 month
                # Filter: today <= due_soon_date <= today + days
                text("(payment_date + INTERVAL '1 month') >= :today"),
                text("(payment_date + INTERVAL '1 month') <= :target_max")
            )
            .params(today=today, target_max=target_max)
            .order_by(text("payment_date + INTERVAL '1 month'"))  # Order by due_soon_date
        )

        results = db.session.execute(stmt).all()
        # Build response
        students_with_due_dates = []
        for student, last_payment_date in results:
            # Calculate due_soon_date (1 month after last payment)
            due_soon_date = self._add_months(last_payment_date, 1)

            students_with_due_dates.append({
                'student': student,
                'last_payment_date': last_payment_date,
                'due_soon_date': due_soon_date
            })
        return students_with_due_dates

    def _add_months(self, source_date: date, months: int) -> date:
        """Add months to a date, handling month-end correctly.

        For example, adding 1 month to January 31 gives February 28/29.

        Args:
            source_date: Original date
            months: Number of months to add

        Returns:
            New date with months added
        """
        import calendar

        year = source_date.year
        month = source_date.month + months

        # Handle year rollover
        while month > 12:
            month -= 12
            year += 1

        # Handle day overflow (e.g., Jan 31 -> Feb 28)
        last_day = calendar.monthrange(year, month)[1]
        day = min(source_date.day, last_day)

        return date(year, month, day)

    def get_students_with_upcoming_renewals(self, days: int = 5) -> List[dict]:
        """Get students whose last payment is approaching one month.

        This method finds active students whose last paid payment is about to
        complete one month, meaning they need to make a new payment soon.

        The logic:
        - For each active student, find their last payment with status='paid'
        - Calculate: due_soon_date = payment_date + 1 month
        - Filter: today <= due_soon_date <= today + days
        - Results ordered by due_soon_date (closest first)

        SQL Strategy (avoiding N+1 problem):
        - Uses a subquery to get the MAX(payment_date) per student
        - Joins the subquery with Student and Payment tables
        - All done in a single efficient database query

        Args:
            days: Number of days to look ahead (default: 5)

        Returns:
            List of dictionaries with student info and renewal dates
        """
        from sqlalchemy import func

        today = date.today()
        target_date = today + timedelta(days=days)

        # Subquery: Get the latest payment_date for each student
        # Only considers payments with status='paid' and non-null payment_date
        latest_payment_subq = (
            select(
                Payment.student_id,
                func.max(Payment.payment_date).label('last_payment_date')
            )
            .where(
                Payment.status == PaymentStatus.PAID,
                Payment.payment_date.is_not(None)
            )
            .group_by(Payment.student_id)
            .subquery()
        )

        # Main query: Join students with their latest payment
        # Filter by active students and date range
        # PostgreSQL: payment_date + interval '1 month' gives us the renewal date
        stmt = (
            select(
                Student,
                latest_payment_subq.c.last_payment_date,
                func.date_add(
                    latest_payment_subq.c.last_payment_date,
                    func.interval('1 month')
                ).label('due_soon_date')
            )
            .join(
                latest_payment_subq,
                Student.id == latest_payment_subq.c.student_id
            )
            .join(
                Payment,
                (Payment.student_id == Student.id) &
                (Payment.payment_date == latest_payment_subq.c.last_payment_date) &
                (Payment.status == PaymentStatus.PAID)
            )
            .where(
                Student.is_active == True,
                latest_payment_subq.c.last_payment_date.is_not(None)
            )
            .having(
                func.date_add(
                    latest_payment_subq.c.last_payment_date,
                    func.interval('1 month')
                ).between(today, target_date)
            )
            .order_by('due_soon_date')
        )

        results = db.session.execute(stmt).all()

        # Build response items
        items = []
        for row in results:
            student = row.Student
            last_payment_date = row.last_payment_date
            due_soon_date = row.due_soon_date

            items.append({
                'student': student,
                'last_payment_date': last_payment_date,
                'due_soon_date': due_soon_date
            })

        return items
