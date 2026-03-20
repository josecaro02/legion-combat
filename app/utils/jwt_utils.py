"""JWT utility functions."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt
from flask import current_app


def create_access_token(user_id: str, role: str) -> str:
    """Create a JWT access token.

    Args:
        user_id: The user's ID
        role: The user's role

    Returns:
        Encoded JWT access token
    """
    now = datetime.now(timezone.utc)
    expires = now + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(minutes=15))

    payload = {
        'user_id': str(user_id),
        'role': str(role),
        'type': 'access',
        'iat': now,
        'exp': expires,
    }

    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
    )


def create_refresh_token(user_id: str) -> Tuple[str, str, datetime]:
    """Create a JWT refresh token.

    Args:
        user_id: The user's ID

    Returns:
        Tuple of (token, jti, expiration_datetime)
    """
    now = datetime.now(timezone.utc)
    expires = now + current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=7))
    jti = str(uuid.uuid4())

    payload = {
        'user_id': str(user_id),
        'type': 'refresh',
        'jti': jti,
        'iat': now,
        'exp': expires,
    }

    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config.get('JWT_ALGORITHM', 'HS256')
    )

    return token, jti, expires


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(
        token,
        current_app.config['JWT_SECRET_KEY'],
        algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
    )


def hash_token(token: str) -> str:
    """Hash a token using SHA-256.

    Args:
        token: The token to hash

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Verify a token against a hash.

    Args:
        token: The token to verify
        token_hash: The expected hash

    Returns:
        True if token matches hash, False otherwise
    """
    return hash_token(token) == token_hash


def get_token_jti(token: str) -> Optional[str]:
    """Extract JTI from a token without verification.

    Args:
        token: The JWT token

    Returns:
        The JTI if present, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload.get('jti')
    except jwt.InvalidTokenError:
        return None


def get_token_expiration(token: str) -> Optional[datetime]:
    """Get token expiration without verification.

    Args:
        token: The JWT token

    Returns:
        Expiration datetime if present, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        exp = payload.get('exp')
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except jwt.InvalidTokenError:
        return None
