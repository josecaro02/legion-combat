"""User controller."""
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_owner, require_roles
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

user_bp = Blueprint('users', __name__)
user_service = UserService()


@user_bp.route('/professors', methods=['POST'])
@jwt_required
@require_owner
def create_professor():
    """Create a new professor (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - first_name
            - last_name
          properties:
            email:
              type: string
              format: email
              example: "professor@gym.com"
            password:
              type: string
              minLength: 8
              example: "securepassword"
            first_name:
              type: string
              example: "Juan"
            last_name:
              type: string
              example: "Pérez"
    responses:
      201:
        description: Professor created successfully
        schema:
          type: object
          properties:
            id:
              type: string
              format: uuid
            email:
              type: string
            first_name:
              type: string
            last_name:
              type: string
            role:
              type: string
              example: "professor"
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden - Owner access required
    """
    data = request.get_json()

    try:
        user_data = UserCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    # Validate role is professor
    if user_data.role != UserRole.PROFESSOR.value:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'Can only create professors'
        }), 400

    try:
        user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        return jsonify(UserResponse.model_validate(user).model_dump()), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@user_bp.route('/professors', methods=['GET'])
@jwt_required
@require_owner
def list_professors():
    """List all professors (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Items per page
    responses:
      200:
        description: List of professors
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    format: uuid
                  email:
                    type: string
                  first_name:
                    type: string
                  last_name:
                    type: string
                  role:
                    type: string
                  is_active:
                    type: boolean
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
      403:
        description: Forbidden
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    try:
        result = user_service.list_users(
            role=UserRole.PROFESSOR.value,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [UserResponse.model_validate(u).model_dump() for u in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@user_bp.route('/professors/<uuid:user_id>', methods=['GET'])
@jwt_required
@require_owner
def get_professor(user_id: UUID):
    """Get professor by ID (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        format: uuid
        required: true
        description: Professor UUID
    responses:
      200:
        description: Professor information
        schema:
          type: object
          properties:
            id:
              type: string
              format: uuid
            email:
              type: string
            first_name:
              type: string
            last_name:
              type: string
            role:
              type: string
            is_active:
              type: boolean
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Professor not found
    """
    try:
        user = user_service.get_user(user_id)
        if user.role != UserRole.PROFESSOR:
            return jsonify({
                'error': 'NOT_FOUND',
                'message': 'Professor not found'
            }), 404
        return jsonify(UserResponse.model_validate(user).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@user_bp.route('/professors/<uuid:user_id>', methods=['PUT'])
@jwt_required
@require_owner
def update_professor(user_id: UUID):
    """Update professor (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        format: uuid
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            first_name:
              type: string
            last_name:
              type: string
            is_active:
              type: boolean
    responses:
      200:
        description: Professor updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Professor not found
    """
    data = request.get_json()

    try:
        user_data = UserUpdate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        user = user_service.update_user(
            user_id=user_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=user_data.is_active
        )
        return jsonify(UserResponse.model_validate(user).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@user_bp.route('/professors/<uuid:user_id>', methods=['DELETE'])
@jwt_required
@require_owner
def delete_professor(user_id: UUID):
    """Delete professor (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Professor deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Professor deleted successfully"
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Professor not found
    """
    try:
        user = user_service.get_user(user_id)
        if user.role != UserRole.PROFESSOR:
            return jsonify({
                'error': 'NOT_FOUND',
                'message': 'Professor not found'
            }), 404

        user_service.delete_user(user_id)
        return jsonify({'message': 'Professor deleted successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@user_bp.route('/<uuid:user_id>/reset-password', methods=['POST'])
@jwt_required
@require_owner
def reset_user_password(user_id: UUID):
    """Reset user password (owner only).
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        format: uuid
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - new_password
          properties:
            new_password:
              type: string
              minLength: 8
              description: New password (min 8 characters)
    responses:
      200:
        description: Password reset successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Password reset successfully"
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: User not found
    """
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password or len(new_password) < 8:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'Password must be at least 8 characters'
        }), 400

    try:
        user_service.reset_password(user_id, new_password)
        return jsonify({'message': 'Password reset successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
