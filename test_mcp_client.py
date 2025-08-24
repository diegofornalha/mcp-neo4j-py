#!/usr/bin/env python3
"""Teste do servidor MCP Neo4j"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Testa o servidor MCP"""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "src/mcp_neo4j/server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Listar ferramentas disponíveis
            tools = await session.list_tools()
            print("\n🔧 Ferramentas disponíveis:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # Testar busca de memórias
            print("\n📋 Testando busca de memórias...")
            result = await session.call_tool(
                "search_memories",
                arguments={"limit": 5}
            )
            print(f"Resultado: {json.dumps(result.content, indent=2)[:200]}...")
            
            # Testar obter orientações
            print("\n📚 Testando obter orientações...")
            result = await session.call_tool(
                "get_guidance",
                arguments={"topic": "labels"}
            )
            print(f"Resultado: {result.content[0].text[:200]}...")
            
            print("\n✅ Servidor MCP funcionando corretamente!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())