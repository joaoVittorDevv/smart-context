# MCP Context Server - Installation Script (Windows)
# This script installs the package locally and configures integration

$ErrorActionPreference = "Stop"

Write-Host "🚀 MCP Context Server - Installation" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Yellow
    exit 1
}

# Get the project root
$ProjectRoot = $PSScriptRoot
Write-Host "📂 Project root: $ProjectRoot" -ForegroundColor Green

# Install the package in editable mode
Write-Host "📦 Installing package..." -ForegroundColor Green
uv pip install -e $ProjectRoot

# Create .claude directory if it doesn't exist
$ClaudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir | Out-Null
}

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Available commands:" -ForegroundColor Cyan
Write-Host "   mcp-context           - CLI for indexing and stats" -ForegroundColor White
Write-Host "   mcp-context-server    - MCP server (for Claude integration)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. For Claude Desktop, add to your config:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   {" -ForegroundColor White
Write-Host "     `"mcpServers`": {" -ForegroundColor White
Write-Host "       `"mcp-context`": {" -ForegroundColor White
Write-Host "         `"command`": `"mcp-context-server`"," -ForegroundColor White
Write-Host "         `"env`": {" -ForegroundColor White
Write-Host "           `"PROJECT_ROOT`": `"$ProjectRoot`"" -ForegroundColor White
Write-Host "         }" -ForegroundColor White
Write-Host "       }" -ForegroundColor White
Write-Host "     }" -ForegroundColor White
Write-Host "   }" -ForegroundColor White
Write-Host ""
Write-Host "2. Index your code:" -ForegroundColor Yellow
Write-Host "   cd $ProjectRoot" -ForegroundColor White
Write-Host "   mcp-context index" -ForegroundColor White
Write-Host ""
