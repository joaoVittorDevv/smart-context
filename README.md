# MCP Context Server

> **Intelligent code context management using the Model Context Protocol (MCP)**

A local-first, token-efficient code context server that transforms your codebase into a searchable knowledge graph. Designed for AI assistants (Claude, Copilot, etc.) to provide **precise context** without wasting tokens.

## 🎯 Features

- **Token-efficient:** Reduces context payload from ~18k to <2.5k tokens
- **Ultra-fast indexing:** < 100ms incremental indexing (tested: 84ms for 17 files)
- **Local-first:** 100% offline, no API dependencies
- **Smart context retrieval:** 1-Level Reach, asymmetric payload, Top 5 insights
- **Multi-agent ready:** Works with Claude, Copilot, and any MCP-compatible tool
- **Easy installation:** One-command setup with automated scripts

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (ultra-fast Python package manager)

### Installation

#### Option 1: Automated Installation (Recommended)

**Linux/macOS:**
```bash
git clone <repo-url>
cd mcp_context
./install.sh
```

**Windows (PowerShell):**
```powershell
git clone <repo-url>
cd mcp_context
.\install.ps1
```

The script will:
- ✅ Verify `uv` is installed
- ✅ Install the package in editable mode
- ✅ Create necessary directories
- ✅ Display integration instructions

#### Option 2: Manual Installation

```bash
# Clone the repository
git clone <repo-url>
cd mcp_context

# Install in editable mode
uv pip install -e .

# Initialize database
mcp-context init

# Index your code
mcp-context index
```

### Available Commands

After installation, two commands are available globally:

```bash
# CLI for indexing and statistics
mcp-context index              # Incremental indexing
mcp-context index --full       # Full re-indexing
mcp-context stats              # Database statistics
mcp-context init               # Initialize database

# MCP server for Claude integration
mcp-context-server             # Start MCP server
```

## 📖 Usage

### Command Line Interface

The `mcp-context` command provides all functionality:

```bash
# Incremental indexing (fast - only changed files)
mcp-context index

# Full re-indexing
mcp-context index --full

# View database statistics
mcp-context stats

# Index specific file patterns
mcp-context index --patterns "**/*.py" "**/*.js"

# Specify project root
mcp-context index --project-root /path/to/project

# Initialize new database
mcp-context init --db-path /custom/path/context.db
```

### MCP Tools

The server provides 3 tools via MCP protocol:

#### 1. `get_symbol_context`
Get complete context for a code symbol including its code, dependencies, and observations.

**Input:**
```json
{
  "symbol_name": "MyClass",
  "include_docstring": true
}
```

**Output:**
- Symbol code (full body)
- Outgoing dependencies (signatures only)
- Incoming dependencies (names and files)
- Top 5 active observations
- Suggested queries

#### 2. `add_observation`
Register a note about a symbol (bug, refactor idea, architecture note).

**Input:**
```json
{
  "symbol_name": "MyClass",
  "content": "TODO: Refactor this method to use async/await",
  "category": "refactor",
  "priority": 3
}
```

**Categories:** `bug`, `refactor`, `logic`, `architecture`

#### 3. `get_project_summary`
Get project statistics, recent changes, and current status.

**Input:** (empty)

**Output:**
- Symbol statistics (total, by type)
- Dependency count
- Observation statistics
- Recent changes (last 24h)
- Project status from `state.md`

## 🔧 Configuration

### Project Structure

```
mcp_context/
├── src/
│   ├── database/          # SQLAlchemy models + repositories
│   ├── indexer/           # Code parser + dependency analyzer
│   ├── mcp_server/       # MCP server + tools
│   └── security.py       # Security validations
├── .claude/
│   ├── hooks/             # Automatic session hooks
│   ├── context.db         # SQLite database (auto-created)
│   └── context.log        # Server logs
├── docs/
│   ├── context/           # Persistent memory (state, journal, decisions)
│   └── INSTALLATION.md    # Installation guide
├── main.py                # CLI entry point
├── install.sh             # Installation script (Linux/macOS)
├── install.ps1            # Installation script (Windows)
└── pyproject.toml         # Dependencies and entry points
```

