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

    Query Parameters:
        - class_instance_id: Filter by class instance
        - student_id: Filter by student
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)

    Returns:
        - items: List of attendance records
        - total: Total count
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

    Request Body:
        - class_instance_id: Class instance ID
        - student_ids: List of student IDs

    Returns:
        - List of created attendance records
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

    Request Body:
        - class_instance_id: Class instance ID
        - student_id: Student ID

    Returns:
        - message: Success message
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

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        - List of class summaries with attendance counts
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

    Args:
        student_id: Student ID

    Query Parameters:
        - months: Number of months to look back (1, 2, or 3, default: 1)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)

    Returns:
        - items: List of attendance records
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
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

    Args:
        student_id: Student ID

    Query Parameters:
        - months: Number of months to analyze (1, 2, or 3, default: 1)

    Returns:
        - Attendance statistics
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

    Args:
        class_instance_id: Class instance ID

    Returns:
        - count: Number of attendances
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

    Args:
        class_instance_id: Class instance ID

    Returns:
        - items: List of attending students
    """
    try:
        attendances = attendance_service.get_class_attendances(class_instance_id)
        return jsonify([AttendanceResponse.model_validate(a).model_dump() for a in attendances]), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
