"""
Repository for Symbol entities.

Provides symbol-specific database operations.
"""

from sqlalchemy.orm import scoped_session
from typing import List, Optional
import uuid

from ..models import Symbol
from .base import BaseRepository


class SymbolRepository(BaseRepository[Symbol]):
    """Repository for Symbol entities."""

    def __init__(self, session: scoped_session):
        super().__init__(session, Symbol)

    def find_by_name(self, name: str) -> Optional[Symbol]:
        """Find symbol by name."""
        return self.session.query(Symbol).filter_by(name=name).first()

    def find_by_file(self, file_path: str) -> List[Symbol]:
        """Find all symbols in a file."""
        return self.session.query(Symbol).filter_by(file=file_path).all()

    def find_by_type(self, symbol_type: str) -> List[Symbol]:
        """Find symbols by type (class, function, method)."""
        return self.session.query(Symbol).filter_by(type=symbol_type).all()

    def upsert_batch(self, symbols_data: List[dict]) -> dict:
        """
        Create or update multiple symbols.

        Args:
            symbols_data: List of dictionaries with symbol data

        Returns:
            Dict with statistics about the operation
        """
        stats = {'created': 0, 'updated': 0}

        for symbol_data in symbols_data:
            name = symbol_data.get('name')
            existing = self.find_by_name(name) if name else None

            if existing:
                # Update existing symbol
                for key, value in symbol_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                stats['updated'] += 1
            else:
                # Create new symbol
                symbol = Symbol(
                    id=str(uuid.uuid4()),
                    **symbol_data
                )
                self.session.add(symbol)
                stats['created'] += 1

        return stats

    def delete_by_file(self, file_path: str) -> int:
        """
        Delete all symbols from a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of symbols deleted
        """
        count = self.session.query(Symbol).filter_by(file=file_path).count()
        self.session.query(Symbol).filter_by(file=file_path).delete()
        return count

    def mark_stale_by_file(self, file_path: str) -> int:
        """
        Mark all observations of symbols in a file as stale.

        This is called when a file is modified.

        Args:
            file_path: Path to the modified file

        Returns:
            Number of symbols affected
        """
        from ..models import Observation

        # Get all symbol IDs from the file
        symbols = self.find_by_file(file_path)
        symbol_ids = [s.id for s in symbols]

        # Mark all observations as stale
        count = self.session.query(Observation).filter(
            Observation.symbol_id.in_(symbol_ids)
        ).update({'is_stale': True}, synchronize_session=False)

        return count

    def get_statistics(self) -> dict:
        """Get statistics about symbols in the database."""
        from sqlalchemy import func

        total = self.count()
        by_type = self.session.query(
            Symbol.type,
            func.count(Symbol.id)
        ).group_by(Symbol.type).all()

        return {
            'total': total,
            'by_type': {t: c for t, c in by_type}
        }
