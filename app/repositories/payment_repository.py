"""Payment repository."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.payment import Payment, PaymentStatus
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment operations."""

    def __init__(self):
        super().__init__(Payment)

    def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        """Get payment by idempotency key."""
        stmt = select(Payment).where(Payment.idempotency_key == key)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_by_student(
        self,
        student_id: UUID,
        status: Optional[PaymentStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """Get payments by student."""
        stmt = select(Payment).where(Payment.student_id == student_id)
        if status:
            stmt = stmt.where(Payment.status == status)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_by_status(
        self,
        status: PaymentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """Get payments by status."""
        stmt = select(Payment).where(Payment.status == status).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_overdue_payments(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get overdue payments."""
        today = date.today()
        stmt = select(Payment).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date < today
        ).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_upcoming_payments(self, days: int = 5, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get payments due in the next N days."""
        from datetime import timedelta
        today = date.today()
        target_date = today + timedelta(days=days)
        stmt = select(Payment).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date <= target_date,
            Payment.due_date >= today
        ).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def get_payments_due_before(self, target_date: date, status: PaymentStatus) -> List[Payment]:
        """Get payments due before a date with specific status."""
        stmt = select(Payment).where(
            Payment.status == status,
            Payment.due_date <= target_date
        )
        return list(db.session.execute(stmt).scalars().all())

    def get_with_student(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment with student loaded."""
        stmt = select(Payment).options(
            joinedload(Payment.student)
        ).where(Payment.id == payment_id)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_overdue_summary(self) -> List[dict]:
        """Get summary of overdue payments by student."""
        from sqlalchemy import func
        today = date.today()
        stmt = select(
            Payment.student_id,
            func.count(Payment.id).label('overdue_count'),
            func.sum(Payment.amount).label('total_owed')
        ).where(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date < today
        ).group_by(Payment.student_id)
        return list(db.session.execute(stmt).mappings().all())
