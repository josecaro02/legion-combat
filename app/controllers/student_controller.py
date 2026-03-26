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
    ---
    tags:
      - Students
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
        maximum: 100
        description: Items per page
      - name: course
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
        description: List of students
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
                  first_name:
                    type: string
                  last_name:
                    type: string
                  course:
                    type: string
                    enum: [boxing, kickboxing, both]
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
        description: Forbidden - Professor access required
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: q
        in: query
        type: string
        required: true
        minLength: 2
        description: Search query (first name or last name)
    responses:
      200:
        description: List of matching students
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                format: uuid
              first_name:
                type: string
              last_name:
                type: string
              course:
                type: string
      400:
        description: Validation error
      401:
        description: Unauthorized
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
        description: Student UUID
    responses:
      200:
        description: Student information
        schema:
          type: object
          properties:
            id:
              type: string
              format: uuid
            first_name:
              type: string
            last_name:
              type: string
            course:
              type: string
            address:
              type: string
            phone:
              type: string
            enrollment_date:
              type: string
              format: date
            is_active:
              type: boolean
      401:
        description: Unauthorized
      404:
        description: Student not found
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - first_name
            - last_name
            - course
          properties:
            first_name:
              type: string
              example: "Juan"
            last_name:
              type: string
              example: "Pérez"
            course:
              type: string
              enum: [boxing, kickboxing, both]
              example: "boxing"
            address:
              type: string
              example: "Av. Principal 123"
            phone:
              type: string
              example: "+56912345678"
            enrollment_date:
              type: string
              format: date
              example: "2024-03-20"
    responses:
      201:
        description: Student created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: student_id
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
            address:
              type: string
            phone:
              type: string
            course:
              type: string
              enum: [boxing, kickboxing, both]
            is_active:
              type: boolean
    responses:
      200:
        description: Student updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Student not found
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Student deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Student deleted successfully"
      401:
        description: Unauthorized
      404:
        description: Student not found
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Student deactivated
      401:
        description: Unauthorized
      404:
        description: Student not found
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
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Student activated
      401:
        description: Unauthorized
      404:
        description: Student not found
    """
    try:
        student = student_service.activate_student(student_id)
        return jsonify(StudentResponse.model_validate(student).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@student_bp.route('/upcoming-payments', methods=['GET'])
@jwt_required
@require_professor
def get_students_with_upcoming_payment_due():
    """Get students whose last payment is approaching one month anniversary.

    Returns active students whose last paid payment_date + 1 month
    falls within the specified window from today. Useful for sending
    payment reminders before the next month is due.
    ---
    tags:
      - Students
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 5
        minimum: 1
        maximum: 30
        description: Number of days to look ahead for payments approaching one month
    responses:
      200:
        description: List of students with upcoming payment due dates
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  student:
                    type: object
                    properties:
                      id:
                        type: string
                        format: uuid
                      first_name:
                        type: string
                      last_name:
                        type: string
                      phone:
                        type: string
                      course:
                        type: string
                  last_payment_date:
                    type: string
                    format: date
                    description: Date of the last payment made
                  due_soon_date:
                    type: string
                    format: date
                    description: Date when one month from last payment is reached (payment_date + 1 month)
            total:
              type: integer
              description: Total number of students found
      400:
        description: Invalid days parameter
      401:
        description: Unauthorized
      403:
        description: Forbidden - Professor access required
    """
    days = request.args.get('days', 5, type=int)

    # Validate days parameter
    if days < 1 or days > 30:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': 'days parameter must be between 1 and 30'
        }), 400
    
    try:
        results = student_service.get_students_with_upcoming_payment_due(days=days)

        # Build response
        items = []
        for result in results:
            student = result['student']
            items.append({
                'student': StudentResponse.model_validate(student).model_dump(),
                'last_payment_date': result['last_payment_date'].isoformat(),
                'due_soon_date': result['due_soon_date'].isoformat()
            })

        return jsonify({
            'items': items,
            'total': len(items)
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
