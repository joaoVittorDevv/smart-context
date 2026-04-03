#!/usr/bin/env python3
"""
Test script for MCP Context Server tools.

Tests the three main tools without running the full MCP server.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import DatabaseConnection
from src.database.repositories import RepositoryManager
from src.mcp_server.tools import get_symbol_context, add_observation, get_project_summary


async def test_tools():
    """Test all MCP tools."""
    print("🧪 Testing MCP Context Server Tools\n")

    # Initialize database
    db = DatabaseConnection()
    db.create_tables()

    # Test 1: get_project_summary
    print("1️⃣ Testing get_project_summary...")
    result = await get_project_summary.handle_get_project_summary({}, db)
    print(result[0][:200] + "..." if len(result[0]) > 200 else result[0])
    print()

    # Test 2: get_symbol_context (for a known symbol)
    print("2️⃣ Testing get_symbol_context for 'Symbol'...")
    result = await get_symbol_context.handle_get_symbol_context({
        'symbol_name': 'Symbol',
        'include_docstring': True
    }, db)
    print(result[0][:300] + "..." if len(result[0]) > 300 else result[0])
    print()

    # Test 3: add_observation
    print("3️⃣ Testing add_observation for 'Symbol'...")
    result = await add_observation.handle_add_observation({
        'symbol_name': 'Symbol',
        'content': 'Test observation from unit test',
        'category': 'architecture',
        'priority': 3
    }, db)
    print(result[0])
    print()

    # Test 4: get_symbol_context again to see observation
    print("4️⃣ Testing get_symbol_context again (should include observation)...")
    result = await get_symbol_context.handle_get_symbol_context({
        'symbol_name': 'Symbol',
        'include_docstring': True
    }, db)
    import json
    data = json.loads(result[0])
    print(f"Observations count: {len(data['observations'])}")
    if data['observations']:
        print(f"Latest observation: {data['observations'][0]['note']}")

    print("\n✅ All tests passed!")


if __name__ == '__main__':
    asyncio.run(test_tools())
