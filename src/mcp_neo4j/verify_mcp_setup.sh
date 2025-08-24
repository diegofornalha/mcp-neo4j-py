#!/bin/bash
# Script de verificação do MCP Neo4j Agent Memory

echo "======================================"
echo "🔍 Verificação do MCP Neo4j Setup"
echo "======================================"

# 1. Verificar container Docker
echo -e "\n1️⃣ Status do Container MCP:"
if docker ps | grep -q mcp-neo4j-agent; then
    echo "✅ Container mcp-neo4j-agent está rodando"
    docker ps | grep mcp-neo4j-agent | awk '{print "   Container ID: " $1 "\n   Uptime: " $5 " " $6 " " $7}'
else
    echo "❌ Container mcp-neo4j-agent NÃO está rodando"
fi

# 2. Verificar container Neo4j
echo -e "\n2️⃣ Status do Neo4j:"
if docker ps | grep -q terminal-neo4j; then
    echo "✅ Container terminal-neo4j está rodando"
    # Testar conexão
    if docker exec terminal-neo4j cypher-shell -u neo4j -p "Neo4j@1992" "RETURN 1" &>/dev/null; then
        echo "✅ Conexão com Neo4j funcionando"
    else
        echo "❌ Erro na conexão com Neo4j"
    fi
else
    echo "❌ Container terminal-neo4j NÃO está rodando"
fi

# 3. Verificar proxy MCP
echo -e "\n3️⃣ Teste do Proxy MCP:"
if [ -f /home/codable/terminal/mcp-proxy.js ]; then
    echo "✅ Arquivo proxy existe"
    # Testar proxy
    RESPONSE=$(echo '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}' | timeout 2 node /home/codable/terminal/mcp-proxy.js 2>/dev/null | grep -o '"jsonrpc":"2.0"')
    if [ ! -z "$RESPONSE" ]; then
        echo "✅ Proxy MCP respondendo corretamente"
    else
        echo "⚠️  Proxy MCP não respondeu ao teste"
    fi
else
    echo "❌ Arquivo proxy não encontrado"
fi

# 4. Verificar configuração .mcp.json
echo -e "\n4️⃣ Configuração MCP:"
if [ -f /home/codable/terminal/.mcp.json ]; then
    echo "✅ Arquivo .mcp.json existe"
    if grep -q "mcp-proxy.js" /home/codable/terminal/.mcp.json; then
        echo "✅ Configuração usando proxy"
    else
        echo "⚠️  Configuração não está usando proxy"
    fi
else
    echo "❌ Arquivo .mcp.json não encontrado"
fi

# 5. Verificar dados no Neo4j
echo -e "\n5️⃣ Dados no Neo4j:"
MEMORY_COUNT=$(docker exec terminal-neo4j cypher-shell -u neo4j -p "Neo4j@1992" --format plain "MATCH (m:Memory) RETURN COUNT(m) as count" 2>/dev/null | grep -o '[0-9]*' | head -1)
if [ ! -z "$MEMORY_COUNT" ]; then
    echo "✅ Neo4j tem $MEMORY_COUNT nó(s) Memory"
else
    echo "⚠️  Não foi possível contar nós Memory"
fi

# 6. Status final
echo -e "\n======================================"
echo "📊 Resumo Final:"
echo "======================================"
echo "• Container MCP: $(docker ps | grep -q mcp-neo4j-agent && echo '✅ OK' || echo '❌ Problema')"
echo "• Container Neo4j: $(docker ps | grep -q terminal-neo4j && echo '✅ OK' || echo '❌ Problema')"
echo "• Proxy MCP: $([ -f /home/codable/terminal/mcp-proxy.js ] && echo '✅ OK' || echo '❌ Problema')"
echo "• Configuração: $([ -f /home/codable/terminal/.mcp.json ] && echo '✅ OK' || echo '❌ Problema')"
echo ""
echo "🎯 Para testar o MCP no Claude, use:"
echo "   claude mcp list"
echo ""