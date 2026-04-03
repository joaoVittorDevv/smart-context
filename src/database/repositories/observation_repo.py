"""
Repository for Observation entities.

Provides observation-specific database operations.
"""

from sqlalchemy.orm import scoped_session
from typing import List, Optional
import uuid

from ..models import Observation
from .base import BaseRepository


class ObservationRepository(BaseRepository[Observation]):
    """Repository for Observation entities."""

    def __init__(self, session: scoped_session):
        super().__init__(session, Observation)

    def find_by_symbol(self, symbol_id: str) -> List[Observation]:
        """Find all observations for a symbol."""
        return self.session.query(Observation).filter_by(symbol_id=symbol_id).all()

    def find_active_by_symbol(self, symbol_id: str, limit: int = 5) -> List[Observation]:
        """
        Find active (non-stale) observations for a symbol.

        Args:
            symbol_id: ID of the symbol
            limit: Maximum number of observations to return

        Returns:
            List of active observations, sorted by priority and date
        """
        return self.session.query(Observation).filter(
            Observation.symbol_id == symbol_id,
            Observation.is_stale == False
        ).order_by(
            Observation.priority.desc(),
            Observation.created_at.desc()
        ).limit(limit).all()

    def find_stale(self) -> List[Observation]:
        """Find all stale observations."""
        return self.session.query(Observation).filter_by(is_stale=True).all()

    def mark_stale(self, observation_id: str) -> bool:
        """Mark an observation as stale."""
        obs = self.get_by_id(observation_id)
        if obs:
            obs.is_stale = True
            return True
        return False

    def mark_fresh(self, observation_id: str) -> bool:
        """Mark a stale observation as fresh."""
        obs = self.get_by_id(observation_id)
        if obs:
            obs.is_stale = False
            return True
        return False

    def create_observation(
        self,
        symbol_id: str,
        note: str,
        category: Optional[str] = None,
        priority: int = 3,
        session_id: Optional[str] = None
    ) -> Observation:
        """
        Create a new observation.

        Args:
            symbol_id: ID of the symbol
            note: Observation text
            category: Category (bug, refactor, logic, architecture)
            priority: Priority (1-5, default 3)
            session_id: Optional session identifier

        Returns:
            Created observation
        """
        observation = Observation(
            id=str(uuid.uuid4()),
            symbol_id=symbol_id,
            note=note,
            category=category,
            priority=priority,
            session_id=session_id
        )
        self.session.add(observation)
        return observation

    def delete_stale(self) -> int:
        """Delete all stale observations."""
        count = self.session.query(Observation).filter_by(is_stale=True).count()
        self.session.query(Observation).filter_by(is_stale=True).delete()
        return count

    def get_statistics(self) -> dict:
        """Get statistics about observations."""
        from sqlalchemy import func

        total = self.count()
        stale = self.session.query(func.count(Observation.id)).filter(
            Observation.is_stale == True
        ).scalar()
        active = total - stale

        by_category = self.session.query(
            Observation.category,
            func.count(Observation.id)
        ).group_by(Observation.category).all()

        return {
            'total': total,
            'active': active,
            'stale': stale,
            'by_category': {c or 'uncategorized': count for c, count in by_category}
        }
