"""Payment schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    """Payment creation schema."""
    student_id: UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    due_date: date
    idempotency_key: str = Field(..., min_length=10, max_length=64)
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    """Payment update schema."""
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    amount: Decimal
    status: str
    payment_date: Optional[date]
    due_date: date
    notes: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle Decimal."""
        data = {
            'id': obj.id,
            'student_id': obj.student_id,
            'amount': obj.amount,
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'payment_date': obj.payment_date,
            'due_date': obj.due_date,
            'notes': obj.notes,
            'created_at': obj.created_at,
        }
        return cls(**data)


class PaymentListResponse(BaseModel):
    """Payment list response schema."""
    items: List[PaymentResponse]
    total: int
    pages: int
    current_page: int


class PaymentWithStudentResponse(PaymentResponse):
    """Payment with student info response."""
    student_name: str


class OverduePaymentSummary(BaseModel):
    """Overdue payment summary."""
    student_id: UUID
    student_name: str
    phone: Optional[str]
    overdue_count: int
    total_owed: Decimal
