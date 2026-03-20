"""Pytest configuration and fixtures."""
import uuid
from datetime import date, datetime, time, timedelta

import pytest
from flask import Flask

from app import create_app
from app.extensions import db
from app.models.class_instance import ClassInstance, ClassStatus
from app.models.payment import Payment, PaymentStatus
from app.models.schedule import DayOfWeek, ScheduleTemplate
from app.models.student import CourseType, Student
from app.models.user import User, UserRole
from app.utils.password_utils import hash_password


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_owner(app):
    """Create test owner user."""
    with app.app_context():
        user = User(
            email='owner@test.com',
            password_hash=hash_password('password123'),
            first_name='Test',
            last_name='Owner',
            role=UserRole.OWNER
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_professor(app):
    """Create test professor user."""
    with app.app_context():
        user = User(
            email='professor@test.com',
            password_hash=hash_password('password123'),
            first_name='Test',
            last_name='Professor',
            role=UserRole.PROFESSOR
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_student(app):
    """Create test student."""
    with app.app_context():
        student = Student(
            first_name='Test',
            last_name='Student',
            course=CourseType.BOXING,
            enrollment_date=date.today()
        )
        db.session.add(student)
        db.session.commit()
        return student


@pytest.fixture
def test_schedule_template(app, test_professor):
    """Create test schedule template."""
    with app.app_context():
        template = ScheduleTemplate(
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(18, 0),
            end_time=time(19, 0),
            course_type=CourseType.BOXING,
            max_capacity=20,
            valid_from=date.today(),
            professor_id=test_professor.id
        )
        db.session.add(template)
        db.session.commit()
        return template


@pytest.fixture
def test_class_instance(app, test_schedule_template, test_professor):
    """Create test class instance."""
    with app.app_context():
        instance = ClassInstance(
            template_id=test_schedule_template.id,
            date=date.today(),
            start_time=time(18, 0),
            end_time=time(19, 0),
            course_type=CourseType.BOXING,
            max_capacity=20,
            professor_id=test_professor.id,
            status=ClassStatus.SCHEDULED
        )
        db.session.add(instance)
        db.session.commit()
        return instance


@pytest.fixture
def test_payment(app, test_student):
    """Create test payment."""
    with app.app_context():
        payment = Payment(
            student_id=test_student.id,
            amount=50.00,
            due_date=date.today() + timedelta(days=30),
            status=PaymentStatus.PENDING,
            idempotency_key=str(uuid.uuid4()).replace('-', '')
        )
        db.session.add(payment)
        db.session.commit()
        return payment


@pytest.fixture
def auth_headers_owner(app, test_owner):
    """Get auth headers for owner."""
    with app.app_context():
        from app.utils.jwt_utils import create_access_token
        token = create_access_token(test_owner.id, test_owner.role.value)
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_headers_professor(app, test_professor):
    """Get auth headers for professor."""
    with app.app_context():
        from app.utils.jwt_utils import create_access_token
        token = create_access_token(test_professor.id, test_professor.role.value)
        return {'Authorization': f'Bearer {token}'}
