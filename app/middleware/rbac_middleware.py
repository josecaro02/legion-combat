"""Role-Based Access Control middleware."""
from functools import wraps
from uuid import UUID

from flask import g, jsonify

from app.models.user import UserRole


def require_roles(*allowed_roles):
    """Decorator to require specific roles.

    Args:
        *allowed_roles: Variable list of allowed role strings

    Usage:
        @require_roles('owner')
        @require_roles('owner', 'professor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = getattr(g, 'user_role', None)

            if not user_role:
                return jsonify({
                    'error': 'AUTHORIZATION_ERROR',
                    'message': 'Authentication required'
                }), 401

            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'AUTHORIZATION_ERROR',
                    'message': f'Insufficient permissions. Required: {", ".join(allowed_roles)}'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_owner(f):
    """Decorator to require owner role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = getattr(g, 'user_role', None)

        if not user_role:
            return jsonify({
                'error': 'AUTHORIZATION_ERROR',
                'message': 'Authentication required'
            }), 401

        if user_role != UserRole.OWNER.value:
            return jsonify({
                'error': 'AUTHORIZATION_ERROR',
                'message': 'Owner access required'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def require_professor(f):
    """Decorator to require professor or owner role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = getattr(g, 'user_role', None)

        if not user_role:
            return jsonify({
                'error': 'AUTHORIZATION_ERROR',
                'message': 'Authentication required'
            }), 401

        if user_role not in [UserRole.OWNER.value, UserRole.PROFESSOR.value]:
            return jsonify({
                'error': 'AUTHORIZATION_ERROR',
                'message': 'Professor or owner access required'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def is_owner() -> bool:
    """Check if current user is an owner."""
    return getattr(g, 'user_role', None) == UserRole.OWNER.value


def is_professor() -> bool:
    """Check if current user is a professor."""
    return getattr(g, 'user_role', None) == UserRole.PROFESSOR.value


def can_manage_user(target_user_id: str) -> bool:
    """Check if current user can manage target user.

    Owners can manage anyone, professors can only manage themselves.

    Args:
        target_user_id: Target user ID

    Returns:
        True if allowed, False otherwise
    """
    user_role = getattr(g, 'user_role', None)
    user_id = getattr(g, 'user_id', None)

    if user_role == UserRole.OWNER.value:
        return True

    if user_role == UserRole.PROFESSOR.value:
        return str(user_id) == str(target_user_id)

    return False


def can_create_professors() -> bool:
    """Check if current user can create professors."""
    return is_owner()


def can_manage_schedules() -> bool:
    """Check if current user can manage schedules."""
    return is_owner()


def can_view_all_payments() -> bool:
    """Check if current user can view all payments."""
    return is_owner() or is_professor()


def can_change_own_password_only(user_id: str) -> bool:
    """Check if professor can only change their own password.

    Args:
        user_id: Target user ID

    Returns:
        True if allowed, False otherwise
    """
    current_user_id = getattr(g, 'user_id', None)
    user_role = getattr(g, 'user_role', None)

    if user_role == UserRole.OWNER.value:
        return True

    if user_role == UserRole.PROFESSOR.value:
        return str(current_user_id) == str(user_id)

    return False
