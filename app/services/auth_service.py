"""Authentication service."""
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.exceptions.custom_exceptions import AuthenticationError
from app.models.user import RefreshToken, User, UserRole
from app.repositories.user_repository import UserRepository
from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.utils.password_utils import verify_password


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """Authenticate user and create tokens.

        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Dictionary with access_token, refresh_token, token_type, expires_in

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")

        # Create tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, jti, expires = create_refresh_token(user.id)

        # Store refresh token
        self.user_repo.save_refresh_token(
            user_id=user.id,
            token=refresh_token,
            jti=jti,
            expires_at=expires,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': 900  # 15 minutes
        }

    def refresh(
        self,
        refresh_token_str: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> dict:
        """Refresh access token using refresh token.

        Implements token rotation and reuse detection.

        Args:
            refresh_token_str: The refresh token
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Dictionary with new tokens

        Raises:
            AuthenticationError: If token is invalid, expired, or reused
        """
        # Decode and validate token
        try:
            payload = decode_token(refresh_token_str)
        except Exception as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

        if payload.get('type') != 'refresh':
            raise AuthenticationError("Invalid token type")

        jti = payload.get('jti')
        user_id = payload.get('user_id')

        if not jti or not user_id:
            raise AuthenticationError("Invalid token payload")

        # Find stored token
        token_hash = hash_token(refresh_token_str)
        stored_token = self.user_repo.get_refresh_token_by_hash(token_hash)

        if not stored_token:
            raise AuthenticationError("Token not found")

        # Check if revoked
        if stored_token.is_revoked():
            raise AuthenticationError("Token revoked")

        # Check if expired
        if stored_token.is_expired():
            raise AuthenticationError("Token expired")

        # Reuse detection: if token has been replaced, it's a reuse attempt
        if stored_token.replaced_by_token_id:
            # Possible token theft! Revoke all user tokens
            self.user_repo.revoke_all_user_tokens(user_id)
            raise AuthenticationError("Token reuse detected. All tokens revoked.")

        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Generate new tokens
        new_access_token = create_access_token(user.id, user.role.value)
        new_refresh_token, new_jti, new_expires = create_refresh_token(user.id)

        # Store new refresh token
        new_stored = self.user_repo.save_refresh_token(
            user_id=user.id,
            token=new_refresh_token,
            jti=new_jti,
            expires_at=new_expires,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Mark old token as replaced
        self.user_repo.mark_refresh_token_replaced(stored_token.id, new_stored.id)

        return {
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'token_type': 'bearer',
            'expires_in': 900
        }

    def logout(self, user_id: str, token_jti: str) -> None:
        """Logout user by revoking refresh token.

        Args:
            user_id: User ID
            token_jti: Token JTI to revoke
        """
        stored_token = self.user_repo.get_refresh_token_by_jti(token_jti)
        if stored_token and str(stored_token.user_id) == user_id:
            self.user_repo.revoke_refresh_token(stored_token.id)

    def logout_all(self, user_id: str) -> int:
        """Logout user from all sessions.

        Args:
            user_id: User ID

        Returns:
            Number of revoked tokens
        """
        return self.user_repo.revoke_all_user_tokens(user_id)

    def validate_token(self, token: str) -> dict:
        """Validate an access token.

        Args:
            token: JWT token

        Returns:
            Token payload

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            payload = decode_token(token)
            if payload.get('type') != 'access':
                raise AuthenticationError("Invalid token type")
            return payload
        except Exception as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
