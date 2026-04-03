# Backlog do Projeto - MCP Context Server

**Última Atualização:** 2026-04-02
**Versão do PRD:** 4.1
**Responsável:** Engenheiro de IA

---

## 📋 Requisitos Técnicos Extraídos do PRD

### Stack Mandatória
- **Linguagem:** Python 3.10+ (Type Hinting + Asyncio)
- **SDK MCP:** Biblioteca oficial `mcp` para JSON-RPC sobre STDIO
- **Banco de Dados:** SQLite 3 (arquivo `.claude/context.db`)
- **Gerenciador:** `uv` (MANDATÓRIO - 100x mais rápido que pip)
- **Parser:** tree-sitter para AST (não Regex simples)

### KPIs de Sucesso
| Métrica | Meta | Como Medir |
|---------|------|------------|
| Tokens por mensagem | < 3.000 | Contagem de tokens na resposta |
| Erros de assinatura | -80% | Logs de erro do servidor |
| Tempo de indexação | < 100ms | Benchmark incremental |
| Cobertura de símbolos | 100% | Contagem de símbolos indexados |

### Heurísticas de Relevância (4 Regras de Ouro)
1. **1-Level Reach:** Não expandir recursivamente
2. **Payload Assimétrico:** Body para alvo, signature para vizinhos
3. **Top 5 Insights:** Filtrar observações por relevância
4. **Curiosidade Direcionada:** Metadados sugerem próximas consultas

---

## 🔴 P0 - Crítico (Sprint 1-2) ✅ **CONCLUÍDO**

### FASE 1: Infraestrutura Base (3-5 dias) ✅ **CONCLUÍDO**

#### 1.1 Configuração do Ambiente
- [x] **Inicializar projeto com uv**
  - [x] `uv init context-server` (se necessário)
  - [x] Verificar Python 3.10+ instalado
  - [x] Criar estrutura de diretórios:
    ```
    src/
    ├── database/
    │   ├── __init__.py
    │   ├── schema.py
    │   └── connection.py
    ├── indexer/
    │   ├── __init__.py
    │   ├── parser.py
    │   └── incremental.py
    ├── mcp_server/
    │   ├── __init__.py
    │   ├── server.py
    │   └── tools/
    │       ├── get_symbol_context.py
    │       ├── add_observation.py
    │       └── get_project_summary.py
    └── main.py
    ```
  - [x] Validar com `uv sync`

- [x] **Instalar dependências via uv**
  - [x] `uv add mcp` (SDK oficial)
  - [x] `uv add tree-sitter`
  - [x] `uv add tree-sitter-languages`
  - [x] Nota: sqlite3 vem com Python padrão
  - [x] Validar importações

#### 1.2 Banco de Dados SQLite
- [x] **Implementar esquema relacional**
  - [x] Criar `src/database/schema.py`
  - [x] Tabela `symbols`:
    ```sql
    CREATE TABLE symbols (
      id TEXT PRIMARY KEY,  -- UUID
      name TEXT NOT NULL,
      file TEXT NOT NULL,
      body TEXT,
      signature TEXT,
      type TEXT CHECK(type IN ('class', 'function', 'method')),
      start_line INTEGER,
      end_line INTEGER,
      last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      file_hash TEXT
    );
    CREATE INDEX idx_symbols_name ON symbols(name);
    CREATE INDEX idx_symbols_file ON symbols(file);
    ```
  - [x] Tabela `dependencies`:
    ```sql
    CREATE TABLE dependencies (
      id TEXT PRIMARY KEY,
      caller_id TEXT NOT NULL,
      callee_id TEXT NOT NULL,
      call_site_line INTEGER,
      FOREIGN KEY (caller_id) REFERENCES symbols(id),
      FOREIGN KEY (callee_id) REFERENCES symbols(id)
    );
    CREATE INDEX idx_deps_caller ON dependencies(caller_id);
    CREATE INDEX idx_deps_callee ON dependencies(callee_id);
    ```
  - [x] Tabela `observations`:
    ```sql
    CREATE TABLE observations (
      id TEXT PRIMARY KEY,
      symbol_id TEXT NOT NULL,
      note TEXT NOT NULL,
      category TEXT CHECK(category IN ('bug', 'refactor', 'logic', 'architecture')),
      priority INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
      is_stale BOOLEAN DEFAULT FALSE,
      session_id TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (symbol_id) REFERENCES symbols(id)
    );
    CREATE INDEX idx_obs_symbol ON observations(symbol_id);
    CREATE INDEX idx_obs_stale ON observations(is_stale);
    ```
  - [x] Tabela `project_metadata`:
    ```sql
    CREATE TABLE project_metadata (
      key TEXT PRIMARY KEY,
      value TEXT,
      last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```
  - [x] Tabela `file_hashes` (para incremental):
    ```sql
    CREATE TABLE file_hashes (
      file_path TEXT PRIMARY KEY,
      hash TEXT NOT NULL,
      last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```

