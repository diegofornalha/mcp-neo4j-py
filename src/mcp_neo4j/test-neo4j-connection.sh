#!/bin/bash

echo "🔍 Testando conexão com Neo4j..."
echo "================================"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="Neo4j@1992"
NEO4J_DATABASE="neo4j"

echo -e "${YELLOW}Configurações:${NC}"
echo "  URI: $NEO4J_URI"
echo "  Username: $NEO4J_USERNAME"
echo "  Database: $NEO4J_DATABASE"
echo ""

# Teste de conexão usando Node.js
cd /home/codable/terminal/mcp-neo4j-agent-memory

echo -e "${YELLOW}Testando conexão direta...${NC}"
node -e "
const neo4j = require('neo4j-driver');
const driver = neo4j.driver('$NEO4J_URI', neo4j.auth.basic('$NEO4J_USERNAME', '$NEO4J_PASSWORD'));
const session = driver.session();

session.run('MATCH (n) RETURN count(n) as total, labels(n) as labels')
  .then(async result => {
    const total = result.records[0].get('total').toNumber();
    console.log('✅ Conexão bem sucedida!');
    console.log('📊 Total de nós no banco: ' + total);
    
    // Buscar labels únicos
    const labelsResult = await session.run('MATCH (n) RETURN DISTINCT labels(n) as labels');
    const uniqueLabels = new Set();
    labelsResult.records.forEach(record => {
      const labels = record.get('labels');
      if (labels) labels.forEach(label => uniqueLabels.add(label));
    });
    
    console.log('🏷️  Labels encontrados:');
    Array.from(uniqueLabels).sort().forEach(label => {
      console.log('   - ' + label);
    });
    
    session.close();
    driver.close();
  })
  .catch(err => {
    console.error('❌ Erro de conexão:', err.message);
    process.exit(1);
  });
"

echo ""
echo -e "${YELLOW}Verificando configuração MCP...${NC}"

if [ -f ~/.config/claude/mcp-config.json ]; then
    echo -e "${GREEN}✅ Arquivo de configuração MCP encontrado${NC}"
    echo "Conteúdo:"
    cat ~/.config/claude/mcp-config.json | jq '.'
else
    echo -e "${RED}❌ Arquivo de configuração MCP não encontrado${NC}"
fi

echo ""
echo -e "${YELLOW}Status do MCP:${NC}"
echo "⚠️  O MCP precisa que o Claude seja reiniciado para carregar as mudanças"
echo "   Depois do restart, as ferramentas estarão disponíveis com o prefixo 'mcp__neo4j-memory__'"

echo ""
echo "📝 Ferramentas que estarão disponíveis após restart:"
echo "   - mcp__neo4j-memory__create_memory"
echo "   - mcp__neo4j-memory__search_memories"
echo "   - mcp__neo4j-memory__update_memory"
echo "   - mcp__neo4j-memory__delete_memory"
echo "   - mcp__neo4j-memory__list_memory_labels"
echo "   - mcp__neo4j-memory__create_connection"
echo "   - mcp__neo4j-memory__update_connection"
echo "   - mcp__neo4j-memory__delete_connection"
echo "   - mcp__neo4j-memory__get_guidance"