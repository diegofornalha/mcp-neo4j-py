#!/usr/bin/env node
/**
 * MCP Proxy Server - Ponte entre Claude e o container Docker do MCP Neo4j
 */

const { spawn } = require('child_process');
const readline = require('readline');

console.error('MCP Proxy iniciando...');

// Criar processo Docker
const dockerProcess = spawn('docker', [
  'exec', '-i', 'mcp-neo4j-agent', 
  'node', 'build/index.js'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Interface para ler input do stdin
const rl = readline.createInterface({
  input: process.stdin,
  output: null,
  terminal: false
});

// Redirecionar stdin para o processo Docker
rl.on('line', (line) => {
  dockerProcess.stdin.write(line + '\n');
});

// Redirecionar output do Docker para stdout
dockerProcess.stdout.on('data', (data) => {
  process.stdout.write(data);
});

// Redirecionar erros do Docker para stderr
dockerProcess.stderr.on('data', (data) => {
  process.stderr.write(data);
});

// Lidar com encerramento do processo
dockerProcess.on('close', (code) => {
  console.error(`MCP Proxy encerrado com código ${code}`);
  process.exit(code);
});

// Lidar com erros
dockerProcess.on('error', (err) => {
  console.error('Erro no MCP Proxy:', err);
  process.exit(1);
});

// Garantir que o processo Docker seja encerrado quando o proxy for encerrado
process.on('SIGINT', () => {
  dockerProcess.kill();
  process.exit(0);
});

process.on('SIGTERM', () => {
  dockerProcess.kill();
  process.exit(0);
});