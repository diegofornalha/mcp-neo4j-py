#!/usr/bin/env python3
"""
Teste direto do FastMCP
"""

import json
import subprocess
import tempfile
import os

def test_direct_mcp():
    """Testa o FastMCP diretamente"""
    
    print("🧪 Testando FastMCP diretamente...")
    
    # Criar um servidor MCP simples
    mcp_code = '''
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

# Criar servidor MCP
mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Função de teste"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Soma dois números"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")
'''
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(mcp_code)
        temp_file = f.name
    
    try:
        print(f"1. Arquivo temporário criado: {temp_file}")
        
        # Testar se o arquivo pode ser executado
        print("2. Testando execução do servidor...")
        
        # Comandos para testar
        commands = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        ]
        
        input_data = '\n'.join(json.dumps(cmd) for cmd in commands)
        
        # Executar o servidor
        result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', temp_file],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("3. Resposta do servidor:")
        print(result.stdout)
        
        if result.stderr:
            print("4. Erros do servidor:")
            print(result.stderr)
        
        # Verificar se as ferramentas foram listadas
        if 'tools' in result.stdout:
            print("✅ Ferramentas foram listadas!")
        else:
            print("❌ Ferramentas não foram listadas")
        
        # Testar chamada de ferramenta
        print("\n5. Testando chamada de ferramenta...")
        
        tool_commands = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0.0"}
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "hello",
                    "arguments": {"name": "Test"}
                }
            }
        ]
        
        tool_input = '\n'.join(json.dumps(cmd) for cmd in tool_commands)
        
        tool_result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', temp_file],
            input=tool_input,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("6. Resposta da ferramenta:")
        print(tool_result.stdout)
        
        if tool_result.stderr:
            print("7. Erros da ferramenta:")
            print(tool_result.stderr)
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao executar servidor")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        # Limpar arquivo temporário
        try:
            os.unlink(temp_file)
            print(f"8. Arquivo temporário removido: {temp_file}")
        except:
            pass

if __name__ == "__main__":
    test_direct_mcp()
