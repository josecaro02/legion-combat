"""Service modules."""
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.student_service import StudentService
from app.services.payment_service import PaymentService
from app.services.schedule_service import ScheduleService
from app.services.class_service import ClassService
from app.services.attendance_service import AttendanceService

__all__ = [
    'AuthService',
    'UserService',
    'StudentService',
    'PaymentService',
    'ScheduleService',
    'ClassService',
    'AttendanceService',
]
