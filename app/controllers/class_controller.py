"""Class controller."""
from datetime import date, time
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_owner, require_professor
from app.schemas.class_instance import (
    ClassInstanceCreate,
    ClassInstanceResponse,
    ClassInstanceUpdate,
)
from app.services.class_service import ClassService

class_bp = Blueprint('classes', __name__)
class_service = ClassService()


@class_bp.route('/', methods=['GET'])
@jwt_required
@require_professor
def list_classes():
    """List class instances with optional filters.

    Query Parameters:
        - start_date: Start date filter (YYYY-MM-DD)
        - end_date: End date filter (YYYY-MM-DD)
        - course_type: Filter by course type
        - status: Filter by status
        - professor_id: Filter by professor
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)

    Returns:
        - items: List of class instances
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    course_type = request.args.get('course_type')
    status = request.args.get('status')
    professor_id = request.args.get('professor_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Parse dates
    if start_date:
        start_date = date.fromisoformat(start_date)
    if end_date:
        end_date = date.fromisoformat(end_date)
    if professor_id:
        professor_id = UUID(professor_id)

    try:
        result = class_service.list_instances(
            start_date=start_date,
            end_date=end_date,
            course_type=course_type,
            status=status,
            professor_id=professor_id,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [ClassInstanceResponse.model_validate(c).model_dump() for c in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@class_bp.route('/range', methods=['GET'])
@jwt_required
@require_professor
def get_classes_for_range():
    """Get or generate class instances for a date range.

    Query Parameters:
        - start_date: Start date (YYYY-MM-DD, required)
        - end_date: End date (YYYY-MM-DD, required)
        - course_type: Filter by course type (optional)

    Returns:
        - List of class instances
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    course_type = request.args.get('course_type')

    if not start_date or not end_date:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'start_date and end_date are required'
        }), 400

    try:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    except ValueError:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400

    try:
        instances = class_service.get_classes_for_date_range(
            start_date=start_date,
            end_date=end_date,
            course_type=course_type
        )
        return jsonify([ClassInstanceResponse.model_validate(c).model_dump() for c in instances]), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@class_bp.route('/', methods=['POST'])
@jwt_required
@require_owner
def create_instance():
    """Create a new class instance (owner only).

    Request Body:
        - date: Class date (YYYY-MM-DD)
        - start_time: Start time (HH:MM:SS)
        - end_time: End time (HH:MM:SS)
        - course_type: Course type
        - max_capacity: Maximum capacity
        - professor_id: Professor ID
        - template_id: Optional template ID
        - notes: Optional notes

    Returns:
        - Created class instance
    """
    data = request.get_json()

    try:
        class_data = ClassInstanceCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        instance = class_service.create_instance(
            date_obj=class_data.date,
            start_time=class_data.start_time,
            end_time=class_data.end_time,
            course_type=class_data.course_type,
            max_capacity=class_data.max_capacity,
            professor_id=class_data.professor_id,
            template_id=class_data.template_id,
            notes=class_data.notes
        )
        return jsonify(ClassInstanceResponse.model_validate(instance).model_dump()), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@class_bp.route('/<uuid:instance_id>', methods=['GET'])
@jwt_required
@require_professor
def get_instance(instance_id: UUID):
    """Get class instance by ID.

    Args:
        instance_id: Class instance ID

    Returns:
        - Class instance information
    """
    try:
        instance = class_service.get_instance(instance_id)
        return jsonify(ClassInstanceResponse.model_validate(instance).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@class_bp.route('/<uuid:instance_id>', methods=['PUT'])
@jwt_required
@require_owner
def update_instance(instance_id: UUID):
    """Update class instance (owner only).

    Args:
        instance_id: Class instance ID

    Request Body:
        - start_time: New start time (optional)
        - end_time: New end time (optional)
        - status: New status (optional)
        - max_capacity: New max capacity (optional)
        - professor_id: New professor ID (optional)
        - notes: New notes (optional)

    Returns:
        - Updated class instance
    """
    data = request.get_json()

    try:
        class_data = ClassInstanceUpdate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        instance = class_service.update_instance(
            instance_id=instance_id,
            start_time=class_data.start_time,
            end_time=class_data.end_time,
            status=class_data.status,
            max_capacity=class_data.max_capacity,
            professor_id=class_data.professor_id,
            notes=class_data.notes
        )
        return jsonify(ClassInstanceResponse.model_validate(instance).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@class_bp.route('/<uuid:instance_id>', methods=['DELETE'])
@jwt_required
@require_owner
def delete_instance(instance_id: UUID):
    """Delete class instance (owner only).

    Args:
        instance_id: Class instance ID

    Returns:
        - message: Success message
    """
    try:
        class_service.delete_instance(instance_id)
        return jsonify({'message': 'Class instance deleted successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@class_bp.route('/<uuid:instance_id>/cancel', methods=['POST'])
@jwt_required
@require_owner
def cancel_class(instance_id: UUID):
    """Cancel a class (owner only).

    Args:
        instance_id: Class instance ID

    Returns:
        - Updated class instance
    """
    try:
        instance = class_service.cancel_class(instance_id)
        return jsonify(ClassInstanceResponse.model_validate(instance).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@class_bp.route('/<uuid:instance_id>/complete', methods=['POST'])
@jwt_required
@require_professor
def complete_class(instance_id: UUID):
    """Mark class as completed.

    Args:
        instance_id: Class instance ID

    Returns:
        - Updated class instance
    """
    try:
        instance = class_service.complete_class(instance_id)
        return jsonify(ClassInstanceResponse.model_validate(instance).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@class_bp.route('/date/<date_str>', methods=['GET'])
@jwt_required
@require_professor
def get_classes_by_date(date_str: str):
    """Get classes for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        - List of class instances
    """
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid date format. Use YYYY-MM-DD'
        }), 400

    try:
        instances = class_service.get_classes_for_date_range(target_date, target_date)
        return jsonify([ClassInstanceResponse.model_validate(c).model_dump() for c in instances]), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
