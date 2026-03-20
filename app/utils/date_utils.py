"""Date and time utilities."""
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterator


def get_current_datetime() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def get_current_date() -> date:
    """Get current UTC date."""
    return datetime.now(timezone.utc).date()


def get_current_time() -> time:
    """Get current UTC time."""
    return datetime.now(timezone.utc).time()


def date_range(start: date, end: date) -> Iterator[date]:
    """Generate dates from start to end (inclusive).

    Args:
        start: Start date
        end: End date

    Yields:
        Dates from start to end
    """
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def get_weekday_dates(start: date, end: date, weekday: int) -> list[date]:
    """Get all dates with a specific weekday in a range.

    Args:
        start: Start date
        end: End date
        weekday: Day of week (0=Monday, 6=Sunday)

    Returns:
        List of dates matching the weekday
    """
    return [d for d in date_range(start, end) if d.weekday() == weekday]


def add_months(date_obj: date, months: int) -> date:
    """Add months to a date.

    Args:
        date_obj: Starting date
        months: Number of months to add (can be negative)

    Returns:
        New date with months added
    """
    month = date_obj.month - 1 + months
    year = date_obj.year + month // 12
    month = month % 12 + 1
    day = min(date_obj.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30,
                              31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def start_of_day(date_obj: date) -> datetime:
    """Get datetime at start of day."""
    return datetime.combine(date_obj, time.min).replace(tzinfo=timezone.utc)


def end_of_day(date_obj: date) -> datetime:
    """Get datetime at end of day."""
    return datetime.combine(date_obj, time.max).replace(tzinfo=timezone.utc)


def parse_iso_date(date_str: str) -> date:
    """Parse ISO format date string."""
    return date.fromisoformat(date_str)


def parse_iso_datetime(datetime_str: str) -> datetime:
    """Parse ISO format datetime string."""
    return datetime.fromisoformat(datetime_str)
