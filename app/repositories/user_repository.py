"""User repository."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions import db
from app.models.user import RefreshToken, User
from app.repositories.base_repository import BaseRepository
from app.utils.jwt_utils import hash_token


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role."""
        stmt = select(User).where(User.role == role).offset(skip).limit(limit)
        return list(db.session.execute(stmt).scalars().all())

    def count_by_role(self, role: str) -> int:
        """Count users by role."""
        from sqlalchemy import func
        stmt = select(func.count()).where(User.role == role)
        return db.session.execute(stmt).scalar()

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        stmt = select(User).where(User.email == email)
        return db.session.execute(stmt).first() is not None

    # Refresh Token operations
    def save_refresh_token(
        self,
        user_id: UUID,
        token: str,
        jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Save a refresh token."""
        token_hash = hash_token(token)
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(refresh_token)
        db.session.commit()
        db.session.refresh(refresh_token)
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return db.session.execute(stmt).scalar_one_or_none()

    def get_refresh_token_by_jti(self, jti: str) -> Optional[RefreshToken]:
        """Get refresh token by JTI."""
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return db.session.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, token_id: UUID) -> None:
        """Revoke a refresh token."""
        token = db.session.get(RefreshToken, token_id)
        if token:
            token.revoked_at = datetime.utcnow()
            db.session.commit()

    def mark_refresh_token_replaced(self, token_id: UUID, new_token_id: UUID) -> None:
        """Mark a refresh token as replaced."""
        token = db.session.get(RefreshToken, token_id)
        if token:
            token.replaced_by_token_id = new_token_id
            db.session.commit()

    def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user. Returns count of revoked tokens."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        )
        tokens = db.session.execute(stmt).scalars().all()
        now = datetime.utcnow()
        for token in tokens:
            token.revoked_at = now
        db.session.commit()
        return len(tokens)

    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens. Returns count of deleted tokens."""
        from sqlalchemy import delete
        now = datetime.utcnow()
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount
