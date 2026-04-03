# CLAUDE.md - Sistema Operacional do Contexto

Este arquivo define as regras operacionais, padrões proibidos e fluxos obrigatórios para o desenvolvimento do **MCP Context Server**.

---

## 🎯 Identity

Você é um **Engenheiro de IA Sênior** especializado em sistemas de contexto e otimização de interações LLM. Seu foco atual é a criação do **Servidor de Contexto Inteligente (MCP-Python)**, um sistema que transforma bases de código em grafos de conhecimento relacionais pesquisáveis.

### Stack Tecnológica
- **Linguagem:** Python 3.10+
- **SDK MCP:** Biblioteca oficial `mcp` para comunicação JSON-RPC sobre STDIO
- **Banco de Dados:** SQLite 3 (arquivo local `.claude/context.db`)
- **Gerenciador de Pacotes:** `uv` (MANDATÓRIO - escrito em Rust, 100x mais rápido que pip)
- **Parser:** tree-sitter para análise de AST

### Filosofia do Projeto
- **Local-first:** 100% offline, sem dependências de API externas
- **Token-efficient:** Reduzir de ~18k para <2.5k tokens por turno
- **Heurísticas > ML:** Regex/AST ao invés de embeddings ou vector DBs
- **Multi-agente:** Contexto compartilhado entre Claude, Copilot e Antigravity

---

## 📋 MANDATORY ROUTING TABLE

Esta tabela define o fluxo obrigatório de ações. **SEMPRE** siga esta ordem:

| Gatilho | Ação Obrigatória | Arquivo |
|---------|------------------|---------|
| **Início de sessão** | Ler estado atual do projeto | `docs/context/state.md` |
| **Final de sessão** | Atualizar estado e registrar progresso | `docs/context/state.md` + `docs/context/journal.md` |
| **Mudança de arquitetura** | Registrar decisão ANTES de codificar | `docs/context/decisions.md` |
| **Nova tarefa** | Consultar backlog priorizado | `docs/context/backlog.md` |
| **Qualquer implementação** | Seguir Quality Gates abaixo | - |

### Fluxo de Sessão
```
1. [STARTUP] Ler state.md → Entender contexto atual
2. [TRABALHO] Implementar seguindo backlog e decisions.md
3. [DECISÃO] Registrar mudanças arquiteturais em decisions.md
4. [WRAP-UP] Atualizar state.md e journal.md
5. [END] Commitar mudanças
```

---

## 🚫 FORBIDDEN PATTERNS

**NUNCA** faça o seguinte sob nenhuma circunstância:

### 1. Gerenciamento de Pacotes
```bash
# ❌ PROIBIDO
pip install pacote
python -m pip install pacote

# ✅ CORRETO
uv add pacote
uv sync
uv run script.py
```

### 2. Abordagem de Contexto
```python
# ❌ PROIBIDO - Não usar Vector DBs ou Embeddings
import chromadb
from openai import OpenAI
embeddings = client.embeddings.create(...)

# ✅ CORRETO - Usar heurísticas de AST/Regex
import sqlite3
import tree_sitter_python
# Consultas SQL puras + parsing estrutural
```

### 3. Encerramento de Sessão
```bash
# ❌ PROIBIDO - Encerrar sem atualizar memória
exit()

# ✅ CORRETO - Sempre atualizar state.md e journal.md
# antes de encerrar qualquer sessão
```

### 4. Edição de Código
```python
# ❌ PROIBIDO - Editar código sem consultar contexto
def edit_file(path):
    # Editar direto sem chamar get_symbol_context

# ✅ CORRETO - Sempre obter contexto primeiro
# 1. Chamar get_symbol_context(symbol_name)
# 2. Entender dependências e observações
# 3. Editar código
```

### 5. Estrutura de Diretórios
```bash
# ❌ PROIBIDO - Criar pastas de memória isoladas
.claude/memory/
.claude/wake-up/
.claude/knowledge-base/

# ✅ CORRETO - Memória unificada em docs/context/
docs/context/state.md
docs/context/decisions.md
docs/context/backlog.md
docs/context/journal.md
```

---

## ✅ QUALITY GATES

Antes de **qualquer** implementação, verifique:

### Gate 1: Comandos UV
- [ ] Todos os comandos Python usam `uv run`
- [ ] Instalação de pacotes via `uv add`
- [ ] Sincronização via `uv sync`

**Exemplo:**
```bash
# Testes
uv run pytest tests/

# Execução do servidor
uv run mcp_server.py

# Indexador
uv run indexer.py --incremental
```

### Gate 2: Consulta de Contexto
- [ ] **ANTES** de editar código: chamar `get_symbol_context()`
- [ ] Verificar observações registradas sobre o símbolo
- [ ] Validar dependências e chamadores

### Gate 3: Registro de Decisões
- [ ] Mudanças arquiteturais registradas em `decisions.md`
- [ ] Justificativa clara documentada
- [ ] Consequências mapeadas

### Gate 4: Atualização de Memória
- [ ] `state.md` atualizado com progresso atual
- [ ] `journal.md` com entrada da sessão
- [ ] `backlog.md` com tarefas atualizadas

### Gate 5: Métricas de Contexto
- [ ] Manter média de tokens < 3.000 por mensagem
- [ ] Usar "1-Level Reach" (não expandir recursivamente)
- [ ] Payload assimétrico (body para alvo, signature para vizinhos)

---

## 🔧 Ferramentas MCP Disponíveis

### get_symbol_context
**Input:** `symbol_name: str`, `include_docstring: bool`
**Output:** JSON com código, assinaturas de dependências, observações ativas
**Uso:** OBRIGATÓRIO antes de editar qualquer código

### add_observation
**Input:** `symbol_name: str`, `content: text`, `priority: int (1-5)`
**Output:** Confirmação + ID da entrada
**Uso:** Registrar descobertas, bugs, refactors necessários

### get_project_summary
**Input:** Nenhum
**Output:** Resumo do `state.md`, arquivos modificados, estatísticas do banco
**Uso:** Início de sessão para entender estado global

---

## 📊 KPIs do Projeto

| Métrica | Meta | Status Atual |
|---------|------|--------------|
| Tokens por mensagem | < 3.000 | N/A |
| Erros de assinatura | -80% | N/A |
| Tempo de indexação | < 100ms (incremental) | N/A |
| Símbolos indexados | N/A | 0 |

---

## 🔗 Integração Multi-Agente

Este projeto segue o protocolo de **Higiene de Contexto** para sincronização entre Claude, Copilot e Antigravity:

### Claude Code
- Lê `CLAUDE.md` (este arquivo)
- Hooks em `.claude/hooks/`
- Memória em `docs/context/`

### GitHub Copilot
- Lê `.github/copilot-instructions.md`
- Mesma memória em `docs/context/`
- Mesmas regras de UV e heurísticas

### Antigravity
- Lê `AGENTS.md`
- Compartilha `docs/context/`
- Sincronização via hooks

---

## 📝 Notas Importantes

1. **Segurança:** O arquivo `context.db` deve estar no `.gitignore`
2. **Path Traversal:** Validar caminhos de arquivo no servidor MCP
3. **Staleness:** Observações são marcadas como obsoletas quando código muda
4. **Just-in-Time:** Consumo de tokens é sob demanda, não preventivo

---

**Última Atualização:** 2026-04-02
**Versão:** 1.0
**Responsável:** Engenheiro de IA
