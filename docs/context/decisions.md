# Registro de Decisões Técnicas

Este documento registra todas as decisões arquiteturais e técnicas do projeto.

---

## Decisão #001: Abordagem Heurística vs RAG
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Escolha do mecanismo de busca de contexto

### Decisão
O uso de RAG (Retrieval-Augmented Generation) foi **descartado** em favor de heurísticas de Regex/AST no SQLite.

### Justificativa
- **Redução drástica de tokens:** De ~18k para <2.5k por turno
- **Simplicidade operacional:** Sem dependência de modelos de embedding
- **Performance:** SQLite puro é mais rápido que chamadas de API para embeddings
- **Custo:** Zero custo de API para embeddings
- **Local-first:** Funciona 100% offline

### Consequências
- Não usar Vector DBs (Chroma, Pinecone, etc.)
- Foco em tree-sitter para parsing de AST
- Implementação das "4 Regras de Ouro" de relevância

---

## Decisão #002: Gerenciador de Pacotes UV
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Escolha do gerenciador de pacotes Python

### Decisão
Uso mandatório do **uv** como gerenciador de pacotes e ambientes.

### Justificativa
- **Velocidade:** Até 100x mais rápido que pip (escrito em Rust)
- **Crítico para hooks:** Scripts de inicialização precisam rodar em milissegundos
- **Sincronização:** Garante consistência entre desenvolvedores
- **Moderno:** Melhores práticas de 2026

### Consequências
- PROIBIDO usar `pip install` direto
- Comandos sempre prefixados com `uv run`
- Ambiente isolado e reproduzível

---

## Decisão #003: SQLite como Banco de Contexto
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Escolha do banco de dados

### Decisão
SQLite 3 como banco de dados local em arquivo único (`.claude/context.db`).

### Justificativa
- **Zero configuração:** Não requer servidor
- **Portabilidade:** Arquivo único versionável (exceto pelo .gitignore)
- **Performance:** Suficiente para projetos médios
- **Local-first:** Funciona 100% offline

### Consequências
- Arquivo `context.db` deve estar no `.gitignore`
- Esquema relacional com 4 tabelas principais
- Lógica de "staleness" para observações obsoletas

---

## Decisão #004: SQLAlchemy Core vs ORM Completo
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Escolha da abordagem ORM para banco de dados

### Decisão
Usar **SQLAlchemy Core** com modelos declarativos em vez de ORM completo com sessions complexas.

### Justificativa
- **Controle fino:** Queries SQL diretas são mais performáticas que ORM abstrato
- **Simplicidade:** Menos overhead de aprendizado para a equipe
- **Performance:** Para queries de contexto, controle do SQL é crítico
- **Type-safe:** Modelos declarativos com type hints mantêm type-safety

### Consequências
- Models SQLAlchemy com `DeclarativeBase`
- Repositórios com padrão Repository para abstração
- Queries SQL diretas onde performance é crítica
- Thread-safety via `scoped_session`

---

## Decisão #005: Parser Regex-based para MVP
**Data:** 2026-04-02
**Status:** ✅ APROVADA (Provisória)
**Contexto:** Instabilidade da API do tree-sitter-languages

### Decisão
Implementar **parser baseado em regex** para MVP, postpondo tree-sitter.

### Justificativa
- **API instável:** tree-sitter-languages mudou a API entre versões
- **Complexidade:** Configuração de tree-sitter requer compilação de grammars
- **Timeline MVP:** Regex é suficiente para extrair classes/funções Python
- **Progresso:** Permite avançar no desenvolvimento enquanto se estuda tree-sitter

### Consequências
- Parser SimpleCodeParser implementado com regex patterns
- Extração funcional de classes, funções e métodos Python
- **Débito técnico:** Migrar para tree-sitter quando API estabilizar
- Limitação: Suporte inicial apenas para Python

---

## Decisão #006: Padrão Repository para Abstração
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Arquitetura de acesso a dados

### Decisão
Implementar **Padrão Repository** para abstrair acesso ao banco de dados.

### Justificativa
- **Separação de concerns:** Lógica de negócio separada de acesso a dados
- **Testabilidade:** Repositórios podem ser mockados em testes
- **Reutilização:** Operações CRUD genéricas em BaseRepository
- **Manutenibilidade:** Mudanças no schema impactam apenas repositórios

