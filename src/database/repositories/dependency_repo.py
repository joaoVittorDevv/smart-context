"""
Repository for Dependency entities.

Provides dependency-specific database operations.
"""

from sqlalchemy.orm import scoped_session
from typing import List
import uuid

from ..models import Dependency
from .base import BaseRepository


class DependencyRepository(BaseRepository[Dependency]):
    """Repository for Dependency entities."""

    def __init__(self, session: scoped_session):
        super().__init__(session, Dependency)

    def find_by_caller(self, caller_id: str) -> List[Dependency]:
        """Find all dependencies from a caller symbol."""
        return self.session.query(Dependency).filter_by(caller_id=caller_id).all()

    def find_by_callee(self, callee_id: str) -> List[Dependency]:
        """Find all dependencies to a callee symbol."""
        return self.session.query(Dependency).filter_by(callee_id=callee_id).all()

    def create_batch(self, dependencies_data: List[dict]) -> int:
        """
        Create multiple dependencies.

        Args:
            dependencies_data: List of dictionaries with dependency data

        Returns:
            Number of dependencies created
        """
        for dep_data in dependencies_data:
            if 'id' not in dep_data:
                dep_data['id'] = str(uuid.uuid4())
            dependency = Dependency(**dep_data)
            self.session.add(dependency)

        return len(dependencies_data)

    def delete_by_file(self, file_path: str) -> int:
        """
        Delete all dependencies from symbols in a file.

        Args:
            file_path: Path to the file

        Returns:
            Number of dependencies deleted
        """
        from ..models import Symbol

        # Get all symbol IDs from the file
        symbol_ids = [s.id for s in self.session.query(Symbol.id).filter_by(file=file_path).all()]

        # Delete dependencies where caller is in the file
        count = self.session.query(Dependency).filter(
            Dependency.caller_id.in_(symbol_ids)
        ).delete(synchronize_session=False)

        return count

    def get_dependency_graph(self, symbol_id: str, depth: int = 1) -> dict:
        """
        Get dependency graph for a symbol.

        Args:
            symbol_id: ID of the symbol
            depth: Depth of traversal (1 = direct dependencies only)

        Returns:
            Dict with 'outgoing' and 'incoming' dependencies
        """
        result = {
            'outgoing': [],
            'incoming': []
        }

        if depth >= 1:
            # Direct outgoing dependencies (what this symbol calls)
            outgoing = self.session.query(Dependency).filter_by(caller_id=symbol_id).all()
            for dep in outgoing:
                result['outgoing'].append({
                    'id': dep.callee_id,
                    'line': dep.call_site_line
                })

            # Direct incoming dependencies (what calls this symbol)
            incoming = self.session.query(Dependency).filter_by(callee_id=symbol_id).all()
            for dep in incoming:
                result['incoming'].append({
                    'id': dep.caller_id
                })

        return result
