"""
Database connection management for MCP Context Server.

This module provides thread-safe connection management for SQLite database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    """
    Singleton database connection manager.

    Provides thread-safe session management and automatic
    database initialization.
    """

    _instance: Optional['DatabaseConnection'] = None
    _session_factory = None

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        # Only initialize once
        if hasattr(self, '_initialized'):
            return

        if db_path is None:
            db_path = Path.home() / '.claude' / 'context.db'

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine with thread safety
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            connect_args={'check_same_thread': False},
            echo=False
        )

        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        DatabaseConnection._session_factory = scoped_session(session_factory)

        self._initialized = True

    def create_tables(self):
        """Create all tables if they don't exist."""
        from .models import Base
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        from .models import Base
        Base.metadata.drop_all(self.engine)

    @classmethod
    def get_session(cls):
        """
        Get a thread-scoped database session.

        Returns:
            scoped_session: Thread-safe SQLAlchemy session
        """
        if cls._session_factory is None:
            cls()
        return cls._session_factory()

    @classmethod
    def close_session(cls):
        """Close the current thread's session."""
        if cls._session_factory is not None:
            cls._session_factory.remove()


# Global singleton instance
db_connection = DatabaseConnection()
