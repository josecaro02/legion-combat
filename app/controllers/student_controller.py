"""Student controller."""
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_professor
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.services.student_service import StudentService

student_bp = Blueprint('students', __name__)
student_service = StudentService()


@student_bp.route('/', methods=['GET'])
@jwt_required
@require_professor
def list_students():
    """List students with optional filters.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - course: Filter by course type (boxing, kickboxing, both)
        - is_active: Filter by active status (true/false)

    Returns:
        - items: List of students
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    course = request.args.get('course')
    is_active = request.args.get('is_active')

    # Convert is_active to boolean
    if is_active is not None:
        is_active = is_active.lower() == 'true'

    try:
        result = student_service.list_students(
            course=course,
            is_active=is_active,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [StudentResponse.model_validate(s).model_dump() for s in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@student_bp.route('/search', methods=['GET'])
@jwt_required
@require_professor
def search_students():
    """Search students by name.

    Query Parameters:
        - q: Search query (first name or last name)

    Returns:
        - List of matching students
    """
    query = request.args.get('q', '')

    if len(query) < 2:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'Search query must be at least 2 characters'
        }), 400

    try:
        students = student_service.search_students(query)
        return jsonify([
            StudentResponse.model_validate(s).model_dump() for s in students
        ]), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@student_bp.route('/<uuid:student_id>', methods=['GET'])
@jwt_required
@require_professor
def get_student(student_id: UUID):
    """Get student by ID.

    Args:
        student_id: Student ID

    Returns:
        - Student information
    """
    try:
        student = student_service.get_student(student_id)
        return jsonify(StudentResponse.model_validate(student).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@student_bp.route('/', methods=['POST'])
@jwt_required
@require_professor
def create_student():
    """Create a new student.

    Request Body:
        - first_name: First name
        - last_name: Last name
        - course: Course type (boxing, kickboxing, both)
        - address: Optional address
        - phone: Optional phone
        - enrollment_date: Optional enrollment date (defaults to today)

    Returns:
        - Created student information
    """
    data = request.get_json()

    try:
        student_data = StudentCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        student = student_service.create_student(
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            course=student_data.course,
            address=student_data.address,
            phone=student_data.phone,
            enrollment_date=student_data.enrollment_date
        )
        return jsonify(StudentResponse.model_validate(student).model_dump()), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@student_bp.route('/<uuid:student_id>', methods=['PUT'])
@jwt_required
@require_professor
def update_student(student_id: UUID):
    """Update student.

    Args:
        student_id: Student ID

    Request Body:
        - first_name: First name (optional)
        - last_name: Last name (optional)
        - address: Address (optional)
        - phone: Phone (optional)
        - course: Course type (optional)
        - is_active: Active status (optional)

    Returns:
        - Updated student information
    """
    data = request.get_json()

    try:
        student_data = StudentUpdate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        student = student_service.update_student(
            student_id=student_id,
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            address=student_data.address,
            phone=student_data.phone,
            course=student_data.course,
            is_active=student_data.is_active
        )
        return jsonify(StudentResponse.model_validate(student).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@student_bp.route('/<uuid:student_id>', methods=['DELETE'])
@jwt_required
@require_professor
def delete_student(student_id: UUID):
    """Delete student.

    Args:
        student_id: Student ID

    Returns:
        - message: Success message
    """
    try:
        student_service.delete_student(student_id)
        return jsonify({'message': 'Student deleted successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@student_bp.route('/<uuid:student_id>/deactivate', methods=['POST'])
@jwt_required
@require_professor
def deactivate_student(student_id: UUID):
    """Deactivate a student.

    Args:
        student_id: Student ID

    Returns:
        - Updated student information
    """
    try:
        student = student_service.deactivate_student(student_id)
        return jsonify(StudentResponse.model_validate(student).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@student_bp.route('/<uuid:student_id>/activate', methods=['POST'])
@jwt_required
@require_professor
def activate_student(student_id: UUID):
    """Activate a student.

    Args:
        student_id: Student ID

    Returns:
        - Updated student information
    """
    try:
        student = student_service.activate_student(student_id)
        return jsonify(StudentResponse.model_validate(student).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
