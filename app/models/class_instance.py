import uuid
from datetime import date, time
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text, Enum, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin
from app.models.student import CourseType

if TYPE_CHECKING:
    from app.models.schedule import ScheduleTemplate
    from app.models.user import User
    from app.models.attendance import Attendance


class ClassStatus(str, PyEnum):
    """Class instance status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ClassInstance(Base, TimestampMixin):
    """Class instance model for actual scheduled classes."""

    __tablename__ = "class_instances"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("schedule_templates.id"),
        nullable=True
    )
    date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )
    course_type: Mapped[CourseType] = mapped_column(
        Enum(CourseType),
        nullable=False
    )
    status: Mapped[ClassStatus] = mapped_column(
        Enum(ClassStatus),
        default=ClassStatus.SCHEDULED,
        nullable=False
    )
    max_capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    professor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    template: Mapped[Optional["ScheduleTemplate"]] = relationship(
        back_populates="class_instances"
    )
    professor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[professor_id],
        back_populates="classes"
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        back_populates="class_instance",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Indexes
    __table_args__ = (
        Index('ix_class_instances_date_status', 'date', 'status'),
        Index('ix_class_instances_professor_date', 'professor_id', 'date'),
        Index('ix_class_instances_course_date', 'course_type', 'date'),
    )

    def __repr__(self) -> str:
        return f"<ClassInstance {self.date} {self.start_time}-{self.end_time}>"

    def to_dict(self) -> dict:
        """Convert class instance to dictionary."""
        return {
            'id': str(self.id),
            'template_id': str(self.template_id) if self.template_id else None,
            'date': self.date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'course_type': self.course_type.value,
            'status': self.status.value,
            'max_capacity': self.max_capacity,
            'professor_id': str(self.professor_id),
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def current_attendance(self) -> int:
        """Get current attendance count."""
        return len(self.attendances) if self.attendances else 0

    def has_capacity(self) -> bool:
        """Check if class has available capacity."""
        return self.current_attendance < self.max_capacity
