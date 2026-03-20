import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.class_instance import ClassInstance
    from app.models.student import Student


class Attendance(Base, TimestampMixin):
    """Attendance model for tracking student attendance."""

    __tablename__ = "attendances"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    class_instance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("class_instances.id"),
        index=True,
        nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"),
        index=True,
        nullable=False
    )
    check_in_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(
        nullable=True
    )

    # Relationships
    class_instance: Mapped["ClassInstance"] = relationship(
        back_populates="attendances"
    )
    student: Mapped["Student"] = relationship(
        back_populates="attendances"
    )

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint(
            'class_instance_id',
            'student_id',
            name='uq_attendance_class_student'
        ),
        Index('ix_attendances_student_checkin', 'student_id', 'check_in_time'),
    )

    def __repr__(self) -> str:
        return f"<Attendance student={self.student_id} class={self.class_instance_id}>"

    def to_dict(self) -> dict:
        """Convert attendance to dictionary."""
        return {
            'id': str(self.id),
            'class_instance_id': str(self.class_instance_id),
            'student_id': str(self.student_id),
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_with_student(self) -> dict:
        """Convert attendance to dictionary with student info."""
        base = self.to_dict()
        if self.student:
            base['student_name'] = self.student.full_name
        return base
