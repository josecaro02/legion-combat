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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        description: Start date filter (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        format: date
        description: End date filter (YYYY-MM-DD)
      - name: course_type
        in: query
        type: string
        enum: [boxing, kickboxing, both]
      - name: status
        in: query
        type: string
        enum: [scheduled, in_progress, completed, cancelled]
      - name: professor_id
        in: query
        type: string
        format: uuid
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: List of class instances
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
                  date:
                    type: string
                    format: date
                  start_time:
                    type: string
                  end_time:
                    type: string
                  course_type:
                    type: string
                  status:
                    type: string
                  max_capacity:
                    type: integer
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        required: true
        description: Start date (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        format: date
        required: true
        description: End date (YYYY-MM-DD)
      - name: course_type
        in: query
        type: string
        enum: [boxing, kickboxing, both]
        description: Filter by course type
    responses:
      200:
        description: List of class instances
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              date:
                type: string
              start_time:
                type: string
              end_time:
                type: string
              course_type:
                type: string
              status:
                type: string
      400:
        description: Validation error
      401:
        description: Unauthorized
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - date
            - start_time
            - end_time
            - course_type
            - professor_id
          properties:
            date:
              type: string
              format: date
              example: "2024-03-20"
            start_time:
              type: string
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
            professor_id:
              type: string
              format: uuid
            template_id:
              type: string
              format: uuid
              description: Optional template ID
            notes:
              type: string
    responses:
      201:
        description: Class instance created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Class instance information
        schema:
          type: object
          properties:
            id:
              type: string
            date:
              type: string
            start_time:
              type: string
            end_time:
              type: string
            course_type:
              type: string
            status:
              type: string
            professor_id:
              type: string
            max_capacity:
              type: integer
      401:
        description: Unauthorized
      404:
        description: Class instance not found
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: instance_id
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
            start_time:
              type: string
            end_time:
              type: string
            status:
              type: string
              enum: [scheduled, in_progress, completed, cancelled]
            max_capacity:
              type: integer
            professor_id:
              type: string
              format: uuid
            notes:
              type: string
    responses:
      200:
        description: Class instance updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Class instance not found
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Class instance deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Class instance deleted successfully"
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Class instance not found
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Class cancelled successfully
        schema:
          type: object
          properties:
            id:
              type: string
            status:
              type: string
              example: "cancelled"
      400:
        description: Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Class marked as completed
        schema:
          type: object
          properties:
            id:
              type: string
            status:
              type: string
              example: "completed"
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Class instance not found
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
    ---
    tags:
      - Classes
    security:
      - Bearer: []
    parameters:
      - name: date_str
        in: path
        type: string
        required: true
        description: Date in YYYY-MM-DD format
    responses:
      200:
        description: List of classes for the date
        schema:
          type: array
          items:
            type: object
      400:
        description: Invalid date format
      401:
        description: Unauthorized
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
