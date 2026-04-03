# **PRD: Servidor de Contexto Inteligente (MCP-Python)**

**Status:** Finalizado (Refinado via Questionamento Socrático)

**Versão:** 4.1 \- Edição Expandida

**Responsável:** Engenheiro de IA

**Ambiente:** Python 3.10+ | Gerenciador: uv

## **1\. Visão Geral e Justificativa Estratégica**

O objetivo deste projeto é construir um servidor de contexto local de alto desempenho utilizando o **Model Context Protocol (MCP)**. Em vez de forçar os Modelos de Linguagem de Grande Escala (LLMs) a processarem arquivos de código inteiros — o que leva ao fenômeno de *"Lost in the Middle"* (onde o modelo ignora informações no meio de contextos longos) e a custos proibitivos — este servidor transforma a base de código em um **Grafo de Conhecimento Relacional** pesquisável e granular.

### **O Problema do "Context Drift" e "Token Waste"**

Atualmente, ferramentas como Claude Code ou GitHub Copilot frequentemente lêem arquivos de configuração ou módulos de utilitários repetidamente. Em um projeto médio, isso pode consumir 18.000 tokens por turno. Se o desenvolvedor realiza 50 interações por dia, o desperdício é massivo. Além disso, quando uma IA resolve um bug complexo, esse conhecimento "evapora" assim que a sessão termina, forçando o desenvolvedor a re-explicar a arquitetura na sessão seguinte.

### **Objetivos Estratégicos**

* **Eficiência Operacional:** Reduzir o *payload* de entrada de \~18k para \< 2.5k tokens, otimizando a latência e o custo.  
* **Persistência de Conhecimento:** Criar uma "memória de longo prazo" onde a IA registra descobertas sobre débitos técnicos e regras de negócio implícitas.  
* **Sincronização Multi-Agente:** Garantir que o estado do projeto seja uma fonte única de verdade para Claude, Copilot e Antigravity simultaneamente.

## **2\. Stack Técnica e Gerenciamento (UV Ecosystem)**

A escolha do **uv** como gerenciador de pacotes e ambientes é mandatória. O uv é escrito em Rust e oferece velocidades até 100x superiores ao pip, o que é crítico para os *Hooks* de inicialização que precisam rodar em milissegundos.

### **Componentes de Software**

* **Linguagem:** Python 3.10+ (aproveitando *Type Hinting* e *Asyncio* para o servidor MCP).  
* **SDK MCP:** Utilização da biblioteca oficial mcp para abstração da camada JSON-RPC sobre STDIO.  
* **Banco de Dados:** SQLite 3 (armazenamento local em arquivo único no diretório .claude/).  
* **Motor de Parsing:** tree-sitter. Diferente de Regex, o tree-sitter constrói uma *Abstract Syntax Tree* (AST) real, permitindo identificar com precisão o início e fim de funções, classes e referências cruzadas, independentemente do estilo de indentação.

### **Comandos de Ciclo de Vida**

\# Setup inicial do ambiente isolado  
uv init context-server  
uv add mcp-sdk sqlite3 tree-sitter-languages tree-sitter

\# Sincronização de ambiente (garante que todos os devs usem a mesma versão)  
uv sync

\# Execução otimizada do servidor  
uv run mcp\_server.py

## **3\. Arquitetura de Dados e Esquema Relacional**

O banco de dados .claude/context.db é o cérebro do sistema. Ele não armazena apenas texto, mas a topologia do código.

| Tabela | Descrição Detalhada | Campos Chave |
| :---- | :---- | :---- |
| symbols | Registro de entidades de código. | id (UUID), name (string), file (path), body (text), signature (text), type (class/func/method), last\_updated (timestamp) |
| dependencies | Mapeamento de grafo direcionado. | caller\_id (FK), callee\_id (FK), call\_site\_line (int) |
| observations | Registro de aprendizado da IA. | id, symbol\_id (FK), note (text), category (bug/refactor/logic), is\_stale (bool), session\_id |
| project\_metadata | Estado global do projeto. | key, value, last\_modified |

### **Lógica de "Staleness" (Obsolescência)**

Sempre que o indexador detecta uma mudança no body de um símbolo, ele marca todas as observations vinculadas a ele como is\_stale \= 1\. Isso força a IA a re-validar suas suposições sobre o código modificado.

