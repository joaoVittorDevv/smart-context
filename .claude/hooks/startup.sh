#!/bin/bash
#
# MCP Context Server - Startup Hook
#
# This script runs automatically when a Claude session starts.
# It performs incremental indexing and displays project status.
#

set -e

PROJECT_ROOT="${PROJECT_ROOT:-.}"
SCRIPT_NAME="$(basename "$0")"

echo ""
echo "🔄 MCP Context Server - Sincronizando contexto..."
echo ""

# Run incremental indexing
echo "📂 Indexando código (modo incremental)..."
cd "$PROJECT_ROOT" 2>/dev/null || true

if command -v uv &> /dev/null; then
    uv run main.py index 2>&1 | grep -E "(✅|🔄|Arquivos|Símbolos|Time)" || true
else
    echo "⚠️  'uv' não encontrado. Execute: uv run main.py index"
fi

echo ""
echo "📊 Resumo do Projeto:"
echo ""

if command -v uv &> /dev/null; then
    uv run main.py stats 2>&1 | grep -E "(📊|Symbols|Dependencies|Observations|-)" || true
fi

echo ""
echo "✅ Pronto! O contexto está sincronizado."
echo ""
echo "💡 Dicas:"
echo "   - Use 'get_symbol_context(nome)' para ver detalhes de um símbolo"
echo "   - Use 'add_observation(nome, nota)' para registrar observações"
echo "   - Use 'get_project_summary()' para ver estatísticas"
echo ""
