#!/bin/bash
# MCP Context Server - Installation Script
# This script installs the package locally and configures integration

set -e

echo "🚀 MCP Context Server - Installation"
echo "======================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Get the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📂 Project root: $PROJECT_ROOT"

# Install the package in editable mode
echo "📦 Installing package..."
uv pip install -e "$PROJECT_ROOT"

# Create .claude directory if it doesn't exist
CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"

# Invoke interactive initialization wizard
echo "🧭 Starting project initialization Wizard..."
uv run python "$PROJECT_ROOT/main.py" init

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Available commands:"
echo "   mcp-context           - CLI for indexing and stats"
echo "   mcp-context-server    - MCP server (for Claude integration)"
echo ""
echo "🔧 Next steps:"
echo ""
echo "1. For Claude Desktop, add to your config:"
echo ""
echo "   {"
echo "     \"mcpServers\": {"
echo "       \"mcp-context\": {"
echo "         \"command\": \"mcp-context-server\","
echo "         \"env\": {"
echo "           \"PROJECT_ROOT\": \"$PROJECT_ROOT\""
echo "         }"
echo "       }"
echo "     }"
echo "   }"
echo ""
echo "2. For Claude Code, add to CLAUDE.md or settings.json:"
echo ""
echo "   mcpServers:"
echo "     - name: mcp-context"
echo "       command: mcp-context-server"
echo ""
echo "💡 Tip: If you cloned this repo into a .mcp/ folder, "
echo "the wizard has already correctly pointed the indexing to your parent folder!"
echo ""
echo "3. Index your code:"
echo "   mcp-context index --full"
echo ""
