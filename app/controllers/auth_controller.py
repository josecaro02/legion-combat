"""Authentication controller."""
from flask import Blueprint, g, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RefreshRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
user_service = UserService()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens.

    Request Body:
        - email: User email
        - password: User password

    Returns:
        - access_token: JWT access token
        - refresh_token: JWT refresh token
        - token_type: Token type (bearer)
        - expires_in: Token expiration in seconds
    """
    data = request.get_json()

    try:
        login_data = LoginRequest(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        tokens = auth_service.login(
            email=login_data.email,
            password=login_data.password,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify(tokens), 200
    except Exception as e:
        return jsonify({
            'error': 'AUTHENTICATION_ERROR',
            'message': str(e)
        }), 401


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token.

    Implements token rotation - returns new access and refresh tokens.

    Request Body:
        - refresh_token: Valid refresh token

    Returns:
        - access_token: New JWT access token
        - refresh_token: New JWT refresh token
        - token_type: Token type (bearer)
        - expires_in: Token expiration in seconds
    """
    data = request.get_json()

    try:
        refresh_data = RefreshRequest(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        tokens = auth_service.refresh(
            refresh_token_str=refresh_data.refresh_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        return jsonify(tokens), 200
    except Exception as e:
        return jsonify({
            'error': 'AUTHENTICATION_ERROR',
            'message': str(e)
        }), 401


@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """Logout user by revoking refresh token.

    Requires authentication.

    Returns:
        - message: Success message
    """
    user_id = getattr(g, 'user_id', None)

    # Get refresh token from Authorization header (we need to revoke it)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            from app.utils.jwt_utils import decode_token
            payload = decode_token(token)
            jti = payload.get('jti')
            if jti:
                auth_service.logout(user_id, jti)
        except Exception:
            pass

    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/logout-all', methods=['POST'])
@jwt_required
def logout_all():
    """Logout user from all sessions.

    Requires authentication. Revokes all refresh tokens for the user.

    Returns:
        - message: Success message
        - revoked_count: Number of revoked tokens
    """
    user_id = getattr(g, 'user_id', None)

    try:
        count = auth_service.logout_all(user_id)
        return jsonify({
            'message': 'All sessions terminated',
            'revoked_count': count
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'AUTHENTICATION_ERROR',
            'message': str(e)
        }), 401


@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Get current authenticated user info.

    Requires authentication.

    Returns:
        - User information
    """
    user_id = getattr(g, 'user_id', None)

    try:
        user = user_service.get_user(user_id)
        return jsonify(UserResponse.model_validate(user).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@auth_bp.route('/me/password', methods=['PUT'])
@jwt_required
def change_password():
    """Change current user password.

    Requires authentication.

    Request Body:
        - old_password: Current password
        - new_password: New password (min 8 chars)

    Returns:
        - message: Success message
    """
    user_id = getattr(g, 'user_id', None)
    data = request.get_json()

    try:
        password_data = PasswordChangeRequest(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        user_service.change_password(
            user_id=user_id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
