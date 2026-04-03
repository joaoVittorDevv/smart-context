"""
Repository manager for easy access to all repositories.

This module provides a unified interface for database operations.
"""

from .base import BaseRepository
from .symbol_repo import SymbolRepository
from .dependency_repo import DependencyRepository
from .observation_repo import ObservationRepository


class RepositoryManager:
    """
    Manages all repositories and provides easy access.

    Usage:
        manager = RepositoryManager(session)
        symbols = manager.symbols.find_by_name('MyFunction')
    """

    def __init__(self, session):
        """
        Initialize repository manager.

        Args:
            session: SQLAlchemy scoped session
        """
        self.session = session
        self.symbols = SymbolRepository(session)
        self.dependencies = DependencyRepository(session)
        self.observations = ObservationRepository(session)

    def commit(self):
        """Commit pending changes."""
        self.session.commit()

    def rollback(self):
        """Rollback pending changes."""
        self.session.rollback()

    def close(self):
        """Close the session."""
        self.session.close()


__all__ = [
    'BaseRepository',
    'SymbolRepository',
    'DependencyRepository',
    'ObservationRepository',
    'RepositoryManager'
]
