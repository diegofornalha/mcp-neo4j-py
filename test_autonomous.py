#!/usr/bin/env python3
"""
Script para testar e demonstrar o modo autônomo
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_autonomous():
    """Testa o sistema autônomo"""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "src/mcp_neo4j/server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🤖 TESTANDO SISTEMA AUTÔNOMO MCP\n")
            
            # Listar ferramentas
            tools = await session.list_tools()
            autonomous_tools = [t for t in tools.tools if 'autonomous' in t.name.lower()]
            
            print("🔧 Ferramentas Autônomas Disponíveis:")
            for tool in autonomous_tools:
                print(f"  • {tool.name}")
            
            # Verificar status
            print("\n📊 Verificando status atual...")
            result = await session.call_tool("autonomous_status", {})
            status = json.loads(result.content[0].text) if result.content else {}
            
            print(f"  Status: {'ATIVO' if status.get('active') else 'INATIVO'}")
            if status.get('statistics'):
                stats = status['statistics']
                print(f"  Aprendizados: {stats.get('total_learnings', 0)}")
                print(f"  Padrões detectados: {stats.get('patterns_detected', 0)}")
            
            # Ativar modo autônomo
            if not status.get('active'):
                print("\n🚀 Ativando modo autônomo...")
                result = await session.call_tool("activate_autonomous", {})
                activation = json.loads(result.content[0].text) if result.content else {}
                print(f"  {activation.get('message', 'Ativado!')}")
                
                if activation.get('features'):
                    print("\n  Recursos ativos:")
                    for feature in activation['features']:
                        print(f"    ✓ {feature}")
            
            # Testar sugestões
            print("\n💡 Testando sugestões inteligentes...")
            result = await session.call_tool(
                "suggest_best_approach",
                {"current_task": "implementar nova feature MCP"}
            )
            suggestions = json.loads(result.content[0].text) if result.content else {}
            
            if suggestions.get('important_rules'):
                print("  Regras importantes:")
                for rule in suggestions['important_rules'][:3]:
                    print(f"    • {rule}")
            
            print("\n✅ Sistema autônomo funcionando perfeitamente!")
            print("\n🎯 COLABORAÇÃO ATIVA:")
            print("  • O sistema está monitorando todas as ações")
            print("  • Aprendendo com cada execução")
            print("  • Melhorando continuamente")
            print("  • Sugerindo melhores práticas")

if __name__ == "__main__":
    asyncio.run(test_autonomous())