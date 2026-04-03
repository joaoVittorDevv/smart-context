#!/bin/bash
#
# MCP Context Server - Session End Hook
#
# This script runs when a Claude session ends.
# It checks if state.md was updated and warns if not.
#

set -e

PROJECT_ROOT="${PROJECT_ROOT:-.}"
STATE_FILE="$PROJECT_ROOT/docs/context/state.md"
SESSION_FILE="$PROJECT_ROOT/.claude/.session_start_time"

echo ""
echo "🏁 Encerrando sessão MCP Context Server..."
echo ""

# Check if state.md exists
if [ ! -f "$STATE_FILE" ]; then
    echo "⚠️  AVISO: Arquivo 'docs/context/state.md' não encontrado!"
    echo "   Este arquivo deve existir para rastrear o progresso do projeto."
    echo ""
    exit 0
fi

# Get last modified time of state.md
if [[ "$OSTYPE" == "darwin"* ]]; then
    STATE_MOD=$(stat -f "%m" "$STATE_FILE" 2>/dev/null || echo "0")
else
    STATE_MOD=$(stat -c "%Y" "$STATE_FILE" 2>/dev/null || echo "0")
fi

# Get session start time (if exists)
SESSION_START=0
if [ -f "$SESSION_FILE" ]; then
    SESSION_START=$(cat "$SESSION_FILE" 2>/dev/null || echo "0")
fi

# Check if state was modified during session
if [ "$SESSION_START" -gt 0 ] && [ "$STATE_MOD" -le "$SESSION_START" ]; then
    echo "⚠️  AVISO IMPORTANTE:"
    echo "   O arquivo 'docs/context/state.md' NÃO foi atualizado nesta sessão!"
    echo ""
    echo "   Por favor, registre o progresso antes de sair:"
    echo "   1. Atualize 'docs/context/state.md' com status atual"
    echo "   2. Adicione entradas em 'docs/context/journal.md'"
    echo "   3. Registre decisões arquiteturais em 'docs/context/decisions.md'"
    echo ""
    echo "   Isso ajuda a manter a continuidade entre sessões."
    echo ""
elif [ "$SESSION_START" -eq 0 ]; then
    echo "ℹ️  Nota: Tempo de início da sessão não registrado."
    echo "   Considere atualizar 'docs/context/state.md' ao final de cada sessão."
    echo ""
else
    echo "✅ Memória da sessão registrada em 'docs/context/state.md'"
    echo ""
fi

# Clean up session file
rm -f "$SESSION_FILE"

echo "👋 Até a próxima sessão!"
echo ""
