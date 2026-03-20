"""Tests for payment service."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.exceptions.custom_exceptions import BusinessError, NotFoundError, ValidationError
from app.models.payment import Payment, PaymentStatus
from app.services.payment_service import PaymentService


class TestPaymentService:
    """Test cases for PaymentService."""

    def test_create_payment(self, app, test_student):
        """Test creating a payment."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='unique-key-12345'
            )

            assert payment.student_id == test_student.id
            assert payment.amount == Decimal('50.00')
            assert payment.status == PaymentStatus.PENDING

    def test_create_payment_idempotency(self, app, test_student):
        """Test payment creation is idempotent."""
        with app.app_context():
            service = PaymentService()

            # Create first payment
            payment1 = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='same-key-12345'
            )

            # Create second payment with same key
            payment2 = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('75.00'),  # Different amount
                due_date=date.today() + timedelta(days=60),  # Different date
                idempotency_key='same-key-12345'
            )

            # Should return the first payment
            assert payment1.id == payment2.id
            assert payment2.amount == Decimal('50.00')  # Original amount

    def test_create_payment_invalid_amount(self, app, test_student):
        """Test creating payment with invalid amount."""
        with app.app_context():
            service = PaymentService()
            with pytest.raises(ValidationError):
                service.create_payment(
                    student_id=test_student.id,
                    amount=Decimal('-10.00'),
                    due_date=date.today() + timedelta(days=30),
                    idempotency_key='key-12345'
                )

    def test_create_payment_nonexistent_student(self, app):
        """Test creating payment for nonexistent student."""
        with app.app_context():
            service = PaymentService()
            with pytest.raises(NotFoundError):
                service.create_payment(
                    student_id='12345678-1234-1234-1234-123456789abc',
                    amount=Decimal('50.00'),
                    due_date=date.today() + timedelta(days=30),
                    idempotency_key='key-12345'
                )

    def test_mark_as_paid(self, app, test_student):
        """Test marking payment as paid."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='paid-key-12345'
            )

            updated = service.mark_as_paid(payment.id)

            assert updated.status == PaymentStatus.PAID
            assert updated.payment_date == date.today()

    def test_mark_already_paid_payment(self, app, test_student):
        """Test marking already paid payment."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='already-paid-key-12345'
            )

            # Mark as paid first time
            service.mark_as_paid(payment.id)

            # Try to mark as paid again
            with pytest.raises(BusinessError):
                service.mark_as_paid(payment.id)

    def test_get_overdue_payments(self, app, test_student):
        """Test getting overdue payments."""
        with app.app_context():
            from app.extensions import db

            service = PaymentService()

            # Create overdue payment
            overdue = Payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() - timedelta(days=5),
                status=PaymentStatus.PENDING,
                idempotency_key='overdue-key-12345'
            )
            db.session.add(overdue)

            # Create future payment
            future = Payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                status=PaymentStatus.PENDING,
                idempotency_key='future-key-12345'
            )
            db.session.add(future)
            db.session.commit()

            overdue_payments = service.get_overdue_payments()

            assert len(overdue_payments) == 1
            assert overdue_payments[0].id == overdue.id

    def test_get_upcoming_payments(self, app, test_student):
        """Test getting upcoming payments."""
        with app.app_context():
            from app.extensions import db

            service = PaymentService()

            # Create payment due in 3 days
            upcoming = Payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=3),
                status=PaymentStatus.PENDING,
                idempotency_key='upcoming-key-12345'
            )
            db.session.add(upcoming)

            # Create payment due in 30 days (outside range)
            far_future = Payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                status=PaymentStatus.PENDING,
                idempotency_key='far-key-12345'
            )
            db.session.add(far_future)
            db.session.commit()

            upcoming_payments = service.get_upcoming_payments(days=5)

            assert len(upcoming_payments) == 1
            assert upcoming_payments[0].id == upcoming.id

    def test_update_payment(self, app, test_student):
        """Test updating payment."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='update-key-12345'
            )

            new_date = date.today() + timedelta(days=60)
            updated = service.update_payment(
                payment_id=payment.id,
                due_date=new_date
            )

            assert updated.due_date == new_date
            assert updated.amount == Decimal('50.00')  # Unchanged

    def test_update_paid_payment(self, app, test_student):
        """Test updating paid payment fails."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='no-update-key-12345'
            )

            # Mark as paid
            service.mark_as_paid(payment.id)

            # Try to update
            with pytest.raises(BusinessError):
                service.update_payment(
                    payment_id=payment.id,
                    amount=Decimal('75.00')
                )

    def test_delete_payment(self, app, test_student):
        """Test deleting payment."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='delete-key-12345'
            )

            service.delete_payment(payment.id)

            # Should raise NotFoundError
            with pytest.raises(NotFoundError):
                service.get_payment(payment.id)

    def test_delete_paid_payment(self, app, test_student):
        """Test deleting paid payment fails."""
        with app.app_context():
            service = PaymentService()
            payment = service.create_payment(
                student_id=test_student.id,
                amount=Decimal('50.00'),
                due_date=date.today() + timedelta(days=30),
                idempotency_key='no-delete-key-12345'
            )

            # Mark as paid
            service.mark_as_paid(payment.id)

            # Try to delete
            with pytest.raises(BusinessError):
                service.delete_payment(payment.id)
