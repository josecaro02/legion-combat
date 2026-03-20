"""Payment service."""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.exceptions.custom_exceptions import BusinessError, NotFoundError, ValidationError
from app.models.payment import Payment, PaymentStatus
from app.models.student import Student
from app.repositories.payment_repository import PaymentRepository
from app.repositories.student_repository import StudentRepository


class PaymentService:
    """Service for payment operations."""

    def __init__(
        self,
        payment_repo: Optional[PaymentRepository] = None,
        student_repo: Optional[StudentRepository] = None
    ):
        self.payment_repo = payment_repo or PaymentRepository()
        self.student_repo = student_repo or StudentRepository()

    def create_payment(
        self,
        student_id: UUID,
        amount: Decimal,
        due_date: date,
        idempotency_key: str,
        notes: Optional[str] = None
    ) -> Payment:
        """Create a new payment.

        Implements idempotency to prevent duplicate payments.

        Args:
            student_id: Student ID
            amount: Payment amount
            due_date: Due date
            idempotency_key: Unique key for idempotency
            notes: Optional notes

        Returns:
            Created or existing payment
        """
        # Check idempotency
        existing = self.payment_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        # Verify student exists
        student = self.student_repo.get_by_id(student_id)
        if not student:
            raise NotFoundError("Student")

        # Validate amount
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")

        payment = Payment(
            student_id=student_id,
            amount=amount,
            due_date=due_date,
            idempotency_key=idempotency_key,
            notes=notes,
            status=PaymentStatus.PENDING
        )
        return self.payment_repo.create(payment)

    def get_payment(self, payment_id: UUID) -> Payment:
        """Get payment by ID.

        Args:
            payment_id: Payment ID

        Returns:
            Payment
        """
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment")
        return payment

    def get_payment_with_student(self, payment_id: UUID) -> Payment:
        """Get payment with student info.

        Args:
            payment_id: Payment ID

        Returns:
            Payment with student loaded
        """
        payment = self.payment_repo.get_with_student(payment_id)
        if not payment:
            raise NotFoundError("Payment")
        return payment

    def list_payments(
        self,
        student_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """List payments with pagination.

        Args:
            student_id: Filter by student
            status: Filter by status
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        skip = (page - 1) * per_page

        if student_id:
            payments = self.payment_repo.get_by_student(
                student_id,
                PaymentStatus(status) if status else None,
                skip,
                per_page
            )
            total = len(payments)  # Approximate for student-specific
        elif status:
            payments = self.payment_repo.get_by_status(
                PaymentStatus(status),
                skip,
                per_page
            )
            total = len(payments)
        else:
            payments = self.payment_repo.get_all(skip, per_page)
            total = self.payment_repo.count()

        pages = (total + per_page - 1) // per_page

        return {
            'items': payments,
            'total': total,
            'pages': pages,
            'current_page': page
        }

    def get_student_payments(
        self,
        student_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """Get payments for a student.

        Args:
            student_id: Student ID
            status: Filter by status
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        return self.list_payments(student_id, status, page, per_page)

    def mark_as_paid(
        self,
        payment_id: UUID,
        payment_date: Optional[date] = None
    ) -> Payment:
        """Mark payment as paid.

        Args:
            payment_id: Payment ID
            payment_date: Optional payment date (defaults to today)

        Returns:
            Updated payment
        """
        payment = self.get_payment(payment_id)

        if payment.status == PaymentStatus.PAID:
            raise BusinessError("Payment is already marked as paid")

        payment.mark_as_paid(payment_date)
        return self.payment_repo.update(payment)

    def get_overdue_payments(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get overdue payments.

        Returns:
            List of overdue payments
        """
        return self.payment_repo.get_overdue_payments(skip, limit)

    def get_upcoming_payments(self, days: int = 5, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get payments due in the next N days.

        Args:
            days: Number of days to look ahead
            skip: Skip N records
            limit: Limit results

        Returns:
            List of upcoming payments
        """
        return self.payment_repo.get_upcoming_payments(days, skip, limit)

    def get_overdue_summary(self) -> List[dict]:
        """Get summary of overdue payments by student.

        Returns:
            List of dictionaries with student info and overdue amounts
        """
        summaries = self.payment_repo.get_overdue_summary()
        result = []
        for summary in summaries:
            student = self.student_repo.get_by_id(summary['student_id'])
            if student:
                result.append({
                    'student_id': str(student.id),
                    'student_name': student.full_name,
                    'phone': student.phone,
                    'overdue_count': summary['overdue_count'],
                    'total_owed': str(summary['total_owed'])
                })
        return result

    def update_payment(
        self,
        payment_id: UUID,
        amount: Optional[Decimal] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Update payment.

        Args:
            payment_id: Payment ID
            amount: New amount
            due_date: New due date
            notes: New notes

        Returns:
            Updated payment
        """
        payment = self.get_payment(payment_id)

        if payment.status == PaymentStatus.PAID:
            raise BusinessError("Cannot update a paid payment")

        if amount is not None:
            if amount <= 0:
                raise ValidationError("Amount must be greater than 0")
            payment.amount = amount
        if due_date is not None:
            payment.due_date = due_date
        if notes is not None:
            payment.notes = notes

        return self.payment_repo.update(payment)

    def delete_payment(self, payment_id: UUID) -> None:
        """Delete payment.

        Args:
            payment_id: Payment ID
        """
        payment = self.get_payment(payment_id)
        if payment.status == PaymentStatus.PAID:
            raise BusinessError("Cannot delete a paid payment")
        self.payment_repo.delete(payment)
