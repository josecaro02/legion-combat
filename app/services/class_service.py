"""Class instance service."""
from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from app.exceptions.custom_exceptions import BusinessError, NotFoundError, ValidationError
from app.models.class_instance import ClassInstance, ClassStatus
from app.models.schedule import ScheduleTemplate
from app.models.student import CourseType
from app.repositories.class_repository import ClassRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.utils.date_utils import get_weekday_dates


class ClassService:
    """Service for class instance operations."""

    def __init__(
        self,
        class_repo: Optional[ClassRepository] = None,
        schedule_repo: Optional[ScheduleRepository] = None
    ):
        self.class_repo = class_repo or ClassRepository()
        self.schedule_repo = schedule_repo or ScheduleRepository()

    def create_instance(
        self,
        date_obj: date,
        start_time,
        end_time,
        course_type: str,
        max_capacity: int,
        professor_id: UUID,
        template_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> ClassInstance:
        """Create a class instance.

        Args:
            date_obj: Class date
            start_time: Start time
            end_time: End time
            course_type: Course type
            max_capacity: Maximum capacity
            professor_id: Professor ID
            template_id: Optional template ID
            notes: Optional notes

        Returns:
            Created class instance
        """
        # Validate course type
        try:
            course = CourseType(course_type)
        except ValueError:
            raise ValidationError(f"Invalid course type: {course_type}")

        # Validate times
        if start_time >= end_time:
            raise ValidationError("Start time must be before end time")

        # Validate template if provided
        if template_id:
            template = self.schedule_repo.get_by_id(template_id)
            if not template:
                raise NotFoundError("Schedule template")
            if not template.is_valid_for_date(date_obj):
                raise ValidationError("Template is not valid for the specified date")

        instance = ClassInstance(
            template_id=template_id,
            date=date_obj,
            start_time=start_time,
            end_time=end_time,
            course_type=course,
            max_capacity=max_capacity,
            professor_id=professor_id,
            notes=notes,
            status=ClassStatus.SCHEDULED
        )
        return self.class_repo.create(instance)

    def get_or_create_instance(
        self,
        template_id: UUID,
        date_obj: date
    ) -> ClassInstance:
        """Get or create a class instance from a template.

        Args:
            template_id: Template ID
            date_obj: Date for the instance

        Returns:
            Class instance
        """
        # Check if instance already exists
        existing = self.class_repo.get_by_template_and_date(template_id, date_obj)
        if existing:
            return existing

        # Get template
        template = self.schedule_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError("Schedule template")

        # Validate date
        if not template.is_valid_for_date(date_obj):
            raise ValidationError("Template is not valid for the specified date")

        # Create instance from template
        instance = ClassInstance(
            template_id=template_id,
            date=date_obj,
            start_time=template.start_time,
            end_time=template.end_time,
            course_type=template.course_type,
            max_capacity=template.max_capacity,
            professor_id=template.professor_id,
            status=ClassStatus.SCHEDULED
        )
        return self.class_repo.create(instance)

    def get_instance(self, instance_id: UUID) -> ClassInstance:
        """Get class instance by ID.

        Args:
            instance_id: Instance ID

        Returns:
            Class instance
        """
        instance = self.class_repo.get_by_id(instance_id)
        if not instance:
            raise NotFoundError("Class instance")
        return instance

    def get_instance_with_attendances(self, instance_id: UUID) -> ClassInstance:
        """Get class instance with attendances.

        Args:
            instance_id: Instance ID

        Returns:
            Class instance with attendances
        """
        instance = self.class_repo.get_with_attendances(instance_id)
        if not instance:
            raise NotFoundError("Class instance")
        return instance

    def list_instances(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        course_type: Optional[str] = None,
        status: Optional[str] = None,
        professor_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """List class instances with pagination.

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            course_type: Filter by course type
            status: Filter by status
            professor_id: Filter by professor
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        skip = (page - 1) * per_page

        if professor_id:
            instances = self.class_repo.get_by_professor(
                professor_id, start_date, end_date, skip, per_page
            )
        elif start_date and end_date:
            try:
                course = CourseType(course_type) if course_type else None
            except ValueError:
                raise ValidationError(f"Invalid course type: {course_type}")
            instances = self.class_repo.get_by_date_range(
                start_date, end_date, course, skip, per_page
            )
        elif status:
            try:
                status_enum = ClassStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")
            instances = self.class_repo.get_by_status(status_enum, start_date, skip, per_page)
        else:
            instances = self.class_repo.get_all(skip, per_page)

        total = len(instances)  # Approximate
        pages = (total + per_page - 1) // per_page

        return {
            'items': instances,
            'total': total,
            'pages': pages,
            'current_page': page
        }

    def get_classes_for_date_range(
        self,
        start_date: date,
        end_date: date,
        course_type: Optional[str] = None
    ) -> List[ClassInstance]:
        """Get or generate classes for a date range.

        This implements lazy generation of class instances from templates.

        Args:
            start_date: Start date
            end_date: End date
            course_type: Optional course type filter

        Returns:
            List of class instances
        """
        # Get valid templates for the range
        templates = self.schedule_repo.get_valid_for_date_range(start_date, end_date)

        instances = []
        for template in templates:
            # Filter by course type if specified
            if course_type and template.course_type.value != course_type:
                continue

            # Get dates for this template in the range
            template_start = max(start_date, template.valid_from)
            template_end = min(end_date, template.valid_to or end_date)

            for class_date in get_weekday_dates(
                template_start,
                template_end,
                template.day_of_week.value
            ):
                # Get or create instance
                instance = self.class_repo.get_by_template_and_date(template.id, class_date)
                if not instance:
                    instance = ClassInstance(
                        template_id=template.id,
                        date=class_date,
                        start_time=template.start_time,
                        end_time=template.end_time,
                        course_type=template.course_type,
                        max_capacity=template.max_capacity,
                        professor_id=template.professor_id,
                        status=ClassStatus.SCHEDULED
                    )
                    instance = self.class_repo.create(instance)
                instances.append(instance)

        # Sort by date and time
        instances.sort(key=lambda x: (x.date, x.start_time))
        return instances

    def update_instance(
        self,
        instance_id: UUID,
        start_time = None,
        end_time = None,
        status: Optional[str] = None,
        max_capacity: Optional[int] = None,
        professor_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> ClassInstance:
        """Update class instance.

        Args:
            instance_id: Instance ID
            start_time: New start time
            end_time: New end time
            status: New status
            max_capacity: New max capacity
            professor_id: New professor ID
            notes: New notes

        Returns:
            Updated instance
        """
        instance = self.get_instance(instance_id)

        if start_time is not None:
            instance.start_time = start_time
        if end_time is not None:
            instance.end_time = end_time
        if status is not None:
            try:
                instance.status = ClassStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")
        if max_capacity is not None:
            instance.max_capacity = max_capacity
        if professor_id is not None:
            instance.professor_id = professor_id
        if notes is not None:
            instance.notes = notes

        return self.class_repo.update(instance)

    def cancel_class(self, instance_id: UUID) -> ClassInstance:
        """Cancel a class.

        Args:
            instance_id: Instance ID

        Returns:
            Cancelled instance
        """
        return self.update_instance(instance_id, status=ClassStatus.CANCELLED.value)

    def start_class(self, instance_id: UUID) -> ClassInstance:
        """Mark class as in progress.

        Args:
            instance_id: Instance ID

        Returns:
            Updated instance
        """
        return self.update_instance(instance_id, status=ClassStatus.IN_PROGRESS.value)

    def complete_class(self, instance_id: UUID) -> ClassInstance:
        """Mark class as completed.

        Args:
            instance_id: Instance ID

        Returns:
            Updated instance
        """
        return self.update_instance(instance_id, status=ClassStatus.COMPLETED.value)

    def delete_instance(self, instance_id: UUID) -> None:
        """Delete class instance.

        Args:
            instance_id: Instance ID
        """
        instance = self.get_instance(instance_id)
        self.class_repo.delete(instance)
