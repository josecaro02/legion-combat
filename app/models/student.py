import uuid
from datetime import date
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.attendance import Attendance


class CourseType(str, PyEnum):
    """Types of courses available."""
    BOXING = "boxing"
    KICKBOXING = "kickboxing"
    BOTH = "both"


class Student(Base, TimestampMixin):
    """Student model for gym members."""

    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    course: Mapped[CourseType] = mapped_column(
        Enum(CourseType),
        nullable=False
    )
    enrollment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Student {self.first_name} {self.last_name}>"

    def to_dict(self) -> dict:
        """Convert student to dictionary."""
        return {
            'id': str(self.id),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address': self.address,
            'phone': self.phone,
            'course': self.course.value,
            'enrollment_date': self.enrollment_date.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def full_name(self) -> str:
        """Return full name of student."""
        return f"{self.first_name} {self.last_name}"
