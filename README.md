# MCP Neo4j Python - Grafo de Conhecimento Global

Sistema de memória persistente usando Neo4j para o Claude Code SDK, configurado globalmente para todos os projetos.

## 🚀 Quick Start

O MCP já está configurado globalmente! Use em qualquer projeto:

```bash
# Verificar status
claude mcp list

# Deve mostrar:
# neo4j-memory: /Users/2a/.claude/mcp-neo4j-py/run_mcp.sh - ✓ Connected
```

## 📚 Documentação

- [Configuração Global](docs/CONFIGURACAO_GLOBAL_MCP.md) - Como foi configurado globalmente
- [API Reference](docs/API.md) - Documentação das ferramentas disponíveis
- [Exemplos](docs/EXAMPLES.md) - Casos de uso práticos

## 🛠️ Ferramentas Disponíveis

### Leitura
- `read_graph` - Ler grafo completo com filtro opcional
- `search_memories` - Busca fulltext em memórias
- `find_memories_by_name` - Buscar por nomes exatos

### Escrita
- `create_entities` - Criar/atualizar entidades
- `create_relations` - Criar relações entre entidades
- `add_observations` - Adicionar observações

### Exclusão
- `delete_observations` - Remover observações específicas
- `delete_entities` - Deletar entidades
- `delete_relations` - Deletar relações

## 🏗️ Arquitetura

```
src/mcp_neo4j/
├── core/           # Lógica de negócio
│   ├── config.py   # Configurações do servidor
│   └── memory.py   # Operações de memória
├── database/       # Camada de dados
│   └── connection.py
├── server/         # Servidor MCP
│   ├── mcp_server.py
│   └── runtime.py
└── utils/          # Utilitários
    └── logging_setup.py
```

## 🔧 Desenvolvimento

### Setup Local

```bash
# Clonar e entrar no diretório
cd /Users/2a/.claude/mcp-neo4j-py

# Ativar ambiente virtual
source venv/bin/activate

# Instalar em modo desenvolvimento
pip install -e .
```

### Executar Localmente

```bash
# Via script wrapper
./run_mcp.sh

# Ou diretamente
venv/bin/python -m mcp_neo4j
```

### Testes

```bash
# Executar testes
pytest tests/

# Com cobertura
pytest --cov=src/mcp_neo4j tests/
```

## 📊 Modelo de Dados

### Entidade (Learning)
```python
{
    "name": "Nome único da entidade",
    "type": "person | company | concept | event",
    "observations": ["Fato 1", "Fato 2", ...]
}
```

### Relação
```python
{
    "source": "Nome da entidade origem",
    "target": "Nome da entidade destino",
    "relationType": "WORKS_AT | USES | CONNECTS_TO"
}
```

## 🌟 Casos de Uso

### 1. Armazenar Conhecimento Técnico
```
"Crie uma entidade Learning sobre Hooks do Claude SDK"
→ Armazena conceitos, exemplos e padrões
```

### 2. Conectar Conceitos
```
"Conecte o conceito de Hooks com Custom Tools"
→ Cria grafo de conhecimento relacionado
```

### 3. Buscar Soluções
```
"Busque no conhecimento sobre async Python"
→ Encontra aprendizados anteriores
```

### 4. Aprender com Erros
```
"Adicione observação: erro corrigido usando context manager"
→ Registra lições aprendidas
```

## 🔐 Configuração

### Variáveis de Ambiente (.env)

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
MCP_LOG_LEVEL=INFO
```

### Configuração Global MCP

```bash
# Adicionar globalmente
claude mcp add --scope user neo4j-memory \
  /Users/2a/.claude/mcp-neo4j-py/run_mcp.sh

# Remover
claude mcp remove neo4j-memory -s user
```

## 🐛 Troubleshooting

### Servidor não conecta
1. Verificar se Neo4j está rodando: `neo4j status`
2. Testar conexão: `cypher-shell -u neo4j -p password`
3. Ver logs: `./run_mcp.sh` (modo debug)

### Erro de Python
1. Verificar versão: `venv/bin/python --version` (deve ser 3.11+)
2. Reinstalar: `pip install -e .`

### Reconfigurar do Zero
```bash
# Remover configurações
claude mcp remove neo4j-memory -s user
claude mcp remove neo4j-memory -s local

# Recriar venv
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -e .

# Adicionar globalmente
claude mcp add --scope user neo4j-memory \
  /Users/2a/.claude/mcp-neo4j-py/run_mcp.sh
```

## 🔄 Changelog

### v0.1.0 (2025-10-06)
- ✅ Configuração global do MCP
- ✅ Correção de bug do event loop
- ✅ Script wrapper para execução
- ✅ Documentação completa
- ✅ Label "Learning" como padrão

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-feature`
3. Commit: `git commit -am 'Adiciona nova feature'`
4. Push: `git push origin feature/nova-feature`
5. Pull Request

## 📝 Licença

Este projeto está sob licença MIT.

## 🙏 Agradecimentos

- [Neo4j](https://neo4j.com/) - Graph Database
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP Framework
- [Claude Code SDK](https://docs.anthropic.com/) - SDK Base

## 📞 Suporte

- Issues: [GitHub Issues](https://github.com/seu-usuario/mcp-neo4j-py/issues)
- Documentação: [docs/](docs/)
- Exemplos: [examples/](examples/)
