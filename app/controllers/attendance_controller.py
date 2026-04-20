"""Attendance controller."""
from datetime import date
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_professor
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceRemoveRequest,
    AttendanceResponse,
)
from app.services.attendance_service import AttendanceService

attendance_bp = Blueprint('attendance', __name__)
attendance_service = AttendanceService()


@attendance_bp.route('/', methods=['GET'])
@jwt_required
@require_professor
def list_attendance():
    """List attendance records.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: class_instance_id
        in: query
        type: string
        format: uuid
        description: Filter by class instance
      - name: student_id
        in: query
        type: string
        format: uuid
        description: Filter by student
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: List of attendance records
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
                  class_instance_id:
                    type: string
                  student_id:
                    type: string
                  attended_at:
                    type: string
                    format: date-time
            total:
              type: integer
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    class_instance_id = request.args.get('class_instance_id')
    student_id = request.args.get('student_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        if class_instance_id:
            attendances = attendance_service.get_class_attendances(
                UUID(class_instance_id)
            )
        elif student_id:
            result = attendance_service.get_student_attendances(
                UUID(student_id),
                months=1,
                page=page,
                per_page=per_page
            )
            return jsonify({
                'items': [AttendanceResponse.model_validate(a).model_dump() for a in result['items']],
                'total': result['total'],
                'pages': result['pages'],
                'current_page': result['current_page']
            }), 200
        else:
            return jsonify({
                'error': 'VALIDATION_ERROR',
                'message': 'class_instance_id or student_id required'
            }), 400

        return jsonify({
            'items': [AttendanceResponse.model_validate(a).model_dump() for a in attendances],
            'total': len(attendances)
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@attendance_bp.route('/', methods=['POST'])
@jwt_required
@require_professor
def register_attendance():
    """Register attendance for students.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - class_instance_id
            - student_ids
          properties:
            class_instance_id:
              type: string
              format: uuid
              description: Class instance ID
            student_ids:
              type: array
              items:
                type: string
                format: uuid
              description: List of student IDs
    responses:
      201:
        description: Attendance registered successfully
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              class_instance_id:
                type: string
              student_id:
                type: string
              attended_at:
                type: string
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    data = request.get_json()

    try:
        attendance_data = AttendanceCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        attendances = attendance_service.register_attendance(
            class_instance_id=attendance_data.class_instance_id,
            student_ids=attendance_data.student_ids
        )
        return jsonify([AttendanceResponse.model_validate(a).model_dump() for a in attendances]), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@attendance_bp.route('/remove', methods=['POST'])
@jwt_required
@require_professor
def remove_attendance():
    """Remove attendance for a student.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - class_instance_id
            - student_id
          properties:
            class_instance_id:
              type: string
              format: uuid
            student_id:
              type: string
              format: uuid
    responses:
      200:
        description: Attendance removed successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Attendance removed successfully"
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Attendance record not found
    """
    data = request.get_json()

    try:
        remove_data = AttendanceRemoveRequest(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        attendance_service.remove_attendance(
            class_instance_id=remove_data.class_instance_id,
            student_id=remove_data.student_id
        )
        return jsonify({'message': 'Attendance removed successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@attendance_bp.route('/daily/<date_str>', methods=['GET'])
@jwt_required
@require_professor
def get_daily_attendance(date_str: str):
    """Get daily attendance summary.
    ---
    tags:
      - Attendance
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
        description: Daily attendance summary
        schema:
          type: array
          items:
            type: object
            properties:
              class_id:
                type: string
              class_time:
                type: string
              course_type:
                type: string
              attendance_count:
                type: integer
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
        summary = attendance_service.get_daily_attendance(target_date)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@attendance_bp.route('/student/<uuid:student_id>', methods=['GET'])
@jwt_required
@require_professor
def get_student_attendance(student_id: UUID):
    """Get attendance history for a student.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
      - name: months
        in: query
        type: integer
        default: 1
        enum: [1, 2, 3]
        description: Number of months to look back
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 50
    responses:
      200:
        description: Student attendance history
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
                  class_instance_id:
                    type: string
                  attended_at:
                    type: string
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
      404:
        description: Student not found
    """
    months = request.args.get('months', 1, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        result = attendance_service.get_student_attendances(
            student_id=student_id,
            months=months,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [AttendanceResponse.model_validate(a).model_dump() for a in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@attendance_bp.route('/student/<uuid:student_id>/stats', methods=['GET'])
@jwt_required
@require_professor
def get_student_attendance_stats(student_id: UUID):
    """Get attendance statistics for a student.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
      - name: months
        in: query
        type: integer
        default: 1
        enum: [1, 2, 3]
        description: Number of months to analyze
    responses:
      200:
        description: Attendance statistics
        schema:
          type: object
          properties:
            total_classes:
              type: integer
            attended_classes:
              type: integer
            attendance_rate:
              type: number
              description: Percentage (0-100)
      401:
        description: Unauthorized
      404:
        description: Student not found
    """
    months = request.args.get('months', 1, type=int)

    try:
        stats = attendance_service.get_attendance_stats(
            student_id=student_id,
            months=months
        )
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@attendance_bp.route('/class/<uuid:class_instance_id>/count', methods=['GET'])
@jwt_required
@require_professor
def get_class_attendance_count(class_instance_id: UUID):
    """Get attendance count for a class.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: class_instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Attendance count
        schema:
          type: object
          properties:
            count:
              type: integer
      401:
        description: Unauthorized
      404:
        description: Class not found
    """
    try:
        count = attendance_service.get_class_attendance_count(class_instance_id)
        return jsonify({'count': count}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@attendance_bp.route('/class/<uuid:class_instance_id>/students', methods=['GET'])
@jwt_required
@require_professor
def get_class_attending_students(class_instance_id: UUID):
    """Get list of students attending a class.
    ---
    tags:
      - Attendance
    security:
      - Bearer: []
    parameters:
      - name: class_instance_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: List of attending students
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              student_id:
                type: string
              attended_at:
                type: string
      401:
        description: Unauthorized
      404:
        description: Class not found
    """
    try:
        attendances = attendance_service.get_class_attendances(class_instance_id)
        return jsonify([AttendanceResponse.model_validate(a).model_dump() for a in attendances]), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
