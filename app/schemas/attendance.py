"""Attendance schemas."""
from datetime import date, datetime, time
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
