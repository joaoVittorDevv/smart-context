"""
MCP Tool: get_project_summary

Retrieves project summary including statistics, recent changes, and status.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def handle_get_project_summary(arguments: dict, db) -> list[str]:
    """
    Handle get_project_summary tool call.

    Args:
        arguments: Tool arguments (empty)
        db: Database connection

    Returns:
        JSON string with project summary
    """
    # Get session and repositories
    session = db.get_session()
    from src.database.repositories import RepositoryManager
    repos = RepositoryManager(session)

    # Get statistics
    symbol_stats = repos.symbols.get_statistics()
    obs_stats = repos.observations.get_statistics()
    dep_count = repos.dependencies.count()

    # Get recent changes (symbols modified in last 24h)
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_symbols = session.query(repos.symbols.model_class).filter(
        repos.symbols.model_class.last_updated >= cutoff
    ).all()

    # Get included folders and project root
    included_folders = repos.metadata.get_included_folders()
    project_root = repos.metadata.get_project_root()

    recent_changes = []
    for symbol in recent_symbols[:10]:  # Last 10
        recent_changes.append({
            'name': symbol.name,
            'type': symbol.type,
            'file': symbol.file,
            'updated': symbol.last_updated.isoformat() if symbol.last_updated else None
        })

    # Read state.md for project status
    state_content = ""
    state_path = Path.cwd() / 'docs' / 'context' / 'state.md'
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                # Extract status line (first line after status header)
                for line in f:
                    if 'Status Geral' in line:
                        continue
                    if line.startswith('🟢') or line.startswith('🟡') or line.startswith('🔴'):
                        state_content = line.strip()
                        break
                    if state_content and not line.startswith('#'):
                        break
        except Exception as e:
            logger.warning(f"Could not read state.md: {e}")

    repos.close()

    # Build response
    result = {
        "project_status": state_content or "Status unknown",
        "statistics": {
            "symbols": {
                "total": symbol_stats['total'],
                "by_type": symbol_stats['by_type']
            },
            "dependencies": dep_count,
            "observations": {
                "total": obs_stats['total'],
                "active": obs_stats['active'],
                "stale": obs_stats['stale'],
                "by_category": obs_stats['by_category']
            }
        },
        "recent_changes": {
            "count": len(recent_changes),
            "items": recent_changes
        },
        "metadata": {
            "database_path": str(db.db_path),
            "project_root": project_root,
            "monitored_folders": included_folders,
            "last_indexed": datetime.utcnow().isoformat()
        },
        "suggestions": [
            "Use 'get_symbol_context(symbol_name)' to get details about a specific symbol",
            "Use 'add_observation(symbol_name, content)' to register notes about code",
            "Run 'uv run main.py index' to update the code index"
        ]
    }

    return [json.dumps(result, indent=2)]
