"""Student schemas."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
