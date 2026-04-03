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
from src.database.repositories import RepositoryManager
import questionary
import json
import os
from collections import Counter


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
    """Handle init command with interactive wizard."""
    db = DatabaseConnection(db_path=args.db_path)
    db.create_tables()
    session = DatabaseConnection.get_session()
    repos = RepositoryManager(session)

    print(f"✅ Database initialized at {db.db_path}")

    # Determine project root
    # If we are in project/.mcp/, the root is project/
    current_path = Path.cwd().resolve()
    if current_path.name == '.mcp' or (current_path / 'src' / 'database').exists():
        # We are likely inside the context server directory
        # If it's a hidden .mcp folder, go up one level
        if current_path.name == '.mcp':
            project_root = current_path.parent
        else:
            # Maybe it's just the cloned repo, assume parent is the project target
            project_root = current_path.parent
    else:
        project_root = current_path

    print(f"📂 Project Root identified as: {project_root}")

    # Discovery of folders
    exclude_folders = {'.git', 'node_modules', '__pycache__', '.venv', '.mcp', '.pytest_cache', 'dist', 'build'}
    available_folders = []
    
    for item in project_root.iterdir():
        if item.is_dir() and item.name not in exclude_folders and not item.name.startswith('.'):
            available_folders.append(item.name)

    if not available_folders:
        print("⚠️ No subdirectories found in project root to index.")
        repos.metadata.set_included_folders([])
        repos.metadata.set_project_root(str(project_root))
        repos.commit()
        return

    # Interactive Checklist
    selected_folders = questionary.checkbox(
        "Select folders to monitor and index:",
        choices=[
            questionary.Choice(folder, checked=True if folder in ('src', 'app', 'lib', 'packages') else False)
            for folder in sorted(available_folders)
        ]
    ).ask()

    if selected_folders is None:
        print("❌ Initialization cancelled.")
        return

    # --- Discovery Preview (Dry-Run) ---
    print("\n🔍 Scanning selected folders for a preview...")
    extensions_found = Counter()
    total_files = 0
    
    supported_exts = {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.java', '.cpp', '.hpp', '.h'}
    
    for folder in selected_folders:
        folder_path = project_root / folder
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_exts:
                if not any(part.startswith('.') or part == 'node_modules' for part in file_path.parts):
                    extensions_found[file_path.suffix] += 1
                    total_files += 1

    print("\n" + "="*40)
    print("📋 DISCOVERY PREVIEW (Dry-Run)")
    print("="*40)
    print(f"📂 Folders: {', '.join(selected_folders)}")
    print(f"📄 Potential files to index: {total_files}")
    print("-" * 40)
    if extensions_found:
        print("🌐 Languages detected:")
        for ext, count in sorted(extensions_found.items(), key=lambda x: x[1], reverse=True):
            lang_label = ext[1:].upper()
            print(f"   • {lang_label}: {count} files")
    else:
        print("⚠️ No supported source files found in the selected folders.")
    print("="*40 + "\n")

    confirm_start = questionary.confirm(
        "Everything looks correct? Do you want to save and start the FULL indexing now?",
        default=True
    ).ask()

    if not confirm_start:
        print("💾 Configuration NOT saved. Initialization aborted.")
        return

    # Save to database
    repos.metadata.set_included_folders(selected_folders)
    repos.metadata.set_project_root(str(project_root))
    repos.commit()

    print(f"\n✨ Configuration Saved!")
    
    # Trigger full index immediately
    print(f"🚀 Starting FULL indexing of {len(selected_folders)} folders...")
    indexer = IncrementalIndexer(project_root=str(project_root))
    stats = indexer.index_full()
    
    print(f"\n✅ Initial indexing complete in {stats['time_ms']}ms")
    print(f"   Files indexed: {stats['files_indexed']}")
    print(f"   Symbols found: {stats['symbols_created']}")

    repos.close()


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

