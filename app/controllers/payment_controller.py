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
    ---
    tags:
      - Payments
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
        description: Items per page
      - name: status
        in: query
        type: string
        enum: [pending, paid, overdue]
        description: Filter by payment status
    responses:
      200:
        description: List of payments
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
                  student_id:
                    type: string
                    format: uuid
                  amount:
                    type: string
                    example: "25000.00"
                  status:
                    type: string
                    enum: [pending, paid, overdue]
                  due_date:
                    type: string
                    format: date
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      401:
        description: Unauthorized
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - student_id
            - amount
            - due_date
            - idempotency_key
          properties:
            student_id:
              type: string
              format: uuid
              example: "123e4567-e89b-12d3-a456-426614174000"
            amount:
              type: number
              format: decimal
              description: Payment amount (positive number)
              example: 25000.00
            due_date:
              type: string
              format: date
              example: "2024-03-20"
            idempotency_key:
              type: string
              minLength: 10
              maxLength: 64
              description: Unique key to prevent duplicate payments
            notes:
              type: string
              description: Optional notes
    responses:
      201:
        description: Payment created successfully
      400:
        description: Validation error or duplicate payment
      401:
        description: Unauthorized
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Payment information
        schema:
          type: object
          properties:
            id:
              type: string
            student_id:
              type: string
            amount:
              type: string
            status:
              type: string
            due_date:
              type: string
            payment_date:
              type: string
            student_name:
              type: string
      401:
        description: Unauthorized
      404:
        description: Payment not found
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: payment_id
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
            amount:
              type: number
              description: New amount
            due_date:
              type: string
              format: date
            notes:
              type: string
    responses:
      200:
        description: Payment updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Payment not found
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: string
        format: uuid
        required: true
    responses:
      200:
        description: Payment deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Payment deleted successfully"
      401:
        description: Unauthorized
      404:
        description: Payment not found
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: student_id
        in: path
        type: string
        format: uuid
        required: true
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
      - name: status
        in: query
        type: string
        enum: [pending, paid, overdue]
    responses:
      200:
        description: List of payments for student
      401:
        description: Unauthorized
      404:
        description: Student not found
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: string
        format: uuid
        required: true
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            payment_date:
              type: string
              format: date
              description: Optional payment date (defaults to today)
    responses:
      200:
        description: Payment marked as paid
        schema:
          type: object
          properties:
            id:
              type: string
            status:
              type: string
              example: "paid"
            payment_date:
              type: string
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Payment not found
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 5
        description: Number of days to look ahead
    responses:
      200:
        description: List of upcoming payments
        schema:
          type: array
          items:
            type: object
      401:
        description: Unauthorized
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    responses:
      200:
        description: List of overdue payments
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              student_name:
                type: string
              amount:
                type: string
              due_date:
                type: string
      401:
        description: Unauthorized
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
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    responses:
      200:
        description: Summary of debtors
        schema:
          type: array
          items:
            type: object
            properties:
              student_id:
                type: string
              student_name:
                type: string
              overdue_count:
                type: integer
              total_amount:
                type: string
      401:
        description: Unauthorized
    """
    try:
        summary = payment_service.get_overdue_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500
