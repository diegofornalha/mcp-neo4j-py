# 🔄 Distinção Crítica: MCP Claude Code vs MCP Cursor Agent

## ⚠️ IMPORTANTE: NÃO CONFUNDIR OS CONTEXTOS

### MCP Claude Code (Separado)
- É uma ferramenta DIFERENTE do Cursor Agent
- Funciona no Claude Desktop/Code
- Tem suas próprias configurações e ferramentas
- NÃO é o que estamos usando aqui
- Configuração separada e independente
- Usa comandos `claude mcp`

### MCP Cursor Agent (Aqui)
- É o que estamos usando neste contexto
- Integrado ao Cursor Agent
- Ferramentas disponíveis através do Cursor Agent
- É o que importa para nosso projeto
- Usa ferramentas prefixadas pelo servidor MCP dentro do Cursor
- Configurado via arquivo `~/.cursor/mcp.json` (ou UI do Cursor)

## 🎯 Contexto do Projeto (Neo4j)

### Ferramentas Disponíveis (expostas pelo servidor MCP Neo4j)
- `search_memories(query?, label?, limit?, depth?, since_date?)`
- `create_memory(label, properties)`
- `create_connection(from_memory_id, to_memory_id, connection_type, properties?)`
- `update_memory(node_id, properties)`
- `delete_memory(node_id)`
- `list_memory_labels()`
- `update_connection(from_memory_id, to_memory_id, connection_type, properties)`
- `delete_connection(from_memory_id, to_memory_id, connection_type)`
- `get_context_for_task(task_description)`
- `learn_from_result(task, result, success?, category?)`
- `suggest_best_approach(current_task)`
- `activate_autonomous()`
- `deactivate_autonomous()`
- `autonomous_status()`
- `get_guidance(topic?)`

Observação: o servidor é nomeado como `neo4j-memory` e roda via `stdio`.

### O que NÃO fazer
- ❌ Confundir com MCP do Claude Code
- ❌ Usar comandos `claude mcp` neste contexto
- ❌ Misturar configurações dos dois sistemas

### O que fazer
- ✅ Usar as ferramentas acima através do Cursor Agent
- ✅ Focar no contexto do Cursor Agent
- ✅ Manter esta distinção clara em todo o projeto

---

# 🚀 Guia Completo: Configurando MCP Neo4j no Cursor Agent

## 📋 Visão Geral
Este guia mostra como conectar o servidor MCP do seu projeto Neo4j ao Cursor Agent (substituindo qualquer exemplo de RAG).

## 🎯 Objetivo
Habilitar ferramentas MCP para gerenciamento de memórias no Neo4j diretamente no Cursor Agent.

---

## 📁 Estrutura relevante do Projeto

```
<repo>
├── src/
│   └── mcp_neo4j/
│       ├── server.py              # Servidor MCP principal (FastMCP/stdio)
│       ├── autonomous.py          # Modo autônomo de aprendizado
│       ├── self_improve.py        # Heurísticas de melhorias
│       └── ...
├── pyproject.toml
├── uv.lock
└── Dockerfile
```

---

## 🔧 Passo a Passo Detalhado

### Passo 1: Verificar o Servidor MCP (Neo4j)

1.1 Confirmar existência do entrypoint
```bash
ls -la src/mcp_neo4j/server.py
```

1.2 Testar inicialização básica (protocolo MCP via stdio)
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}' | uv run python -m mcp_neo4j.server
```

Resultado esperado (resumo):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "neo4j-memory", "version": "1.0.0"}
  }
}
```

