"""Controller modules."""
from flask import Flask

from app.controllers.auth_controller import auth_bp
from app.controllers.user_controller import user_bp
from app.controllers.student_controller import student_bp
from app.controllers.payment_controller import payment_bp
from app.controllers.schedule_controller import schedule_bp
from app.controllers.class_controller import class_bp
from app.controllers.attendance_controller import attendance_bp


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(student_bp, url_prefix='/students')
    app.register_blueprint(payment_bp, url_prefix='/payments')
    app.register_blueprint(schedule_bp, url_prefix='/schedules')
    app.register_blueprint(class_bp, url_prefix='/classes')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')


__all__ = [
    'auth_bp',
    'user_bp',
    'student_bp',
    'payment_bp',
    'schedule_bp',
    'class_bp',
    'attendance_bp',
    'register_blueprints',
]
