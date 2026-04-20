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
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              description: User email
              example: "owner@gym.com"
            password:
              type: string
              description: User password
              example: "securepassword"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
              description: JWT access token
            refresh_token:
              type: string
              description: JWT refresh token
            token_type:
              type: string
              example: "bearer"
            expires_in:
              type: integer
              description: Token expiration in seconds
              example: 900
      401:
        description: Authentication failed
        schema:
          type: object
          properties:
            error:
              type: string
              example: "AUTHENTICATION_ERROR"
            message:
              type: string
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
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - refresh_token
          properties:
            refresh_token:
              type: string
              description: Valid refresh token
    responses:
      200:
        description: Token refresh successful
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
            token_type:
              type: string
            expires_in:
              type: integer
      401:
        description: Invalid or expired refresh token
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
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Logout successful
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Logged out successfully"
      401:
        description: Unauthorized
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
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: All sessions terminated
        schema:
          type: object
          properties:
            message:
              type: string
              example: "All sessions terminated"
            revoked_count:
              type: integer
              description: Number of revoked tokens
      401:
        description: Unauthorized
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
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: User information
        schema:
          type: object
          properties:
            id:
              type: string
              format: uuid
            email:
              type: string
              format: email
            first_name:
              type: string
            last_name:
              type: string
            role:
              type: string
              enum: [owner, professor]
            is_active:
              type: boolean
            created_at:
              type: string
              format: date-time
      401:
        description: Unauthorized
      404:
        description: User not found
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
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - old_password
            - new_password
          properties:
            old_password:
              type: string
              description: Current password
            new_password:
              type: string
              description: New password (min 8 characters)
    responses:
      200:
        description: Password updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Password updated successfully"
      400:
        description: Validation error
      401:
        description: Unauthorized
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
