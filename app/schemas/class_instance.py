"""Class instance schemas."""
from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
