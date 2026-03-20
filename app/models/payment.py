import uuid
from datetime import date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.student import Student


class PaymentStatus(str, PyEnum):
    """Payment status options."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class Payment(Base, TimestampMixin):
    """Payment model for student fees."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"),
        index=True,
        nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    student: Mapped["Student"] = relationship(
        back_populates="payments"
    )

    # Composite indexes
    __table_args__ = (
        Index('ix_payments_student_due_date', 'student_id', 'due_date'),
        Index('ix_payments_status_due_date', 'status', 'due_date'),
    )

    def __repr__(self) -> str:
        return f"<Payment {self.amount} for student {self.student_id}>"

    def to_dict(self) -> dict:
        """Convert payment to dictionary."""
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'amount': str(self.amount),
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'due_date': self.due_date.isoformat(),
            'status': self.status.value,
            'idempotency_key': self.idempotency_key,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_overdue(self) -> bool:
        """Check if payment is overdue."""
        return self.status == PaymentStatus.PENDING and self.due_date < date.today()

    def mark_as_paid(self, payment_date: Optional[date] = None) -> None:
        """Mark payment as paid."""
        self.status = PaymentStatus.PAID
        self.payment_date = payment_date or date.today()
