#!/usr/bin/env python3
"""
Teste simples do FastMCP
"""

from mcp.server.fastmcp import FastMCP

# Criar servidor MCP
mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Função de teste simples"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Soma dois números"""
    return a + b

def main():
    """Função principal"""
    print("🧪 Testando FastMCP...")
    
    # Verificar se as ferramentas foram registradas
    print(f"1. Servidor MCP criado: {mcp is not None}")
    print(f"2. Nome do servidor: {mcp.name}")
    
    # Verificar se as funções têm o decorator
    print("\n3. Verificando decorators:")
    
    if hasattr(hello, '__mcp_tool__'):
        print("   ✅ hello: Decorator MCP aplicado")
    else:
        print("   ❌ hello: Decorator MCP não aplicado")
    
    if hasattr(add, '__mcp_tool__'):
        print("   ✅ add: Decorator MCP aplicado")
    else:
        print("   ❌ add: Decorator MCP não aplicado")
    
    # Testar execução das funções
    print("\n4. Testando execução:")
    try:
        result1 = hello("Test")
        print(f"   ✅ hello('Test'): {result1}")
        
        result2 = add(5, 3)
        print(f"   ✅ add(5, 3): {result2}")
        
    except Exception as e:
        print(f"   ❌ Erro na execução: {e}")
    
    print("\n5. Testando protocolo MCP...")
    
    # Simular comando MCP
    import json
    
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
    
    try:
        import subprocess
        import tempfile
        
        # Criar arquivo temporário com o código
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="stdio")
''')
            temp_file = f.name
        
        # Executar o arquivo temporário
        result = subprocess.run(
            ['/home/codable/terminal/mcp-neo4j-py/.venv/bin/python', temp_file],
            input=input_data,
            capture_output=True,
            text=True
        )
        
        print("   Resposta do servidor:")
        print(result.stdout)
        
        if result.stderr:
            print("   Erros:")
            print(result.stderr)
        
        # Limpar arquivo temporário
        import os
        os.unlink(temp_file)
        
    except Exception as e:
        print(f"   ❌ Erro no teste MCP: {e}")

if __name__ == "__main__":
    main()
