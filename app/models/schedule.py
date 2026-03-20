import uuid
from datetime import date, time
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin
from app.models.student import CourseType

if TYPE_CHECKING:
    from app.models.class_instance import ClassInstance


class DayOfWeek(int, PyEnum):
    """Days of the week for scheduling."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class ScheduleTemplate(Base, TimestampMixin):
    """Schedule template for recurring classes."""

    __tablename__ = "schedule_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek),
        index=True,
        nullable=False
    )
    start_time: Mapped[time] = mapped_column(
        nullable=False
    )
    end_time: Mapped[time] = mapped_column(
        nullable=False
    )
    course_type: Mapped[CourseType] = mapped_column(
        Enum(CourseType),
        nullable=False
    )
    max_capacity: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False
    )
    valid_from: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False
    )
    valid_to: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    replaced_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("schedule_templates.id"),
        nullable=True
    )
    professor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # Relationships
    class_instances: Mapped[List["ClassInstance"]] = relationship(
        back_populates="template",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<ScheduleTemplate {self.day_of_week.name} {self.start_time}-{self.end_time}>"

    def to_dict(self) -> dict:
        """Convert template to dictionary."""
        return {
            'id': str(self.id),
            'day_of_week': self.day_of_week.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'course_type': self.course_type.value,
            'max_capacity': self.max_capacity,
            'valid_from': self.valid_from.isoformat(),
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'is_active': self.is_active,
            'version': self.version,
            'replaced_by_id': str(self.replaced_by_id) if self.replaced_by_id else None,
            'professor_id': str(self.professor_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_valid_for_date(self, target_date: date) -> bool:
        """Check if template is valid for a specific date."""
        if not self.is_active:
            return False
        if target_date < self.valid_from:
            return False
        if self.valid_to and target_date > self.valid_to:
            return False
        return target_date.weekday() == self.day_of_week.value
