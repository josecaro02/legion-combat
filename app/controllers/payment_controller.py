"""Payment controller."""
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import jwt_required
from app.middleware.rbac_middleware import require_professor
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from app.services.payment_service import PaymentService

payment_bp = Blueprint('payments', __name__)
payment_service = PaymentService()


@payment_bp.route('/', methods=['GET'])
@jwt_required
@require_professor
def list_payments():
    """List payments with optional filters.

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - status: Filter by status (pending, paid, overdue)

    Returns:
        - items: List of payments
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    try:
        result = payment_service.list_payments(
            status=status,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [PaymentResponse.from_orm(p).model_dump() for p in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@payment_bp.route('/', methods=['POST'])
@jwt_required
@require_professor
def create_payment():
    """Create a new payment.

    Request Body:
        - student_id: Student ID
        - amount: Payment amount
        - due_date: Due date (YYYY-MM-DD)
        - idempotency_key: Unique key for idempotency (10-64 chars)
        - notes: Optional notes

    Returns:
        - Created payment information
    """
    data = request.get_json()

    try:
        payment_data = PaymentCreate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        payment = payment_service.create_payment(
            student_id=payment_data.student_id,
            amount=payment_data.amount,
            due_date=payment_data.due_date,
            idempotency_key=payment_data.idempotency_key,
            notes=payment_data.notes
        )
        return jsonify(PaymentResponse.from_orm(payment).model_dump()), 201
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@payment_bp.route('/<uuid:payment_id>', methods=['GET'])
@jwt_required
@require_professor
def get_payment(payment_id: UUID):
    """Get payment by ID.

    Args:
        payment_id: Payment ID

    Returns:
        - Payment information
    """
    try:
        payment = payment_service.get_payment_with_student(payment_id)
        response = PaymentResponse.from_orm(payment).model_dump()
        if payment.student:
            response['student_name'] = payment.student.full_name
        return jsonify(response), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@payment_bp.route('/<uuid:payment_id>', methods=['PUT'])
@jwt_required
@require_professor
def update_payment(payment_id: UUID):
    """Update payment.

    Args:
        payment_id: Payment ID

    Request Body:
        - amount: New amount (optional)
        - due_date: New due date (optional)
        - notes: New notes (optional)

    Returns:
        - Updated payment information
    """
    data = request.get_json()

    try:
        payment_data = PaymentUpdate(**data)
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400

    try:
        payment = payment_service.update_payment(
            payment_id=payment_id,
            amount=payment_data.amount,
            due_date=payment_data.due_date,
            notes=payment_data.notes
        )
        return jsonify(PaymentResponse.from_orm(payment).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@payment_bp.route('/<uuid:payment_id>', methods=['DELETE'])
@jwt_required
@require_professor
def delete_payment(payment_id: UUID):
    """Delete payment.

    Args:
        payment_id: Payment ID

    Returns:
        - message: Success message
    """
    try:
        payment_service.delete_payment(payment_id)
        return jsonify({'message': 'Payment deleted successfully'}), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@payment_bp.route('/student/<uuid:student_id>', methods=['GET'])
@jwt_required
@require_professor
def get_student_payments(student_id: UUID):
    """Get payments for a student.

    Args:
        student_id: Student ID

    Query Parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20)
        - status: Filter by status

    Returns:
        - items: List of payments
        - total: Total count
        - pages: Total pages
        - current_page: Current page number
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    try:
        result = payment_service.get_student_payments(
            student_id=student_id,
            status=status,
            page=page,
            per_page=per_page
        )
        return jsonify({
            'items': [PaymentResponse.from_orm(p).model_dump() for p in result['items']],
            'total': result['total'],
            'pages': result['pages'],
            'current_page': result['current_page']
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404


@payment_bp.route('/<uuid:payment_id>/mark-paid', methods=['POST'])
@jwt_required
@require_professor
def mark_payment_paid(payment_id: UUID):
    """Mark payment as paid.

    Args:
        payment_id: Payment ID

    Request Body:
        - payment_date: Optional payment date (defaults to today)

    Returns:
        - Updated payment information
    """
    data = request.get_json() or {}
    payment_date = data.get('payment_date')

    try:
        from datetime import date
        if payment_date:
            payment_date = date.fromisoformat(payment_date)

        payment = payment_service.mark_as_paid(payment_id, payment_date)
        return jsonify(PaymentResponse.from_orm(payment).model_dump()), 200
    except Exception as e:
        return jsonify({
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400


@payment_bp.route('/upcoming', methods=['GET'])
@jwt_required
@require_professor
def get_upcoming_payments():
    """Get upcoming payments due in next N days.

    Query Parameters:
        - days: Number of days to look ahead (default: 5)

    Returns:
        - List of upcoming payments
    """
    days = request.args.get('days', 5, type=int)

    try:
        payments = payment_service.get_upcoming_payments(days=days)
        return jsonify([PaymentResponse.from_orm(p).model_dump() for p in payments]), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@payment_bp.route('/overdue', methods=['GET'])
@jwt_required
@require_professor
def get_overdue_payments():
    """Get overdue payments.

    Returns:
        - List of overdue payments with student info
    """
    try:
        payments = payment_service.get_overdue_payments()
        return jsonify([PaymentResponse.from_orm(p).model_dump() for p in payments]), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500


@payment_bp.route('/overdue/summary', methods=['GET'])
@jwt_required
@require_professor
def get_overdue_summary():
    """Get summary of overdue payments by student.

    Returns:
        - List of student summaries with overdue counts and totals
    """
    try:
        summary = payment_service.get_overdue_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
