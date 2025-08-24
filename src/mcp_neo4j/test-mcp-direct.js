#!/usr/bin/env node
const { spawn } = require('child_process');

// Teste direto do MCP com inicialização completa
const testMCP = async () => {
  console.log('🔍 Testando MCP diretamente...\n');
  
  // Criar processo Docker
  const docker = spawn('docker', [
    'exec', '-i', 'mcp-neo4j-agent',
    'node', 'build/index.js'
  ], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: process.env
  });

  let response = '';
  
  // Capturar resposta
  docker.stdout.on('data', (data) => {
    response += data.toString();
  });
  
  docker.stderr.on('data', (data) => {
    console.error('STDERR:', data.toString());
  });
  
  // 1. Enviar initialize
  const initRequest = {
    jsonrpc: "2.0",
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: {
        name: "test-client",
        version: "1.0.0"
      }
    },
    id: 1
  };
  
  docker.stdin.write(JSON.stringify(initRequest) + '\n');
  
  // Aguardar resposta
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 2. Listar ferramentas
  const listRequest = {
    jsonrpc: "2.0",
    method: "tools/list",
    params: {},
    id: 2
  };
  
  docker.stdin.write(JSON.stringify(listRequest) + '\n');
  
  // Aguardar resposta
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 3. Testar uma ferramenta
  const testRequest = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "list_memory_labels",
      arguments: {}
    },
    id: 3
  };
  
  docker.stdin.write(JSON.stringify(testRequest) + '\n');
  
  // Aguardar resposta final
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  docker.kill();
  
  // Processar respostas
  const lines = response.split('\n').filter(line => line.trim());
  lines.forEach((line, i) => {
    if (line.includes('jsonrpc')) {
      try {
        const json = JSON.parse(line);
        console.log(`\n📦 Resposta ${i + 1}:`, JSON.stringify(json, null, 2).substring(0, 500));
      } catch (e) {
        console.log(`\n📝 Linha ${i + 1}:`, line);
      }
    }
  });
};

testMCP().catch(console.error);