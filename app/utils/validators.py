"""Validation utilities."""
import re
import uuid
from typing import Optional


# Phone number validation regex (international format)
PHONE_REGEX = re.compile(r'^[\+]?[1-9][\d]{0,15}$')

# Idempotency key validation
IDEMPOTENCY_KEY_REGEX = re.compile(r'^[a-zA-Z0-9_-]{10,64}$')


def validate_phone(phone: Optional[str]) -> bool:
    """Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return True  # Optional field
    return bool(PHONE_REGEX.match(phone))


def validate_idempotency_key(key: str) -> bool:
    """Validate idempotency key format.

    Args:
        key: Idempotency key to validate

    Returns:
        True if valid, False otherwise
    """
    if not key:
        return False
    return bool(IDEMPOTENCY_KEY_REGEX.match(key))


def generate_idempotency_key() -> str:
    """Generate a valid idempotency key.

    Returns:
        UUID-based idempotency key
    """
    return str(uuid.uuid4()).replace('-', '')


def validate_enum_value(value: str, enum_class) -> bool:
    """Validate that a value is a valid enum member.

    Args:
        value: Value to validate
        enum_class: Enum class to check against

    Returns:
        True if valid enum value, False otherwise
    """
    try:
        enum_class(value)
        return True
    except ValueError:
        return False
