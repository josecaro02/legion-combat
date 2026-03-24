from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, condecimal


# ============== Auth Schemas ==============

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    old_password: str
    new_password: str = Field(..., min_length=8)


# ============== User Schemas ==============

class UserRole(str):
    """User role type."""
    OWNER = "owner"
    PROFESSOR = "professor"


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """User list response schema."""
    items: List[UserResponse]
    total: int
    pages: int
    current_page: int


# ============== Student Schemas ==============

class CourseType(str):
    """Course type."""
    BOXING = "boxing"
    KICKBOXING = "kickboxing"
    BOTH = "both"


class StudentCreate(BaseModel):
    """Student creation schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    course: str
    enrollment_date: Optional[date] = Field(default_factory=date.today)


class StudentUpdate(BaseModel):
    """Student update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    course: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    """Student response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    address: Optional[str]
    phone: Optional[str]
    course: str
    enrollment_date: date
    is_active: bool
    created_at: datetime


class StudentListResponse(BaseModel):
    """Student list response schema."""
    items: List[StudentResponse]
    total: int
    pages: int
    current_page: int


# ============== Payment Schemas ==============

AmountDecimal = condecimal(max_digits=10, decimal_places=2, gt=0)

class PaymentStatus(str):
    """Payment status."""
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentCreate(BaseModel):
    """Payment creation schema."""
    student_id: UUID
    amount: AmountDecimal
    due_date: date
    idempotency_key: str = Field(..., min_length=10, max_length=64)
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    """Payment update schema."""
    amount: Optional[AmountDecimal] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    amount: Decimal
    status: str
    payment_date: Optional[date]
    due_date: date
    notes: Optional[str]
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle Decimal."""
        data = {
            'id': obj.id,
            'student_id': obj.student_id,
            'amount': obj.amount,
            'status': obj.status.value if hasattr(obj.status, 'value') else obj.status,
            'payment_date': obj.payment_date,
            'due_date': obj.due_date,
            'notes': obj.notes,
            'created_at': obj.created_at,
        }
        return cls(**data)


class PaymentListResponse(BaseModel):
    """Payment list response schema."""
    items: List[PaymentResponse]
    total: int
    pages: int
    current_page: int


class PaymentWithStudentResponse(PaymentResponse):
    """Payment with student info response."""
    student_name: str


# ============== Schedule Schemas ==============

class DayOfWeek(int):
    """Day of week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class ScheduleTemplateCreate(BaseModel):
    """Schedule template creation schema."""
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    course_type: str
    max_capacity: int = Field(default=20, ge=1)
    valid_from: date
    professor_id: UUID


class ScheduleTemplateUpdate(BaseModel):
    """Schedule template update schema."""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    course_type: Optional[str] = None
    max_capacity: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class ScheduleTemplateResponse(BaseModel):
    """Schedule template response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    course_type: str
    max_capacity: int
    valid_from: date
    valid_to: Optional[date]
    is_active: bool
    version: int
    professor_id: UUID
    created_at: datetime


class ScheduleTemplateListResponse(BaseModel):
    """Schedule template list response schema."""
    items: List[ScheduleTemplateResponse]
    total: int


# ============== Class Instance Schemas ==============

class ClassStatus(str):
    """Class status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ClassInstanceCreate(BaseModel):
    """Class instance creation schema."""
    template_id: Optional[UUID] = None
    date: date
    start_time: time
    end_time: time
    course_type: str
    max_capacity: int = Field(default=20, ge=1)
    professor_id: UUID
    notes: Optional[str] = None


class ClassInstanceUpdate(BaseModel):
    """Class instance update schema."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    status: Optional[str] = None
    max_capacity: Optional[int] = Field(None, ge=1)
    professor_id: Optional[UUID] = None
    notes: Optional[str] = None


class ClassInstanceResponse(BaseModel):
    """Class instance response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: Optional[UUID]
    date: date
    start_time: time
    end_time: time
    course_type: str
    status: str
    max_capacity: int
    professor_id: UUID
    current_attendance: int = 0
    notes: Optional[str]
    created_at: datetime


class ClassInstanceDetailResponse(ClassInstanceResponse):
    """Class instance with details response."""
    professor_name: str


class ClassInstanceListResponse(BaseModel):
    """Class instance list response schema."""
    items: List[ClassInstanceResponse]
    total: int
    pages: int
    current_page: int


# ============== Attendance Schemas ==============

class AttendanceCreate(BaseModel):
    """Attendance creation schema."""
    class_instance_id: UUID
    student_ids: List[UUID] = Field(..., min_length=1)


class AttendanceRemoveRequest(BaseModel):
    """Attendance removal request schema."""
    class_instance_id: UUID
    student_id: UUID


class AttendanceResponse(BaseModel):
    """Attendance response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    class_instance_id: UUID
    student_id: UUID
    student_name: str
    check_in_time: datetime


class AttendanceListResponse(BaseModel):
    """Attendance list response schema."""
    items: List[AttendanceResponse]
    total: int


class DailyAttendanceSummary(BaseModel):
    """Daily attendance summary schema."""
    class_id: UUID
    time: str
    course: str
    attendance_count: int
    students: List[UUID]


class StudentAttendanceHistory(BaseModel):
    """Student attendance history item."""
    date: date
    start_time: time
    course_type: str
    check_in_time: datetime


class AttendanceStats(BaseModel):
    """Attendance statistics."""
    total_classes: int
    total_attendances: int
    attendance_by_course: dict
    monthly_attendance: dict
