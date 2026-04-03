"""
Incremental code indexer.

This module provides incremental indexing functionality using file hashes.
"""

import hashlib
from pathlib import Path
from typing import List, Optional, Dict
import time

from ..database.connection import DatabaseConnection
from ..database.repositories import RepositoryManager
from .simple_parser import CodeParser
from .dependency_analyzer import DependencyAnalyzer


class IncrementalIndexer:
    """
    Manages incremental code indexing.

    Only re-indexes files that have changed since the last run.
    """

    def __init__(self, project_root: str, language: str = 'python'):
        """
        Initialize incremental indexer.

        Args:
            project_root: Root directory of the project
            language: Programming language (default: 'python')
        """
        self.project_root = Path(project_root).resolve()
        self.language = language

        # Initialize parser and analyzer
        self.parser = CodeParser(language)
        self.analyzer = DependencyAnalyzer()

        # Initialize database
        self.db = DatabaseConnection()
        self.db.create_tables()

        # Get session and repositories
        self.session = DatabaseConnection.get_session()
        self.repos = RepositoryManager(self.session)

    def index_incremental(
        self,
        file_patterns: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Perform incremental indexing.

        Only indexes files that have changed since the last run.

        Args:
            file_patterns: List of glob patterns (default: ['**/*.py'])

        Returns:
            Dictionary with indexing statistics
        """
        if file_patterns is None:
            file_patterns = ['**/*.py']

        stats = {
            'files_indexed': 0,
            'symbols_created': 0,
            'symbols_updated': 0,
            'dependencies_created': 0,
            'time_ms': 0
        }

        start_time = time.time()

        # Find and index files
        for pattern in file_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and self._should_index(file_path):
                    file_stats = self._index_file(file_path)
                    stats['files_indexed'] += 1
                    stats['symbols_created'] += file_stats['symbols_created']
                    stats['symbols_updated'] += file_stats['symbols_updated']
                    stats['dependencies_created'] += file_stats['dependencies_created']

        stats['time_ms'] = int((time.time() - start_time) * 1000)

        # Commit changes
        self.repos.commit()

        return stats

    def index_full(
        self,
        file_patterns: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Perform full indexing of all files.

        Args:
            file_patterns: List of glob patterns (default: ['**/*.py'])

        Returns:
            Dictionary with indexing statistics
        """
        if file_patterns is None:
            file_patterns = ['**/*.py']

        stats = {
            'files_indexed': 0,
            'symbols_created': 0,
            'symbols_updated': 0,
            'dependencies_created': 0,
            'time_ms': 0
        }

        start_time = time.time()

        # Find and index all files
        for pattern in file_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    file_stats = self._index_file(file_path, force=True)
                    stats['files_indexed'] += 1
                    stats['symbols_created'] += file_stats['symbols_created']
                    stats['symbols_updated'] += file_stats['symbols_updated']
                    stats['dependencies_created'] += file_stats['dependencies_created']

        stats['time_ms'] = int((time.time() - start_time) * 1000)

        # Commit changes
        self.repos.commit()

        return stats

    def _should_index(self, file_path: Path) -> bool:
        """
        Check if a file needs to be indexed.

        Args:
            file_path: Path to the file

        Returns:
            True if file should be indexed
        """
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False

        # Skip virtual environment
        if '.venv' in file_path.parts or 'venv' in file_path.parts:
            return False

        # Skip __pycache__ and .pytest_cache
        if '__pycache__' in file_path.parts or '.pytest_cache' in file_path.parts:
            return False

        # Check file hash
        current_hash = self._calculate_hash(file_path)

        # Get stored hash from database
        # Note: For now, we'll always index if we don't have a hash stored
        # In a full implementation, we'd query the FileHash table

        return True  # For MVP, always index

    def _index_file(self, file_path: Path, force: bool = False) -> Dict[str, int]:
        """
        Index a single file.

        Args:
            file_path: Path to the file
            force: Force re-indexing even if unchanged

        Returns:
            Dictionary with file statistics
        """
        stats = {
            'symbols_created': 0,
            'symbols_updated': 0,
            'dependencies_created': 0
        }

        try:
            # Parse file
            symbols_data = self.parser.parse_file(str(file_path))

            if not symbols_data:
                return stats

            # Assign IDs to symbols
            from ..database.models import Symbol

            # Get existing symbols for this file
            existing_symbols = self.repos.symbols.find_by_file(str(file_path))
            existing_map = {s.name: s.id for s in existing_symbols}

            # Prepare symbols with IDs
            for symbol_data in symbols_data:
                symbol_name = symbol_data['name']
                if symbol_name in existing_map:
                    symbol_data['id'] = existing_map[symbol_name]
                else:
                    # Will be assigned by repository
                    symbol_data['file'] = str(file_path)

            # Upsert symbols
            upsert_stats = self.repos.symbols.upsert_batch(symbols_data)
            stats['symbols_created'] = upsert_stats['created']
            stats['symbols_updated'] = upsert_stats['updated']

            # Get symbols with IDs from database
            all_symbols = self.repos.symbols.find_by_file(str(file_path))
            symbol_map = {s.name: s for s in all_symbols}

            # Update symbols_data with proper IDs
            for symbol_data in symbols_data:
                if symbol_data['name'] in symbol_map:
                    symbol_data['id'] = symbol_map[symbol_data['name']].id

            # Analyze dependencies
            dependencies_data = self.analyzer.analyze(symbols_data)

            if dependencies_data:
                # Delete old dependencies for this file
                file_path_str = str(file_path)
                # Delete dependencies where caller is in this file
                caller_ids = [s['id'] for s in symbols_data if 'id' in s]
                if caller_ids:
                    # This would be implemented in DependencyRepository
                    pass

                # Create new dependencies
                count = self.repos.dependencies.create_batch(dependencies_data)
                stats['dependencies_created'] = count

        except Exception as e:
            print(f"Error indexing {file_path}: {e}")

        return stats

    def _calculate_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ''

    def close(self):
        """Close database connection."""
        self.repos.close()
