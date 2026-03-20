"""Schedule service."""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from app.exceptions.custom_exceptions import BusinessError, NotFoundError, ValidationError
from app.models.schedule import DayOfWeek, ScheduleTemplate
from app.models.student import CourseType
from app.repositories.schedule_repository import ScheduleRepository
from app.utils.date_utils import get_weekday_dates


class ScheduleService:
    """Service for schedule operations."""

    def __init__(self, schedule_repo: Optional[ScheduleRepository] = None):
        self.schedule_repo = schedule_repo or ScheduleRepository()

    def create_template(
        self,
        day_of_week: int,
        start_time,
        end_time,
        course_type: str,
        max_capacity: int,
        valid_from: date,
        professor_id: UUID
    ) -> ScheduleTemplate:
        """Create a new schedule template.

        Args:
            day_of_week: Day of week (0-6, Monday-Sunday)
            start_time: Start time
            end_time: End time
            course_type: Course type
            max_capacity: Maximum capacity
            valid_from: Valid from date
            professor_id: Professor ID

        Returns:
            Created template
        """
        # Validate day of week
        try:
            dow = DayOfWeek(day_of_week)
        except ValueError:
            raise ValidationError(f"Invalid day of week: {day_of_week}")

        # Validate course type
        try:
            course = CourseType(course_type)
        except ValueError:
            raise ValidationError(f"Invalid course type: {course_type}")

        # Validate times
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time")

        template = ScheduleTemplate(
            day_of_week=dow,
            start_time=start_time,
            end_time=end_time,
            course_type=course,
            max_capacity=max_capacity,
            valid_from=valid_from,
            professor_id=professor_id
        )
        return self.schedule_repo.create(template)

    def get_template(self, template_id: UUID) -> ScheduleTemplate:
        """Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template
        """
        template = self.schedule_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError("Schedule template")
        return template

    def list_templates(
        self,
        course_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScheduleTemplate]:
        """List schedule templates.

        Args:
            course_type: Filter by course type
            is_active: Filter by active status
            skip: Skip N records
            limit: Limit results

        Returns:
            List of templates
        """
        if course_type:
            try:
                CourseType(course_type)
            except ValueError:
                raise ValidationError(f"Invalid course type: {course_type}")
            return self.schedule_repo.get_by_course_type(course_type, skip, limit)

        if is_active:
            return self.schedule_repo.get_active_templates(date.today(), skip, limit)

        return self.schedule_repo.get_all(skip, limit)

    def update_template(
        self,
        template_id: UUID,
        day_of_week: Optional[int] = None,
        start_time = None,
        end_time = None,
        course_type: Optional[str] = None,
        max_capacity: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> ScheduleTemplate:
        """Update template (creates new version if needed).

        When modifying a template, we create a new version to preserve history.
        The old template is marked with valid_to = today, and a new template
        is created with valid_from = tomorrow.

        Args:
            template_id: Template ID
            day_of_week: New day of week
            start_time: New start time
            end_time: New end time
            course_type: New course type
            max_capacity: New max capacity
            is_active: New active status

        Returns:
            Updated or new template
        """
        old_template = self.get_template(template_id)

        # If just changing is_active, update in place
        if is_active is not None and all(x is None for x in [day_of_week, start_time, end_time, course_type, max_capacity]):
            old_template.is_active = is_active
            return self.schedule_repo.update(old_template)

        # For other changes, create new version
        # Close old version
        old_template.valid_to = date.today()
        old_template.is_active = False
        self.schedule_repo.update(old_template)

        # Create new version
        try:
            new_course = CourseType(course_type) if course_type else old_template.course_type
        except ValueError:
            raise ValidationError(f"Invalid course type: {course_type}")

        try:
            new_dow = DayOfWeek(day_of_week) if day_of_week is not None else old_template.day_of_week
        except ValueError:
            raise ValidationError(f"Invalid day of week: {day_of_week}")

        new_template = ScheduleTemplate(
            day_of_week=new_dow,
            start_time=start_time or old_template.start_time,
            end_time=end_time or old_template.end_time,
            course_type=new_course,
            max_capacity=max_capacity or old_template.max_capacity,
            valid_from=date.today() + timedelta(days=1),
            professor_id=old_template.professor_id,
            version=old_template.version + 1
        )
        return self.schedule_repo.create(new_template)

    def delete_template(self, template_id: UUID) -> None:
        """Delete template (soft delete by marking inactive).

        Args:
            template_id: Template ID
        """
        template = self.get_template(template_id)
        template.is_active = False
        template.valid_to = date.today()
        self.schedule_repo.update(template)

    def get_templates_for_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[ScheduleTemplate]:
        """Get templates valid for a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of valid templates
        """
        return self.schedule_repo.get_valid_for_date_range(start_date, end_date)

    def get_templates_by_day(self, day: int) -> List[ScheduleTemplate]:
        """Get templates by day of week.

        Args:
            day: Day of week (0-6)

        Returns:
            List of templates
        """
        try:
            dow = DayOfWeek(day)
        except ValueError:
            raise ValidationError(f"Invalid day of week: {day}")
        return self.schedule_repo.get_by_day_of_week(dow, date.today())
