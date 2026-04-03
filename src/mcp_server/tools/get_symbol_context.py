"""
MCP Tool: get_symbol_context

Retrieves complete context for a code symbol including code,
dependencies, and observations.
"""

import json
import logging
from typing import Any

from src.security import SecurityValidator

logger = logging.getLogger(__name__)


async def handle_get_symbol_context(arguments: dict, db) -> list[str]:
    """
    Handle get_symbol_context tool call.

    Args:
        arguments: Tool arguments
        db: Database connection

    Returns:
        JSON string with symbol context
    """
    # Validate arguments
    is_valid, error_msg = SecurityValidator.validate_tool_arguments('get_symbol_context', arguments)
    if not is_valid:
        return [json.dumps({
            "error": f"Validation failed: {error_msg}"
        }, indent=2)]

    symbol_name = arguments.get('symbol_name')
    include_docstring = arguments.get('include_docstring', True)

    session = db.get_session()
    from src.database.repositories import RepositoryManager
    repos = RepositoryManager(session)

    # Get symbol
    symbol = repos.symbols.find_by_name(symbol_name)

    if not symbol:
        repos.close()
        return [json.dumps({
            "error": f"Symbol '{symbol_name}' not found",
            "suggestion": f"Use 'get_project_summary' to see all indexed symbols"
        }, indent=2)]

    # Get dependencies (1-Level Reach)
    deps_graph = repos.dependencies.get_dependency_graph(symbol.id, depth=1)

    # Get outgoing dependencies (what this symbol calls)
    outgoing = []
    for dep in deps_graph.get('outgoing', []):
        callee = repos.symbols.get_by_id(dep['id'])
        if callee:
            outgoing.append({
                'name': callee.name,
                'type': callee.type,
                'signature': callee.signature or '',
                'line': dep.get('line')
            })

    # Get incoming dependencies (what calls this symbol)
    incoming = []
    for dep in deps_graph.get('incoming', []):
        caller = repos.symbols.get_by_id(dep['id'])
        if caller:
            incoming.append({
                'name': caller.name,
                'type': caller.type,
                'file': caller.file
            })

    # Get observations (top 5 active, non-stale)
    observations = repos.observations.find_active_by_symbol(
        symbol.id,
        limit=5
    )

    obs_data = []
    for obs in observations:
        obs_data.append({
            'note': obs.note,
            'category': obs.category,
            'priority': obs.priority,
            'created_at': obs.created_at.isoformat() if obs.created_at else None
        })

    # Build suggested queries based on dependencies
    suggested_queries = []
    for dep in outgoing[:3]:  # Top 3
        suggested_queries.append(f"get_symbol_context('{dep['name']}')")
    for caller in incoming[:2]:  # Top 2 callers
        suggested_queries.append(f"get_symbol_context('{caller['name']}')")

    repos.close()

    # Build response
    result = {
        'symbol': {
            'name': symbol.name,
            'type': symbol.type,
            'file': symbol.file,
            'signature': symbol.signature or '',
            'body': symbol.body or '',  # Full body for target
            'start_line': symbol.start_line,
            'end_line': symbol.end_line,
            'last_updated': symbol.last_updated.isoformat() if symbol.last_updated else None
        },
        'outgoing_dependencies': outgoing,  # Signatures only (payload asymmetric)
        'incoming_dependencies': incoming,  # Names and files only
        'observations': obs_data,
        'suggested_queries': suggested_queries,
        'metadata': {
            'total_symbols': repos.symbols.count(),
            'has_observations': len(obs_data) > 0,
            'is_stale': False  # TODO: implement staleness check
        }
    }

    return [json.dumps(result, indent=2)]
