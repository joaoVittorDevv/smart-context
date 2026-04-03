#!/usr/bin/env python3
"""
MCP Context Server - CLI Entry Point

Provides command-line interface for indexing and managing code context.
"""

import argparse
import sys
from pathlib import Path

from src.indexer.incremental import IncrementalIndexer
from src.database.connection import DatabaseConnection


def cmd_index(args):
    """Handle index command."""
    indexer = IncrementalIndexer(
        project_root=args.project_root,
        language=args.language
    )

    if args.full:
        print(f"🔄 Running full indexing of {args.project_root}...")
        stats = indexer.index_full(args.patterns)
    else:
        print(f"🔄 Running incremental indexing of {args.project_root}...")
        stats = indexer.index_incremental(args.patterns)

    print(f"\n✅ Indexing complete in {stats['time_ms']}ms")
    print(f"   Files indexed: {stats['files_indexed']}")
    print(f"   Symbols created: {stats['symbols_created']}")
    print(f"   Symbols updated: {stats['symbols_updated']}")
    print(f"   Dependencies created: {stats['dependencies_created']}")

    indexer.close()


def cmd_stats(args):
    """Handle stats command."""
    from src.database.connection import DatabaseConnection
    from src.database.repositories import RepositoryManager

    db = DatabaseConnection()
    db.create_tables()

    session = DatabaseConnection.get_session()
    repos = RepositoryManager(session)

    # Get statistics
    symbol_stats = repos.symbols.get_statistics()
    obs_stats = repos.observations.get_statistics()
    dep_count = repos.dependencies.count()

    print(f"\n📊 Context Database Statistics")
    print(f"   Symbols: {symbol_stats['total']} total")
    for stype, count in symbol_stats['by_type'].items():
        print(f"      - {stype}: {count}")
    print(f"   Dependencies: {dep_count}")
    print(f"   Observations: {obs_stats['total']} total")
    print(f"      - Active: {obs_stats['active']}")
    print(f"      - Stale: {obs_stats['stale']}")

    repos.close()


def cmd_init(args):
    """Handle init command."""
    db = DatabaseConnection(db_path=args.db_path)
    db.create_tables()
    print(f"✅ Database initialized at {db.db_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='MCP Context Server - Intelligent code context management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run main.py index                    # Incremental index current directory
  uv run main.py index --full              # Full re-index
  uv run main.py index --patterns "**/*.py" "**/*.js"
  uv run main.py stats                     # Show database statistics
  uv run main.py init                      # Initialize database
        """
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='MCP Context Server 0.1.0'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index code')
    index_parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Project root directory (default: current directory)'
    )
    index_parser.add_argument(
        '--language', '-l',
        type=str,
        default='python',
        help='Programming language (default: python)'
    )
    index_parser.add_argument(
        '--patterns',
        type=str,
        nargs='+',
        default=['**/*.py'],
        help='File patterns to index (default: "**/*.py")'
    )
    index_parser.add_argument(
        '--full',
        action='store_true',
        help='Perform full re-index instead of incremental'
    )

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Project root directory'
    )

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Custom database path'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'index':
        cmd_index(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'init':
        cmd_init(args)


if __name__ == '__main__':
    main()