### Consequências
- BaseRepository genérico com CRUD padrão
- SymbolRepository, DependencyRepository, ObservationRepository especializados
- RepositoryManager para acesso centralizado
- Operações batch (`upsert_batch`, `create_batch`) para performance

---

## Decisão #007: Hooks Automáticos para Sincronização
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Sincronização automática de contexto entre sessões

### Decisão
Implementar **scripts de hook** para execução automática ao iniciar/encerrar sessões Claude.

### Justificativa
- **Experiência do usuário:** Contexto sempre sincronizado sem intervenção manual
- **Consistência:** Garante que o index rode antes de cada sessão
- **Rastreabilidade:** Avisa se state.md não foi atualizado (evita perda de contexto)
- **Non-intrusivo:** Scripts são leves e rápidos (< 1 segundo)

### Consequências
- `.claude/hooks/startup.sh` executa `uv run main.py index --incremental`
- `.claude/hooks/session-end.sh` verifica atualização de state.md
- Hooks devem estar em `settings.json` para funcionar automaticamente
- Pode ser desabilitado removendo entrada do settings.json

---

## Decisão #008: Validação de Segurança em Camada de Ferramentas
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Proteção contra ataques comuns em entradas do usuário

### Decisão
Implementar **validação centralizada** em `SecurityValidator` usada por todas as ferramentas MCP.

### Justificativa
- **Defense in depth:** Múltiplas camadas de validação
- **Centralização:** Lógica de segurança em um só lugar facilita manutenção
- **Performance:** Validações antes de acessar banco de dados
- **Auditoria:** Logs de tentativas de ataque em `.claude/context.log`

### Consequências
- Path Traversal protection (valida caminhos dentro do root)
- Sanitização de inputs (remove caracteres perigosos, limita tamanho)
- SQL injection detection (patterns básicos)
- Validação de enums (category, priority ranges)
- Todas as ferramentas MCP usam `SecurityValidator.validate_tool_arguments()`

---

## Decisão #009: MVP Funcional - Conclusão das 3 Fases
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Entrega do MVP do MCP Context Server

### Decisão
**MVP está COMPLETO** e pronto para integração com clientes MCP (Claude, Copilot, etc.).

### Justificativa
- **Todos os requisitos P0 do backlog foram implementados**
- **KPIs atingidos:** Indexação < 100ms (84ms), 100% cobertura de símbolos
- **Segurança básica implementada:** Path traversal, SQL injection, sanitização
- **Hooks automáticos funcionando:** Sincronização transparente

### Consequências
- Projeto pronto para uso em desenvolvimento real
- Próximo passo: Integração com Claude Desktop via configuração
- Débitos técnicos conhecidos:
  - Parser regex-based (migrar para tree-sitter quando API estabilizar)
  - Apenas Python suportado (adicionar JS/TS, Go, Rust no futuro)
- **Status transição:** Desenvolvimento → Integração e Testes

---

## Decisão #010: Instalação Autônoma via Entry Points
**Data:** 2026-04-02
**Status:** ✅ APROVADA
**Contexto:** Facilitar a instalação e integração do servidor MCP

### Decisão
Implementar **instalação autônoma** usando entry points do Python e scripts automatizados.

### Justificativa
- **Experiência do usuário:** `./install.sh` é mais simples que múltiplos comandos manuais
- **Comandos globais:** `mcp-context` e `mcp-context-server` disponíveis em qualquer lugar
- **Padrão Python:** Usar `pip install -e .` é o padrão para pacotes Python
- **Integração facilitada:** Claude só precisa do comando `mcp-context-server`

### Consequências
- Pacote instalável via `uv pip install -e .`
- Dois entry points: CLI (`mcp-context`) e servidor (`mcp-context-server`)
- Scripts de instalação para Linux/macOS (`install.sh`) e Windows (`install.ps1`)
- Documentação de instalação completa em `docs/INSTALLATION.md`

---

## Template para Novas Decisões

```markdown
## Decisão #XXX: [Título]
**Data:** YYYY-MM-DD
**Status:** [EM ANÁLISE | APROVADA | REJEITADA]
**Contexto:** [Contexto da decisão]

### Decisão
[Descrição clara da decisão]

### Justificativa
- [Razão 1]
- [Razão 2]

### Consequências
- [Impacto 1]
- [Impacto 2]
```