## **4\. Heurísticas de Relevância (As 4 Regras de Ouro)**

Para manter o contexto "limpo", o servidor aplica filtros rigorosos antes de responder ao agente:

1. **Limite de Profundidade Única (1-Level Reach):**  
   * *Explicação:* Se a IA pergunta sobre a função UserAuth, o servidor retorna UserAuth e indica que ela chama DatabaseConnector. Ele **não** retorna o código do DatabaseConnector automaticamente.  
   * *Consequência:* Evita que uma pequena consulta puxe metade da biblioteca padrão para o contexto.  
2. **Payload Assimétrico (Summary vs Body):**  
   * *Explicação:* O símbolo alvo vem com o código completo (body). Os vizinhos vêm apenas com a signature (ex: def connect(db\_url: str) \-\> None).  
   * *Consequência:* A IA entende a interface das dependências sem gastar tokens com a implementação interna delas.  
3. **Filtro de Memória Contextual (Top 5 Insights):**  
   * *Explicação:* O servidor ordena as observações por relevância e data.  
   * *Consequência:* Evita que "diários de bordo" antigos e irrelevantes poluam a janela de contexto.  
4. **Descoberta Interativa (Curiosidade Direcionada):**  
   * *Explicação:* As instruções instruem a IA: "Se o metadado da dependência X parecer suspeito, peça o contexto de X explicitamente".  
   * *Consequência:* O consumo de tokens torna-se *Just-in-Time*.

## **5\. Fluxo de Sincronização e Hooks Multi-Plataforma**

O maior desafio é a dessincronização. Para isso, o PRD estabelece um protocolo de "Higiene de Contexto" para Claude, Copilot e Antigravity.

### **A. Hook de Inicialização (Startup Routine)**

Ao abrir o terminal ou iniciar uma sessão de chat:

* O script .claude/hooks/startup.sh é disparado.  
* Ele executa uv run indexer.py \--incremental.  
* O indexador compara o *hash* dos arquivos com o banco e atualiza apenas o que mudou.  
* **Resultado:** A IA começa a sessão com um mapa mental idêntico ao código no disco.

### **B. Regras de Sessão (System Prompts)**

Configuradas em CLAUDE.md ou .github/copilot-instructions.md:

* **Protocolo de Investigação:** "Proibido editar código sem antes chamar get\_symbol\_context".  
* **Registro de Decisão:** "Toda decisão arquitetural que desvie do padrão deve ser registrada via add\_observation".

### **C. Hook de Encerramento (Graceful Shutdown)**

Ao detectar o fim da sessão ou um comando de *commit*:

* O script verifica se o arquivo docs/context/state.md foi atualizado.  
* Caso contrário, ele emite um aviso no terminal: "IA, por favor, resuma o progresso atual antes de sair".  
* **Resultado:** A próxima sessão (ou a próxima IA) retoma exatamente de onde a anterior parou.

## **6\. Definição Detalhada das Ferramentas (MCP Tools)**

### **get\_symbol\_context**

* **Input:** symbol\_name: str, include\_docstring: bool.  
* **Output:** JSON contendo o código do símbolo, assinaturas de quem ele chama, assinaturas de quem o chama, e lista de observações ativas.

### **add\_observation**

* **Input:** symbol\_name: str, content: text, priority: int (1-5).  
* **Output:** Confirmação de gravação e ID da entrada no banco.

### **get\_project\_summary**

* **Input:** Nenhum.  
* **Output:** Resumo do arquivo state.md, lista de arquivos modificados nas últimas 24h e estatísticas do banco de dados (ex: "500 símbolos indexados").

## **7\. Métricas de Sucesso e Governança**

* **KPI de Eficiência:** Manter a média de tokens por mensagem abaixo de 3.000 (mesmo em arquivos grandes).  
* **KPI de Qualidade:** Redução de 80% em erros onde a IA tenta chamar funções que tiveram a assinatura alterada.  
* **Segurança:** O arquivo context.db deve estar obrigatoriamente no .gitignore. O servidor MCP deve validar que os caminhos de arquivo solicitados estão dentro do root do projeto para evitar *Path Traversal*.