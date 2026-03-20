"""User service."""
from typing import List, Optional
from uuid import UUID

from app.exceptions.custom_exceptions import NotFoundError, ValidationError
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.utils.password_utils import hash_password, verify_password


class UserService:
    """Service for user operations."""

    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str
    ) -> User:
        """Create a new user.

        Args:
            email: User email
            password: Plain text password
            first_name: First name
            last_name: Last name
            role: User role (owner or professor)

        Returns:
            Created user

        Raises:
            ValidationError: If email already exists or role is invalid
        """
        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            raise ValidationError(f"Invalid role: {role}")

        # Check email uniqueness
        if self.user_repo.exists_by_email(email):
            raise ValidationError(f"Email already registered: {email}")

        # Create user
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=user_role
        )
        return self.user_repo.create(user)

    def get_user(self, user_id: UUID) -> User:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User

        Raises:
            NotFoundError: If user not found
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User")
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User or None
        """
        return self.user_repo.get_by_email(email)

    def list_users(
        self,
        role: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        """List users with pagination.

        Args:
            role: Filter by role
            page: Page number
            per_page: Items per page

        Returns:
            Dictionary with items, total, pages, current_page
        """
        skip = (page - 1) * per_page

        if role:
            users = self.user_repo.get_by_role(role, skip, per_page)
            total = self.user_repo.count_by_role(role)
        else:
            users = self.user_repo.get_all(skip, per_page)
            total = self.user_repo.count()

        pages = (total + per_page - 1) // per_page

        return {
            'items': users,
            'total': total,
            'pages': pages,
            'current_page': page
        }

    def update_user(
        self,
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """Update user.

        Args:
            user_id: User ID
            first_name: New first name
            last_name: New last name
            is_active: New active status

        Returns:
            Updated user
        """
        user = self.get_user(user_id)

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if is_active is not None:
            user.is_active = is_active

        return self.user_repo.update(user)

    def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> None:
        """Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Raises:
            ValidationError: If old password is incorrect
        """
        user = self.get_user(user_id)

        if not verify_password(old_password, user.password_hash):
            raise ValidationError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        self.user_repo.update(user)

    def reset_password(self, user_id: UUID, new_password: str) -> None:
        """Reset user password (admin only).

        Args:
            user_id: User ID
            new_password: New password
        """
        user = self.get_user(user_id)
        user.password_hash = hash_password(new_password)
        self.user_repo.update(user)

    def delete_user(self, user_id: UUID) -> None:
        """Delete user.

        Args:
            user_id: User ID
        """
        user = self.get_user(user_id)
        self.user_repo.delete(user)
