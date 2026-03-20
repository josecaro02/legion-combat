"""Schedule schemas."""
from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
