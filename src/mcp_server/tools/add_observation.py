"""
MCP Tool: add_observation

Registers an observation/note about a code symbol.
"""

import json
import logging
from typing import Any

from src.security import SecurityValidator

logger = logging.getLogger(__name__)


async def handle_add_observation(arguments: dict, db) -> list[str]:
    """
    Handle add_observation tool call.

    Args:
        arguments: Tool arguments
        db: Database connection

    Returns:
        JSON string with result
    """
    # Validate arguments
    is_valid, error_msg = SecurityValidator.validate_tool_arguments('add_observation', arguments)
    if not is_valid:
        return [json.dumps({
            "error": f"Validation failed: {error_msg}"
        }, indent=2)]

    symbol_name = arguments.get('symbol_name')
    content = arguments.get('content')
    category = arguments.get('category')
    priority = arguments.get('priority', 3)

    # Sanitize content
    content = SecurityValidator.sanitize_string(content, max_length=5000)

    # Get session and repositories
    session = db.get_session()
    from src.database.repositories import RepositoryManager
    repos = RepositoryManager(session)

    # Check if symbol exists
    symbol = repos.symbols.find_by_name(symbol_name)

    if not symbol:
        repos.close()
        return [json.dumps({
            "error": f"Symbol '{symbol_name}' not found",
            "suggestion": f"Symbol must be indexed before adding observations. Run 'uv run main.py index' first."
        }, indent=2)]

    # Create observation
    try:
        observation = repos.observations.create_observation(
            symbol_id=symbol.id,
            note=content,
            category=category,
            priority=priority
        )

        repos.commit()

        result = {
            "success": True,
            "observation_id": observation.id,
            "symbol_name": symbol_name,
            "category": category,
            "priority": priority,
            "created_at": observation.created_at.isoformat() if observation.created_at else None,
            "message": f"Observation registered for symbol '{symbol_name}'"
        }

        repos.close()
        return [json.dumps(result, indent=2)]

    except Exception as e:
        repos.rollback()
        repos.close()
        logger.error(f"Error creating observation: {e}")
        return [json.dumps({
            "error": f"Failed to create observation: {str(e)}"
        }, indent=2)]
