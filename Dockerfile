FROM python:3.11-slim

# Instalar uv para gerenciamento de dependências
RUN pip install --no-cache-dir uv

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos de configuração
COPY pyproject.toml uv.lock ./

# Instalar dependências
RUN uv sync --frozen

# Copiar código fonte
COPY src/ ./src/

# Variáveis de ambiente para Neo4j
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USERNAME=neo4j
ENV NEO4J_PASSWORD=Cancela@1
ENV NEO4J_DATABASE=neo4j

# Comando para rodar o servidor MCP
CMD ["uv", "run", "python", "src/mcp_neo4j/server.py"]