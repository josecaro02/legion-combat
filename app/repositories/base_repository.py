"""Base repository class."""
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extensions import db

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[T]):
        self.model = model

    @property
    def session(self) -> Session:
        """Get current database session."""
        return db.session

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Delete an entity."""
        self.session.delete(entity)
        self.session.commit()

    def delete_by_id(self, id: UUID) -> bool:
        """Delete entity by ID. Returns True if deleted, False if not found."""
        entity = self.get_by_id(id)
        if entity:
            self.delete(entity)
            return True
        return False

    def count(self) -> int:
        """Count total entities."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        return self.session.execute(stmt).scalar()
