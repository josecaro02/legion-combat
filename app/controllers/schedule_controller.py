"""Schedule controller."""
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_owner, require_professor
from app.schemas.schedule import (
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
    ScheduleTemplateUpdate,
)
from app.services.schedule_service import ScheduleService

schedule_bp = Blueprint('schedules', __name__)
schedule_service = ScheduleService()


@schedule_bp.route('/templates', methods=['GET'])
@jwt_required
@require_professor
def list_templates():
    """List schedule templates.

    Query Parameters:
        - course_type: Filter by course type (optional)
        - is_active: Filter by active status (optional)

    Returns:
        - items: List of templates
        - total: Total count
    """
    course_type = request.args.get('course_type')
    is_active = request.args.get('is_active')

    if is_active is not None:
        is_active = is_active.lower() == 'true'

    try:
        templates = schedule_service.list_templates(
            course_type=course_type,
            is_active=is_active
        )
        return jsonify({
            'items': [ScheduleTemplateResponse.model_validate(t).model_dump() for t in templates],
            'total': len(templates)
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@schedule_bp.route('/templates', methods=['POST'])
@jwt_required
@require_owner
def create_template():
    """Create a new schedule template (owner only).

    Request Body:
        - day_of_week: Day of week (0-6, Monday-Sunday)
        - start_time: Start time (HH:MM:SS)
        - end_time: End time (HH:MM:SS)
        - course_type: Course type (boxing, kickboxing, both)
        - max_capacity: Maximum capacity (default: 20)
        - valid_from: Valid from date (YYYY-MM-DD)
        - professor_id: Professor ID

    Returns:
        - Created template information
    """
    data = request.get_json()

    try:
        template_data = ScheduleTemplateCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        from datetime import time as dt_time
        template = schedule_service.create_template(
            day_of_week=template_data.day_of_week,
            start_time=template_data.start_time if isinstance(template_data.start_time, dt_time) else dt_time.fromisoformat(str(template_data.start_time)),
            end_time=template_data.end_time if isinstance(template_data.end_time, dt_time) else dt_time.fromisoformat(str(template_data.end_time)),
            course_type=template_data.course_type,
            max_capacity=template_data.max_capacity,
            valid_from=template_data.valid_from,
            professor_id=template_data.professor_id
        )
        return jsonify(ScheduleTemplateResponse.model_validate(template).model_dump()), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@schedule_bp.route('/templates/<uuid:template_id>', methods=['GET'])
@jwt_required
@require_professor
def get_template(template_id: UUID):
    """Get schedule template by ID.

    Args:
        template_id: Template ID

    Returns:
        - Template information
    """
    try:
        template = schedule_service.get_template(template_id)
        return jsonify(ScheduleTemplateResponse.model_validate(template).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@schedule_bp.route('/templates/<uuid:template_id>', methods=['PUT'])
@jwt_required
@require_owner
def update_template(template_id: UUID):
    """Update schedule template (owner only).

    Args:
        template_id: Template ID

    Request Body:
        - day_of_week: New day of week (optional)
        - start_time: New start time (optional)
        - end_time: New end time (optional)
        - course_type: New course type (optional)
        - max_capacity: New max capacity (optional)
        - is_active: New active status (optional)

    Returns:
        - Updated template information
    """
    data = request.get_json()

    try:
        template_data = ScheduleTemplateUpdate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        from datetime import time as dt_time
        start_time = None
        end_time = None
        if template_data.start_time:
            start_time = template_data.start_time if isinstance(template_data.start_time, dt_time) else dt_time.fromisoformat(str(template_data.start_time))
        if template_data.end_time:
            end_time = template_data.end_time if isinstance(template_data.end_time, dt_time) else dt_time.fromisoformat(str(template_data.end_time))

        template = schedule_service.update_template(
            template_id=template_id,
            day_of_week=template_data.day_of_week,
            start_time=start_time,
            end_time=end_time,
            course_type=template_data.course_type,
            max_capacity=template_data.max_capacity,
            is_active=template_data.is_active
        )
        return jsonify(ScheduleTemplateResponse.model_validate(template).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@schedule_bp.route('/templates/<uuid:template_id>', methods=['DELETE'])
@jwt_required
@require_owner
def delete_template(template_id: UUID):
    """Delete schedule template (owner only - soft delete).

    Args:
        template_id: Template ID

    Returns:
        - message: Success message
    """
    try:
        schedule_service.delete_template(template_id)
        return jsonify({'message': 'Template deleted successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@schedule_bp.route('/templates/by-day/<int:day>', methods=['GET'])
@jwt_required
@require_professor
def get_templates_by_day(day: int):
    """Get templates by day of week.

    Args:
        day: Day of week (0-6, Monday-Sunday)

    Returns:
        - List of templates
    """
    try:
        templates = schedule_service.get_templates_by_day(day)
        return jsonify([ScheduleTemplateResponse.model_validate(t).model_dump() for t in templates]), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