- [x] **Implementar lógica de staleness**
  - [x] Trigger automático quando `body` muda:
    ```sql
    CREATE TRIGGER mark_stale
    AFTER UPDATE OF body ON symbols
    BEGIN
      UPDATE observations
      SET is_stale = TRUE
      WHERE symbol_id = NEW.id;
    END;
    ```
  - [x] Função Python para verificar staleness

- [x] **Criar connection manager**
  - [x] `src/database/connection.py`
  - [x] Singleton para conexão com `.claude/context.db`
  - [x] Métodos CRUD genéricos
  - [x] Validação de Path Traversal

#### 1.3 Indexador tree-sitter
- [x] **Implementar parser Python** (Fallback regex ativo #005)
  - [x] Criar `src/indexer/parser.py`
  - [x] Carregar linguagem: `tree_sitter_languages.get_language('python')`
  - [x] Queries para extrair:
    - Classes: `(class_definition name: (identifier) @class_name)`
    - Funções: `(function_definition name: (identifier) @func_name)`
    - Métodos: `(function_definition (block (expression_statement (call))) @method)`
    - Imports: `(import_statement) @import`
    - Calls: `(call function: (identifier) @call_name)`

- [x] **Mapear dependências**
  - [x] Identificar chamadas dentro de cada símbolo
  - [x] Criar relação caller → callee
  - [x] Armazenar linha da chamada

- [x] **Implementar modo incremental**
  - [x] Calcular hash SHA256 de arquivos
  - [x] Comparar com `file_hashes`
  - [x] Re-indexar apenas mudanças
  - [x] Atualizar tabela de hashes

- [x] **Criar ponto de entrada**
  - [x] `src/indexer/__main__.py`
  - [x] Flags: `--incremental`, `--full`, `--verbose`
  - [x] Exemplo: `uv run -m indexer --incremental`

### FASE 2: Servidor MCP (5-7 dias) ✅ **CONCLUÍDO**

#### 2.1 Estrutura Base do Servidor
- [ ] **Configurar servidor MCP**
  - [ ] Criar `src/mcp_server/server.py`
  - [ ] Importar SDK: `from mcp.server import Server`
  - [ ] Configurar comunicação STDIO:
    ```python
    from mcp.server.stdio import stdio_server
    app = Server("context-server")
    ```
  - [ ] Registrar ferramentas com `@app.list_tools()`
  - [ ] Handler de execução com `@app.call_tool()`

- [ ] **Implementar logging estruturado**
  - [ ] Logs em `.claude/context.log`
  - [ ] Níveis: DEBUG, INFO, ERROR
  - [ ] Rotação de logs

#### 2.2 Ferramenta: get_symbol_context
- [x] **Implementar handler**
  - [x] Criar `src/mcp_server/tools/get_symbol_context.py`
  - [x] Schema de input:
    ```json
    {
      "name": "get_symbol_context",
      "description": "Obtém contexto completo de um símbolo",
      "inputSchema": {
        "type": "object",
        "properties": {
          "symbol_name": {"type": "string"},
          "include_docstring": {"type": "boolean", "default": true}
        },
        "required": ["symbol_name"]
      }
    }
    ```
  - [x] Query SQL:
    ```sql
    -- Símbolo alvo
    SELECT * FROM symbols WHERE name = ?;

    -- Dependências (1-Level Reach)
    SELECT s.name, s.signature, s.type, d.call_site_line
    FROM symbols s
    JOIN dependencies d ON s.id = d.callee_id
    WHERE d.caller_id = ?;

    -- Chamadores
    SELECT s.name, s.signature, s.type
    FROM symbols s
    JOIN dependencies d ON s.id = d.caller_id
    WHERE d.callee_id = ?;

    -- Observações ativas
    SELECT * FROM observations
    WHERE symbol_id = ? AND is_stale = FALSE
    ORDER BY priority DESC, created_at DESC
    LIMIT 5;
    ```

- [x] **Aplicar heurísticas**
  - [x] Body completo para símbolo alvo
  - [x] Apenas signature para vizinhos
  - [x] Limitar a 5 observações
  - [x] Metadados de sugestão:
    ```json
    {
      "suggested_queries": [
        "get_symbol_context('DatabaseConnector')",
        "get_symbol_context('UserRepository')"
      ]
    }
    ```

- [x] **Validação de segurança**
  - [x] Sanitizar `symbol_name` (SQL injection)
  - [x] Validar caminhos de arquivo

#### 2.3 Ferramenta: add_observation
- [x] **Implementar handler**
  - [x] Criar `src/mcp_server/tools/add_observation.py`
  - [x] Schema de input:
    ```json
    {
      "name": "add_observation",
      "description": "Registra observação sobre um símbolo",
      "inputSchema": {
        "type": "object",
        "properties": {
          "symbol_name": {"type": "string"},
          "content": {"type": "string"},
          "category": {
            "type": "string",
            "enum": ["bug", "refactor", "logic", "architecture"]
          },
          "priority": {"type": "integer", "minimum": 1, "maximum": 5}
        },
        "required": ["symbol_name", "content"]
      }
    }
    ```
  - [x] Validar existência do símbolo
  - [x] Gerar UUID para observação
  - [x] Inserir no banco:
    ```sql
    INSERT INTO observations (id, symbol_id, note, category, priority, session_id)
    VALUES (?, (SELECT id FROM symbols WHERE name = ?), ?, ?, ?, ?);
    ```

- [x] **Retornar confirmação**
  ```json
  {
    "observation_id": "uuid-here",
    "symbol_name": "UserAuth",
    "status": "recorded",
    "stale_warning": false
  }
  ```

#### 2.4 Ferramenta: get_project_summary
- [x] **Implementar handler**
  - [x] Criar `src/mcp_server/tools/get_project_summary.py`
  - [x] Schema: input vazio
  - [x] Agregar dados:
    ```sql
    -- Estatísticas
    SELECT COUNT(*) as total_symbols FROM symbols;
    SELECT COUNT(*) as total_observations FROM observations WHERE is_stale = FALSE;
    SELECT type, COUNT(*) FROM symbols GROUP BY type;

    -- Arquivos modificados (últimas 24h)
    SELECT file, last_updated
    FROM symbols
    WHERE last_updated > datetime('now', '-1 day')
    ORDER BY last_updated DESC;
    ```

- [x] **Ler state.md**
  - [x] Parsear `docs/context/state.md`
  - [x] Extrair status atual
  - [x] Incluir no resumo

- [x] **Formatar resposta**
  ```json
  {
    "project_status": "...",
    "statistics": {
      "symbols": 500,
      "observations": 23,
      "files_indexed": 42
    },
    "recent_changes": [...],
    "stale_observations": 3
  }
  ```

---

## 🟡 P1 - Importante (Sprint 3) ✅ **CONCLUÍDO** (MVP)

### FASE 3: Hooks e Integração (3-4 dias) ✅ **CONCLUÍDO**

#### 3.1 Hook de Startup
- [x] **Criar script de inicialização**
  - [x] `.claude/hooks/startup.sh`
  - [x] Conteúdo:
    ```bash
    #!/bin/bash
    echo "🔄 Sincronizando contexto..."
    uv run -m indexer --incremental
    echo "📊 Resumo do projeto:"
    uv run -c "from src.mcp_server.tools.get_project_summary import get_summary; print(get_summary())"
    echo "✅ Pronto!"
    ```
  - [x] Permissões: `chmod +x .claude/hooks/startup.sh`

- [x] **Configurar no settings.json**
  - [x] Adicionar ao `.claude/settings.json`:
    ```json
    {
      "hooks": {
        "session-start": ".claude/hooks/startup.sh"
      }
    }
    ```

#### 3.2 Hook de Session-End
- [x] **Criar script de finalização**
  - [x] `.claude/hooks/session-end.sh`
  - [x] Verificar se `state.md` foi atualizado
  - [x] Aviso se não atualizado

#### 3.3 Validações de Segurança
- [x] **Proteção Path Traversal**
  - [x] Validar caminhos absolutos
  - [x] Rejeitar `../` em caminhos
  - [x] Limitar ao root do projeto

- [x] **Sanitização de Inputs**
  - [x] Escapar caracteres especiais
  - [x] Validar tipos de dados
  - [x] Limitar tamanho de inputs

---

## 🟢 P2 - Nice to Have (Backlog Futuro)

### Expansão de Linguagens ✅ **CONCLUÍDO**
- [x] **JavaScript/TypeScript**
  - [x] Parser tree-sitter para JS/TS
  - [x] Suporte a imports ES6/CommonJS
  - [x] Detectar exports
- [x] **Go**
  - [x] Parser tree-sitter para Go
  - [x] Detectar structs e interfaces como classes
- [x] **Rust**
  - [x] Parser tree-sitter para Rust
  - [x] Detectar traits e impls
- [x] **Java / C++**
  - [x] Parser tree-sitter para Enterprise
  - [x] Mapeamento de classes e herança básica

### Métricas Avançadas
- [ ] **Dashboard de tokens**
  - [ ] Contador de tokens economizados
  - [ ] Gráfico de uso por sessão
  - [ ] ROI do sistema

- [ ] **Observabilidade**
  - [ ] Logs estruturados em JSON
  - [ ] Métricas de performance
  - [ ] Alertas de anomalias

### Ferramentas Adicionais
- [ ] **search_symbols**
  - [ ] Busca fuzzy por nome
  - [ ] Filtros por tipo e arquivo

- [ ] **invalidate_cache**
  - [ ] Forçar re-indexação completa
  - [ ] Limpar observações obsoletas

### 🎯 FASE 5: Gestão de Escopo e Portabilidade (.mcp/) ✅ **CONCLUÍDO**
- [x] **Configuração de Metadados (Banco)**
  - [X] Tabela `settings` e MetadataRepo.
- [x] **Wizard Interativo**
  - [x] Implementar `questionary.checkbox` para seleção de pastas.
  - [x] Lógica de identificação de `project_root` (Parent de .mcp/).
  - [x] **Discovery Preview (Dry-Run)**: Mostrar resumo de arquivos/linguagens antes de indexar.
- [x] **Refatoração do Indexador**
  - [x] Respeitar `included_folders` no loop de glob.
- [x] **Transparência do Agente**
  - [x] Incluir pastas monitoradas no `get_project_summary`.

---

## 📊 Dependências Entre Tarefas

```mermaid
graph TD
    A[1.1 Ambiente uv] --> B[1.2 Banco SQLite]
    B --> C[1.3 Indexador]
    C --> D[2.1 Servidor MCP Base]
    D --> E[2.2 get_symbol_context]
    D --> F[2.3 add_observation]
    D --> G[2.4 get_project_summary]
    E --> H[3.1 Hook Startup]
    F --> H
    G --> H
    H --> I[3.2 Hook Session-End]
```

---

## 🎯 Critérios de Aceitação (Definition of Done)

### Para cada tarefa P0:
- [x] Código implementado segue padrões do CLAUDE.md
- [x] Testado manualmente com `uv run`
- [x] Documentado em `docs/context/decisions.md` se arquitetural
- [x] Atualizado `state.md` com progresso
- [x] Commit realizado

### Para o MVP (fase P0 completa):
- [x] Servidor MCP funcional via STDIO
- [x] 3 ferramentas operacionais
- [x] Indexador incremental < 100ms
- [x] Tokens por resposta < 3.000
- [x] Hooks de startup/session-end funcionando

---

## 📅 Estimativa de Timeline

| Fase | Duração | Entregável |
|------|---------|------------|
| FASE 1 | 3-5 dias | Banco + Indexador |
| FASE 2 | 5-7 dias | Servidor MCP + 3 Tools |
| FASE 3 | 3-4 dias | Hooks + Segurança |
| **Total MVP** | **11-16 dias** | Sistema funcional |

---

## 🔗 Arquivos Relacionados
- **PRD:** `docs/PRD_Context_Server.md`
- **Estado Atual:** `docs/context/state.md`
- **Decisões:** `docs/context/decisions.md`
- **Journal:** `docs/context/journal.md`
- **Validação:** `docs/context/VALIDATION_CHECKLIST.md`

---

## 📝 Notas Importantes
- **MANDATÓRIO:** Usar `uv` para todos comandos Python
- **PROIBIDO:** pip install, Vector DBs, embeddings
- **SEMPRE:** Consultar contexto antes de editar código
- **KPI:** < 3.000 tokens por mensagem

---

**Próxima Ação:** Monitorar a experiência do usuário com o Wizard .mcp/ e planejar integração final com Claude Desktop.
