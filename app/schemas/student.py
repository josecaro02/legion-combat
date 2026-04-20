"""Student schemas."""
import re
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentCreate(BaseModel):
    """Student creation schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    course: str
    enrollment_date: Optional[date] = Field(default_factory=date.today)
    emergency_contact_name: str = Field(..., min_length=1, max_length=100)
    emergency_contact_phone: str = Field(..., min_length=7, max_length=20)
    photo_url: Optional[str] = Field(None, max_length=500)

    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_emergency_phone(cls, v: str) -> str:
        """Validate emergency contact phone format."""
        if v:
            # Basic phone validation: at least 7 digits, allows +, -, spaces, parentheses
            phone_pattern = r'^[\d\+\-\(\)\s]{7,20}$'
            if not re.match(phone_pattern, v):
                raise ValueError('Invalid phone number format')
        return v

    @field_validator('photo_url')
    @classmethod
    def validate_photo_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate photo_url is a valid Cloudinary URL.

        NOTE: Image Consistency Edge Case
        -------------------------------
        If frontend uploads an image to Cloudinary but the backend request fails,
        there may be orphaned images in Cloudinary. This is an accepted inconsistency
        as there is no cleanup mechanism required. The backend only validates the
        received URL, it does not manage Cloudinary storage.
        """
        if v is None:
            return v

        # Must be a valid URL format
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v, re.IGNORECASE):
            raise ValueError('Invalid URL format')

        # Must contain res.cloudinary.com
        if 'res.cloudinary.com' not in v:
            raise ValueError('Photo URL must be from Cloudinary (res.cloudinary.com)')

        return v


class StudentUpdate(BaseModel):
    """Student update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    course: Optional[str] = None
    is_active: Optional[bool] = None
    emergency_contact_name: Optional[str] = Field(None, min_length=1, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, min_length=7, max_length=20)
    photo_url: Optional[str] = Field(None, max_length=500)

    @field_validator('emergency_contact_phone')
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate emergency contact phone format."""
        if v is not None:
            # Basic phone validation: at least 7 digits, allows +, -, spaces, parentheses
            phone_pattern = r'^[\d\+\-\(\)\s]{7,20}$'
            if not re.match(phone_pattern, v):
                raise ValueError('Invalid phone number format')
        return v

    @field_validator('photo_url')
    @classmethod
    def validate_photo_url(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate photo_url is a valid Cloudinary URL.

        NOTE: Image Consistency Edge Case
        -------------------------------
        If frontend uploads an image to Cloudinary but the backend request fails,
        there may be orphaned images in Cloudinary. This is an accepted inconsistency
        as there is no cleanup mechanism required. The backend only validates the
        received URL, it does not manage Cloudinary storage.
        """
        if v is None:
            return v

        # Must be a valid URL format
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, v, re.IGNORECASE):
            raise ValueError('Invalid URL format')

        # Must contain res.cloudinary.com
        if 'res.cloudinary.com' not in v:
            raise ValueError('Photo URL must be from Cloudinary (res.cloudinary.com)')

        return v


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
    emergency_contact_name: str
    emergency_contact_phone: str
    photo_url: Optional[str]
    created_at: datetime


class StudentListResponse(BaseModel):
    """Student list response schema."""
    items: List[StudentResponse]
    total: int
    pages: int
    current_page: int
