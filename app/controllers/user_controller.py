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

    Request Body:
        - email: Professor email
        - password: Professor password (min 8 chars)
        - first_name: First name
        - last_name: Last name
        - role: Must be 'professor'

    Returns:
        - Created professor information
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

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)

    Returns:
        - items: List of professors
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
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

    Args:
        user_id: Professor ID

    Returns:
        - Professor information
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

    Args:
        user_id: Professor ID

    Request Body:
        - first_name: First name (optional)
        - last_name: Last name (optional)
        - is_active: Active status (optional)

    Returns:
        - Updated professor information
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

    Args:
        user_id: Professor ID

    Returns:
        - message: Success message
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

    Args:
        user_id: User ID

    Request Body:
        - new_password: New password (min 8 chars)

    Returns:
        - message: Success message
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
