# 01-autonomy-and-security.md

## 1. Project Identity
**Nome:** Servidor de Contexto Inteligente (MCP-Python)
**Descrição:** Um servidor MCP (Model Context Protocol) escrito em Python para gerenciar o contexto de desenvolvimento e interações com LLMs no workspace.
**Modelo de Negócio:** Ferramenta de produtividade para desenvolvedores que utilizam agentes de IA, focada em retenção de conhecimento e autonomia local.

## 2. Knowledge Rule (Unified)
O Antigravity **NÃO** deve usar o sistema interno de Knowledge Items. Toda a retenção de conhecimento deve ser escrita fisicamente no diretório `docs/context/`.

**Protocolo de Memória:**
- **Antes de qualquer tarefa:** Leia os arquivos `docs/context/state.md` e `docs/context/backlog.md` para entender o estado atual e as pendências.
- **Ao finalizar uma tarefa:** Atualize o `docs/context/state.md` com o progresso atualizado e registre as decisões tomadas em `docs/context/decisions.md`.
- **Registro de Log:** Todas as atividades relevantes devem ser documentadas nos arquivos físicos de contexto para garantir a persistência entre sessões de diferentes agentes (Claude, Copilot, Antigravity).

## 3. Autonomy Rules
- Antes de alterar qualquer código crítico ou realizar mudanças estruturais, o agente deve **sempre** gerar um **Artifact** contendo o **Implementation Plan**.
- O agente tem autonomia total para interagir com o Editor, Terminal e Browser, desde que respeite os protocolos de segurança e as regras de clean code.
- Para qualquer biblioteca externa necessária, o agente deve solicitar a instalação explicitamente ao usuário.
