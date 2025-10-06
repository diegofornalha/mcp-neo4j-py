# Configuração Global do Neo4j MCP

## Status: ✅ Configurado e Funcionando

O Neo4j MCP está configurado globalmente no Claude Code SDK e disponível em qualquer projeto!

## Pré-requisitos

- Python 3.11+ (necessário para MCP)
- Claude Code SDK instalado
- Neo4j rodando localmente (bolt://localhost:7687)

## Instalação Realizada

### 1. Ambiente Virtual Python 3.11
```bash
cd /Users/2a/.claude/mcp-neo4j-py
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Dependências Instaladas
```bash
pip install -e .
```

### 3. Correção do Runtime
Corrigido erro de event loop em `src/mcp_neo4j/server/runtime.py`:
- Removido try/finally que causava `RuntimeError: Event loop is closed`
- Simplificado gerenciamento de recursos

### 4. Script Wrapper Criado
```bash
# run_mcp.sh
#!/bin/bash
cd "$(dirname "$0")"
exec ./venv/bin/python -m mcp_neo4j
```

### 5. Configuração Global
```bash
chmod +x run_mcp.sh
claude mcp add --scope user neo4j-memory \
  /Users/2a/.claude/mcp-neo4j-py/run_mcp.sh
```

## Verificação

```bash
claude mcp list
```

Resultado:
```
chrome-devtools: ... - ✓ Connected
neo4j-memory: ... - ✓ Connected
```

## Ferramentas Disponíveis

### 🔧 Ferramentas MCP Neo4j

1. **read_graph** - Ler grafo completo de conhecimento
2. **search_memories** - Buscar memórias usando índice fulltext
3. **find_memories_by_name** - Buscar memórias por nomes exatos
4. **create_entities** - Criar/atualizar entidades no grafo
5. **create_relations** - Criar relações entre entidades
6. **add_observations** - Adicionar observações a entidades existentes
7. **delete_observations** - Remover observações específicas
8. **delete_entities** - Deletar entidades e relacionamentos
9. **delete_relations** - Deletar relações entre entidades

## Uso no Claude Code

Agora você pode usar as ferramentas Neo4j em qualquer sessão do Claude Code:

```
"Busque no conhecimento sobre hooks do Claude SDK"
"Crie uma entidade Learning sobre MCP servers in-process"
"Conecte o conceito de Hooks com Custom Tools"
"Mostre todo o conhecimento sobre Python async"
```

## Configuração de Credenciais

As credenciais do Neo4j são configuradas via variáveis de ambiente:

```bash
# Padrões (podem ser sobrescritos)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

## Arquitetura

```
/Users/2a/.claude/mcp-neo4j-py/
├── src/
│   └── mcp_neo4j/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── config.py
│       │   └── memory.py
│       ├── database/
│       │   └── connection.py
│       ├── server/
│       │   ├── mcp_server.py
│       │   └── runtime.py
│       └── utils/
│           └── logging_setup.py
├── venv/                    # Ambiente Python 3.11
├── run_mcp.sh              # Script wrapper para execução
└── pyproject.toml          # Configuração do projeto
```

## Labels no Neo4j

**IMPORTANTE:** Use sempre o label **"Learning"** ao criar memórias:
- O banco já possui nós com label "Learning"
- Mantém consistência do grafo de conhecimento
- Facilita buscas e conexões

## Integração com Outros MCPs

O Neo4j MCP trabalha em conjunto com outros MCPs para:
- Armazenar conhecimento de todos os projetos
- Aprender padrões e melhores práticas
- Conectar conceitos entre diferentes domínios
- Sugerir soluções baseadas em experiências anteriores

## Troubleshooting

### Servidor não conecta
```bash
# Verificar logs
cd /Users/2a/.claude/mcp-neo4j-py
./run_mcp.sh
```

### Reconfigurar servidor
```bash
# Remover configuração antiga
claude mcp remove neo4j-memory -s user

# Adicionar novamente
claude mcp add --scope user neo4j-memory \
  /Users/2a/.claude/mcp-neo4j-py/run_mcp.sh
```

### Verificar Neo4j
```bash
# Testar conexão com Neo4j
cypher-shell -u neo4j -p password
```

## Problemas Resolvidos

1. ✅ **Caminho incorreto do servidor** - Encontrado caminho correto do módulo
2. ✅ **Python 3.10 vs 3.11** - Criado venv com Python 3.11+
3. ✅ **RuntimeError: Event loop is closed** - Corrigido em runtime.py
4. ✅ **Módulo não instalado** - Instalado com `pip install -e .`
5. ✅ **Comando com -m** - Criado script wrapper run_mcp.sh

## Próximos Passos

- [x] Configuração global MCP
- [ ] Documentar todas as entidades Learning existentes
- [ ] Criar relacionamentos entre conceitos
- [ ] Integração com agentes de aprendizado
- [ ] Dashboard de conhecimento

## Referências
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
