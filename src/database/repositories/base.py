"""
Base repository with generic CRUD operations.

This module provides a generic repository pattern for database operations.
"""

from sqlalchemy.orm import scoped_session
from typing import TypeVar, Generic, Optional, List
import uuid

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic repository with CRUD operations.

    Provides common database operations for all entities.
    """

    def __init__(self, session: scoped_session, model_class: type):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy scoped session
            model_class: Model class this repository manages
        """
        self.session = session
        self.model_class = model_class

    def get_by_id(self, id: str) -> Optional[T]:
        """Find entity by ID."""
        return self.session.query(self.model_class).filter_by(id=id).first()

    def get_all(self) -> List[T]:
        """Get all entities."""
        return self.session.query(self.model_class).all()

    def create(self, entity: T) -> T:
        """Create new entity."""
        if hasattr(entity, 'id') and not entity.id:
            entity.id = str(uuid.uuid4())
        self.session.add(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update existing entity."""
        self.session.merge(entity)
        return entity

    def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        entity = self.get_by_id(id)
        if entity:
            self.session.delete(entity)
            return True
        return False

    def count(self) -> int:
        """Count all entities."""
        return self.session.query(self.model_class).count()

    def delete_all(self) -> int:
        """Delete all entities. Returns count of deleted records."""
        count = self.count()
        self.session.query(self.model_class).delete()
        return count