### Environment Variables

- `PROJECT_ROOT`: Project root directory (default: current directory)
- `DB_PATH`: Custom database path (default: `~/.claude/context.db`)

### Installed Commands

After installation, the following commands are available globally:

| Command | Purpose |
|---------|---------|
| `mcp-context` | CLI for indexing, stats, and database management |
| `mcp-context-server` | MCP server for Claude integration |

## 🔐 Security

- **Path Traversal Protection:** All file paths validated against project root
- **SQL Injection Prevention:** Input sanitization and pattern detection
- **Input Validation:** Length limits, character filtering, type checking
- **Git Safety:** `context.db` automatically excluded from version control

## 📊 Architecture

### The 4 Golden Rules (Heuristics)

1. **1-Level Reach:** Don't expand dependencies recursively
2. **Asymmetric Payload:** Full body for target, signatures only for neighbors
3. **Top 5 Insights:** Limit observations to most relevant
4. **Directed Discovery:** Metadata suggests next queries

### Technology Stack

- **Language:** Python 3.10+
- **Package Manager:** uv (mandatory - 100x faster than pip)
- **Database:** SQLite 3
- **Parser:** Regex-based (MVP) → tree-sitter (future)
- **MCP SDK:** Official `mcp` library

## 🧪 Testing

```bash
# Test MCP tools
uv run python test_mcp_tools.py

# Run with verbose output
uv run main.py index --verbose
```

## 📚 Documentation

- **Installation Guide:** `docs/INSTALLATION.md` - Complete installation and troubleshooting
- **PRD:** `docs/PRD_Context_Server.md` - Full product requirements
- **Backlog:** `docs/context/backlog.md` - Detailed task list
- **State:** `docs/context/state.md` - Current project status
- **Journal:** `docs/context/journal.md` - Session history
- **Decisions:** `docs/context/decisions.md` - Architectural decisions

## 🚧 Development

### Adding New Language Support

1. Update `src/indexer/simple_parser.py` with language patterns
2. Update `src/indexer/dependency_analyzer.py` if needed
3. Run: `uv run main.py index --full`

### Adding New MCP Tools

1. Create handler in `src/mcp_server/tools/`
2. Register in `src/mcp_server/server.py` (list_tools)
3. Add handler in `call_tool` method

## 🤝 Integration

### Claude Desktop

After running the installation script, add to your Claude Desktop config:

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

Configuration:
```json
{
  "mcpServers": {
    "mcp-context": {
      "command": "mcp-context-server",
      "env": {
        "PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

### Claude Code

Add to your `settings.json`:

```json
{
  "mcpServers": [
    {
      "name": "mcp-context",
      "command": "mcp-context-server",
      "env": {
        "PROJECT_ROOT": "."
      }
    }
  ]
}
```

### VS Code Extensions

Compatible with any MCP client via STDIO.

## 📈 Performance

- **Indexing:** 84ms for 17 files (incremental)
- **Database:** SQLite with proper indexing
- **Memory:** ~5MB RAM for medium projects
- **Disk:** ~1MB per 1000 symbols

## 🗺️ Roadmap

### MVP (Current) ✅
- [x] SQLite database with SQLAlchemy
- [x] Regex-based Python parser
- [x] Incremental indexing
- [x] 3 MCP tools (get_symbol_context, add_observation, get_project_summary)
- [x] Auto-hooks (startup/session-end)
- [x] Security validations
- [x] Automated installation scripts
- [x] Global CLI commands (`mcp-context`, `mcp-context-server`)

### P2 (Future)
- [ ] Tree-sitter native parsing
- [ ] Multi-language support (JS/TS, Go, Rust)
- [ ] Advanced security (rate limiting, audit logs)
- [ ] Performance metrics dashboard
- [ ] Token usage analytics

## 📝 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [uv](https://github.com/astral-sh/uv)

---

**Status:** ✅ MVP Complete + Autonomous Installation | **Version:** 0.1.0 | **Last Updated:** 2026-04-02
