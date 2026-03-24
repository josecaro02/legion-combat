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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: course_type
        in: query
        type: string
        enum: [boxing, kickboxing, both]
        description: Filter by course type
      - name: is_active
        in: query
        type: boolean
        description: Filter by active status
    responses:
      200:
        description: List of schedule templates
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
                  day_of_week:
                    type: integer
                    description: 0=Monday, 6=Sunday
                  start_time:
                    type: string
                    example: "18:00:00"
                  end_time:
                    type: string
                  course_type:
                    type: string
                  max_capacity:
                    type: integer
                  is_active:
                    type: boolean
            total:
              type: integer
      401:
        description: Unauthorized
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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - day_of_week
            - start_time
            - end_time
            - course_type
            - professor_id
          properties:
            day_of_week:
              type: integer
              description: 0=Monday, 6=Sunday
              example: 0
            start_time:
              type: string
              description: HH:MM:SS
              example: "18:00:00"
            end_time:
              type: string
              example: "19:00:00"
            course_type:
              type: string
              enum: [boxing, kickboxing, both]
            max_capacity:
              type: integer
              default: 20
            valid_from:
              type: string
              format: date
            professor_id:
              type: string
              format: uuid
    responses:
      201:
        description: Template created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: template_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Template information
        schema:
          type: object
          properties:
            id:
              type: string
            day_of_week:
              type: integer
            start_time:
              type: string
            end_time:
              type: string
            course_type:
              type: string
            max_capacity:
              type: integer
            is_active:
              type: boolean
      401:
        description: Unauthorized
      404:
        description: Template not found
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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: template_id
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
            day_of_week:
              type: integer
            start_time:
              type: string
            end_time:
              type: string
            course_type:
              type: string
            max_capacity:
              type: integer
            is_active:
              type: boolean
    responses:
      200:
        description: Template updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Template not found
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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: template_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Template deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Template deleted successfully"
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Template not found
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
    ---
    tags:
      - Schedules
    security:
      - Bearer: []
    parameters:
      - name: day
        in: path
        type: integer
        required: true
        description: Day of week (0=Monday, 6=Sunday)
    responses:
      200:
        description: List of templates for the day
        schema:
          type: array
          items:
            type: object
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    try:
        templates = schedule_service.get_templates_by_day(day)
        return jsonify([ScheduleTemplateResponse.model_validate(t).model_dump() for t in templates]), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
