"""
MCP Context Server - Main server implementation.

This module provides the MCP server with STDIO communication.
"""

import logging
from pathlib import Path
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..database.connection import DatabaseConnection
from ..database.repositories import RepositoryManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.claude' / 'context.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Context Server implementation.

    Provides code context management through MCP protocol.
    """

    def __init__(self):
        """Initialize the MCP server."""
        self.app = Server("mcp-context")
        self.db = DatabaseConnection()
        self.db.create_tables()

        # Register tools
        self.app.list_tools()(self.list_tools)
        self.app.call_tool()(self.call_tool)

        logger.info("MCP Context Server initialized")

    async def list_tools(self) -> list[Tool]:
        """
        List available tools.

        Returns:
            List of tool definitions
        """
        return [
            Tool(
                name="get_symbol_context",
                description="Get complete context for a code symbol including its code, dependencies, and observations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol_name": {
                            "type": "string",
                            "description": "Name of the symbol to retrieve"
                        },
                        "include_docstring": {
                            "type": "boolean",
                            "description": "Include docstrings in the output (default: true)",
                            "default": True
                        }
                    },
                    "required": ["symbol_name"]
                }
            ),
            Tool(
                name="add_observation",
                description="Register an observation/note about a code symbol (e.g., bug, refactor idea, architecture note)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol_name": {
                            "type": "string",
                            "description": "Name of the symbol"
                        },
                        "content": {
                            "type": "string",
                            "description": "Observation content"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["bug", "refactor", "logic", "architecture"],
                            "description": "Category of the observation"
                        },
                        "priority": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Priority (1-5, default: 3)",
                            "default": 3
                        }
                    },
                    "required": ["symbol_name", "content"]
                }
            ),
            Tool(
                name="get_project_summary",
                description="Get project summary including statistics, recent changes, and current status",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Any) -> list[TextContent]:
        """
        Handle tool calls.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result as text content
        """
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "get_symbol_context":
            return await self._get_symbol_context(arguments)
        elif name == "add_observation":
            return await self._add_observation(arguments)
        elif name == "get_project_summary":
            return await self._get_project_summary(arguments)
        else:
            logger.error(f"Unknown tool: {name}")
            return [TextContent(f"Error: Unknown tool '{name}'")]

    async def _get_symbol_context(self, arguments: dict) -> list[TextContent]:
        """Handle get_symbol_context tool."""
        from .tools.get_symbol_context import handle_get_symbol_context
        return await handle_get_symbol_context(arguments, self.db)

    async def _add_observation(self, arguments: dict) -> list[TextContent]:
        """Handle add_observation tool."""
        from .tools.add_observation import handle_add_observation
        return await handle_add_observation(arguments, self.db)

    async def _get_project_summary(self, arguments: dict) -> list[TextContent]:
        """Handle get_project_summary tool."""
        from .tools.get_project_summary import handle_get_project_summary
        return await handle_get_project_summary(arguments, self.db)

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting MCP Context Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )


async def main():
    """Main entry point for the server."""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
