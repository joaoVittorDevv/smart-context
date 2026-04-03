# Installation Guide - MCP Context Server

Complete guide for installing and configuring the MCP Context Server.

## Table of Contents

1. [Quick Installation](#quick-installation)
2. [Manual Installation](#manual-installation)
3. [Integration with Claude](#integration-with-claude)
4. [Troubleshooting](#troubleshooting)
5. [Uninstallation](#uninstallation)

---

## Quick Installation

### Prerequisites

- **Python 3.10+**
- **uv** package manager (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Automated Installation

**Linux/macOS:**
```bash
cd /path/to/mcp_context
./install.sh
```

**Windows (PowerShell):**
```powershell
cd C:\path\to\mcp_context
.\install.ps1
```

The script will:
1. Verify `uv` is installed
2. Install the package in editable mode (`uv pip install -e .`)
3. Create necessary directories (`.claude/`)
4. Display next steps for integration

---

## Manual Installation

### Step 1: Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# or
irm https://astral.sh/uv/install.ps1 | iex        # Windows
```

### Step 2: Install the Package

```bash
cd /path/to/mcp_context
uv pip install -e .
```

This installs two commands:
- `mcp-context` - CLI for indexing and stats
- `mcp-context-server` - MCP server for Claude integration

### Step 3: Initialize Database

```bash
mcp-context init
```

Creates `.claude/context.db` SQLite database.

### Step 4: Index Your Code

```bash
cd /path/to/your/project
mcp-context index
```

---

## Integration with Claude

### Claude Desktop

**Find your config file:**

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

**Add the server configuration:**

```json
{
  "mcpServers": {
    "mcp-context": {
      "command": "mcp-context-server",
      "env": {
        "PROJECT_ROOT": "/absolute/path/to/your/project"
      }
    }
  }
}
```

**Restart Claude Desktop** to load the server.

### Claude Code (VS Code)

**Option 1: Via settings.json**

Add to `.claude/settings.json` in your project:

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

**Option 2: Via CLAUDE.md**

Add to your `CLAUDE.md`:

```yaml
# MCP Integration
mcpServers:
  - name: mcp-context
    command: mcp-context-server
```

### Verification

After integration, verify the server is working:

1. Open Claude/Claude Code
2. Check available tools - you should see:
   - `get_symbol_context`
   - `add_observation`
   - `get_project_summary`

---

## Troubleshooting

### "command not found: mcp-context"

**Problem:** The package wasn't installed correctly.

**Solution:**
```bash
# Reinstall
uv pip install -e /path/to/mcp_context

# Verify installation
mcp-context --version
```

### "ModuleNotFoundError: No module named 'src'"

**Problem:** Python path issue.

**Solution:** Ensure you're running from the project root or the package is installed in editable mode.

### MCP server not appearing in Claude

**Problem:** Configuration not loaded.

**Solution:**
1. Check config file syntax (use a JSON validator)
2. Verify paths are absolute (not relative)
3. Restart Claude completely
4. Check `.claude/context.log` for errors

### Database locked error

**Problem:** Multiple processes accessing the database.

**Solution:** Close other Claude sessions and retry.

---

## Uninstallation

### Remove Package

```bash
uv pip uninstall mcp-context
```

### Remove Configuration

```bash
# Remove database and logs
rm -rf ~/.claude/context.db
rm -rf ~/.claude/context.log

# Remove from Claude config
# Edit your claude_desktop_config.json and remove the mcp-context entry
```

---

## Development Installation

For development with hot-reload:

```bash
cd /path/to/mcp_context
uv pip install -e ".[dev]"

# Now you can edit code and changes are reflected immediately
# No need to reinstall
```

---

## Next Steps

After installation:

1. **Index your code:** `mcp-context index`
2. **Configure Claude:** See integration section above
3. **Add observations:** Use `add_observation` tool in Claude
4. **Query context:** Use `get_symbol_context` tool in Claude

For more information, see the main [README.md](../README.md).
