import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.class_instance import ClassInstance


class UserRole(str, PyEnum):
    """User roles for RBAC."""
    OWNER = "owner"
    PROFESSOR = "professor"


class User(Base, TimestampMixin):
    """User model for owners and professors."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    classes: Mapped[List["ClassInstance"]] = relationship(
        back_populates="professor",
        foreign_keys="ClassInstance.professor_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class RefreshToken(Base, TimestampMixin):
    """Refresh token model for JWT token rotation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    jti: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    replaced_by_token_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("refresh_tokens.id"),
        nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens"
    )

    def __repr__(self) -> str:
        return f"<RefreshToken {self.jti} for user {self.user_id}>"

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() > self.expires_at

    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked_at is not None

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired() and not self.is_revoked()
