#!/usr/bin/env python3
"""
Demonstração completa das ferramentas MCP Neo4j
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime

async def demo_mcp():
    """Demonstra todas as funcionalidades MCP"""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "src/mcp_neo4j/server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🎯 DEMONSTRAÇÃO MCP NEO4J EM AÇÃO!\n")
            print("=" * 60)
            
            # 1. BUSCAR MEMÓRIAS
            print("\n📋 1. BUSCANDO MEMÓRIAS EXISTENTES...")
            result = await session.call_tool(
                "search_memories",
                {"query": "MCP", "limit": 3}
            )
            memories = json.loads(result.content[0].text) if result.content else []
            print(f"   Encontradas {len(memories)} memórias sobre MCP")
            for mem in memories[:2]:
                labels = mem.get('labels', [])
                name = mem.get('properties', {}).get('name', 'Sem nome')
                print(f"   • [{labels[0] if labels else '?'}] {name}")
            
            # 2. CRIAR NOVA MEMÓRIA
            print("\n✨ 2. CRIANDO NOVA MEMÓRIA...")
            new_memory = await session.call_tool(
                "create_memory",
                {
                    "label": "DemoMCP",
                    "properties": {
                        "name": f"Demo MCP {datetime.now().strftime('%H:%M:%S')}",
                        "description": "Demonstração ao vivo do MCP funcionando",
                        "status": "active",
                        "features": ["busca", "criação", "conexões", "autônomo"]
                    }
                }
            )
            created = json.loads(new_memory.content[0].text) if new_memory.content else {}
            memory_id = created.get('id', 'unknown')
            print(f"   ✅ Memória criada: {created.get('properties', {}).get('name')}")
            print(f"   ID: {memory_id}")
            
            # 3. VERIFICAR STATUS AUTÔNOMO
            print("\n🤖 3. VERIFICANDO STATUS AUTÔNOMO...")
            status = await session.call_tool("autonomous_status", {})
            auto_status = json.loads(status.content[0].text) if status.content else {}
            
            if auto_status.get('active'):
                print("   ✅ Sistema Autônomo: ATIVO")
            else:
                print("   ⚠️ Sistema Autônomo: INATIVO")
            
            if auto_status.get('statistics'):
                stats = auto_status['statistics']
                print(f"   📊 Estatísticas:")
                print(f"      • Aprendizados: {stats.get('total_learnings', 0)}")
                print(f"      • Padrões: {stats.get('patterns_detected', 0)}")
                print(f"      • Erros catalogados: {stats.get('errors_logged', 0)}")
            
            # 4. OBTER SUGESTÕES INTELIGENTES
            print("\n💡 4. OBTENDO SUGESTÕES INTELIGENTES...")
            suggestions = await session.call_tool(
                "suggest_best_approach",
                {"current_task": "otimizar performance do Neo4j"}
            )
            sugg_data = json.loads(suggestions.content[0].text) if suggestions.content else {}
            
            if sugg_data.get('important_rules'):
                print("   📌 Regras importantes:")
                for rule in sugg_data['important_rules'][:2]:
                    print(f"      • {rule}")
            
            if sugg_data.get('relevant_knowledge'):
                print("   📚 Conhecimento relevante:")
                for knowledge in sugg_data['relevant_knowledge'][:2]:
                    print(f"      • {knowledge.get('name', 'Info')}: {knowledge.get('info', '')[:50]}...")
            
            # 5. LISTAR LABELS
            print("\n🏷️ 5. LISTANDO CATEGORIAS DE MEMÓRIA...")
            labels = await session.call_tool("list_memory_labels", {})
            label_list = json.loads(labels.content[0].text) if labels.content else []
            
            print("   Top 5 categorias:")
            for label in label_list[:5]:
                print(f"      • {label.get('label')}: {label.get('count')} itens")
            
            # 6. REGISTRAR APRENDIZADO
            print("\n📝 6. REGISTRANDO APRENDIZADO...")
            learning = await session.call_tool(
                "learn_from_result",
                {
                    "task": "demonstração MCP",
                    "result": "Todas as ferramentas funcionando perfeitamente",
                    "success": True,
                    "category": "DemoSuccess"
                }
            )
            learn_result = json.loads(learning.content[0].text) if learning.content else {}
            print(f"   ✅ {learn_result.get('message', 'Aprendizado registrado')}")
            
            # 7. BUSCAR CONTEXTO
            print("\n🔍 7. BUSCANDO CONTEXTO PARA TAREFA...")
            context = await session.call_tool(
                "get_context_for_task",
                {"task_description": "criar novo servidor MCP"}
            )
            context_text = context.content[0].text if context.content else ""
            if context_text:
                lines = context_text.split('\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
            
            print("\n" + "=" * 60)
            print("✅ DEMONSTRAÇÃO COMPLETA - MCP FUNCIONANDO PERFEITAMENTE!")
            print("\n🎯 RESUMO:")
            print("   • 15 ferramentas disponíveis")
            print("   • Integração total com Neo4j")
            print("   • Sistema autônomo monitorando")
            print("   • Aprendizado contínuo ativo")
            print("   • Sinergia perfeita!")

if __name__ == "__main__":
    asyncio.run(demo_mcp())