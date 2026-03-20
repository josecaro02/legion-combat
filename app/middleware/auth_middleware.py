"""Authentication middleware."""
from functools import wraps
from typing import Optional

import jwt
from flask import g, jsonify, request

from app.config import get_config


def get_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]


def decode_token(token: str) -> dict:
    """Decode and validate JWT token."""
    config = get_config()
    return jwt.decode(
        token,
        config.JWT_SECRET_KEY,
        algorithms=[config.JWT_ALGORITHM]
    )


def jwt_required(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({
                'error': 'AUTHENTICATION_ERROR',
                'message': 'Authorization header missing or invalid'
            }), 401

        try:
            payload = decode_token(token)

            # Store user info in flask g
            g.user_id = payload.get('user_id')
            g.user_role = payload.get('role')
            g.token_type = payload.get('type')

            # Validate token type
            if g.token_type != 'access':
                return jsonify({
                    'error': 'AUTHENTICATION_ERROR',
                    'message': 'Invalid token type'
                }), 401

        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'AUTHENTICATION_ERROR',
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'error': 'AUTHENTICATION_ERROR',
                'message': f'Invalid token: {str(e)}'
            }), 401

        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> Optional[dict]:
    """Get current authenticated user info.

    Must be called within a request context with jwt_required.

    Returns:
        Dictionary with user_id and role, or None
    """
    return {
        'user_id': getattr(g, 'user_id', None),
        'role': getattr(g, 'user_role', None)
    } if hasattr(g, 'user_id') else None


def optional_auth(f):
    """Decorator to optionally authenticate (user info available if token present)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()

        if token:
            try:
                payload = decode_token(token)
                g.user_id = payload.get('user_id')
                g.user_role = payload.get('role')
                g.token_type = payload.get('type')
            except jwt.InvalidTokenError:
                pass  # Ignore invalid tokens for optional auth

        return f(*args, **kwargs)
    return decorated_function