1.3 Listar ferramentas expostas
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run python -m mcp_neo4j.server
```

---

### Passo 2: Configurar MCP no Cursor Agent

2.1 Localizar/criar o arquivo de configuração do Cursor
```bash
mkdir -p ~/.cursor
ls -la ~/.cursor/mcp.json || echo '{"mcpServers":{}}' > ~/.cursor/mcp.json
```

2.2 Adicionar o servidor `neo4j-memory`
```json
{
  "mcpServers": {
    "neo4j-memory": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "mcp_neo4j.server"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "<defina_aqui>",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

Notas:
- Use `command: "python3"` se preferir não usar `uv`. Se usar `uv`, garanta que o projeto/venv esteja acessível.
- Evite credenciais hardcoded em Dockerfile. Prefira variáveis de ambiente/secret.

2.3 Reiniciar o Cursor Agent para carregar as ferramentas

---

### Passo 3: Verificar Permissões e Ambiente

- Confirme que o Neo4j está acessível em `NEO4J_URI`.
- Verifique usuário/senha/banco via env.
- Se usar Docker, mapeie as variáveis de ambiente no serviço do Cursor ou no host.

---

### Passo 4: Testar Comunicação MCP

4.1 Teste rápido do `tools/list`
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run python -m mcp_neo4j.server
```

4.2 Exemplos de chamadas (no Cursor Agent)
- Você verá as tools sob o servidor `neo4j-memory`. Exemplos de uso:
```javascript
// Buscar memórias
mcp_neo4j-memory_search_memories({ query: "Python", label: "skill", limit: 5 })

// Criar memória
mcp_neo4j-memory_create_memory({
  label: "person",
  properties: { name: "João Silva", email: "joao@example.com" }
})

// Conectar memórias
mcp_neo4j-memory_create_connection({
  from_memory_id: "<id_a>",
  to_memory_id: "<id_b>",
  connection_type: "WORKS_ON",
  properties: { role: "developer", since: "2024-01-01" }
})
```

Observação: o nome exato mostrado pelo Cursor pode variar. Se preferir, selecione as tools pelo painel do Cursor em vez de digitar o nome completo.

---

## 🎯 Ferramentas MCP Neo4j (referência rápida)

1) `search_memories` — Busca memórias por texto/label
2) `create_memory` — Cria um nó com timestamps
3) `create_connection` — Cria relacionamento entre nós
4) `update_memory` — Atualiza propriedades do nó
5) `delete_memory` — Remove nó e seus relacionamentos
6) `list_memory_labels` — Lista labels e contagens
7) `update_connection` — Atualiza propriedades de relacionamento
8) `delete_connection` — Remove relacionamento específico
9) `get_context_for_task` — Contexto antes de executar tarefa
10) `learn_from_result` — Registra aprendizado de execução
11) `suggest_best_approach` — Sugestões baseadas no grafo
12) `activate_autonomous` / `deactivate_autonomous` / `autonomous_status`
13) `get_guidance` — Ajuda e melhores práticas

---

## 🔍 Solução de Problemas

### Problema: "0 tools enabled"
Possíveis causas e soluções:
```bash
# Verificar se o servidor responde
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run python -m mcp_neo4j.server

# Checar configuração do Cursor
cat ~/.cursor/mcp.json | jq .

# Reiniciar o Cursor Agent
```

### Problema: Servidor não conecta ao Neo4j
- Verifique `NEO4J_URI`, usuário e senha
- Confirme se a base `NEO4J_DATABASE` existe
- Teste conectividade com um script simples

### Problema: Credenciais vazando
- Nunca commitar senhas no `Dockerfile`
- Use `.env`, secrets de CI/CD ou variáveis de ambiente do sistema

---

## 📊 Resultados Esperados
- Ferramentas do `neo4j-memory` aparecem no Cursor
- Operações CRUD/relacionamentos funcionam
- Logs no stderr do servidor MCP mostram atividade

---

## 🎉 Conclusão
Com o `~/.cursor/mcp.json` apontando para `python -m mcp_neo4j.server` (ou `uv run ...`), seu MCP Neo4j fica integrado ao Cursor Agent, substituindo qualquer configuração de RAG. Use as ferramentas para construir e consultar seu grafo de memória diretamente do Cursor.

---

## 📝 Dicas Finais
- Se precisar rodar via Docker, injete as variáveis `NEO4J_*` no contêiner do Cursor
- Prefira `python -m mcp_neo4j.server` a caminhos absolutos para portabilidade
- Considere adicionar `[project.scripts]` no `pyproject.toml` para um entrypoint CLI opcional

