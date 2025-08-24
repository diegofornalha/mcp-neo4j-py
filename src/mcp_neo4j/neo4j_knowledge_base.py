#!/usr/bin/env python3
"""
Base de Conhecimento Neo4j - Sistema de Consulta
Acesso rápido ao conhecimento armazenado no grafo
"""

import subprocess
import sys

def execute_cypher(query):
    """Executa query Cypher via Docker"""
    cmd = [
        'docker', 'exec', '-i', 'terminal-neo4j',
        'cypher-shell', '-u', 'neo4j', '-p', 'password',
        '--format', 'plain', query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {e.stderr}")
        return None

def menu():
    """Menu interativo para consultar conhecimento"""
    print("\n" + "="*60)
    print("🧠 BASE DE CONHECIMENTO NEO4J")
    print("="*60)
    print("\n📚 CONSULTAS DISPONÍVEIS:\n")
    print("1. Ver toda documentação")
    print("2. Buscar exemplos Python")
    print("3. Ver comandos Cypher")
    print("4. Listar padrões de modelagem")
    print("5. Estatísticas do grafo")
    print("6. Buscar por palavra-chave")
    print("7. Ver configuração MCP")
    print("8. Query customizada")
    print("0. Sair")
    print("\n" + "-"*60)

def view_documentation():
    """Visualizar toda documentação"""
    query = """
    MATCH (d:Documentation)
    RETURN d.name as Nome, d.type as Tipo, d.language as Linguagem
    ORDER BY d.created_at DESC
    """
    print("\n📖 DOCUMENTAÇÃO DISPONÍVEL:")
    print(execute_cypher(query))

def view_python_examples():
    """Ver exemplos Python"""
    query = """
    MATCH (ex:PythonExample)
    OPTIONAL MATCH (ex)-[:HAS_SNIPPET]->(s:CodeSnippet)
    RETURN ex.name as Exemplo, ex.type as Tipo, COUNT(s) as Snippets
    ORDER BY ex.created_at DESC
    """
    print("\n🐍 EXEMPLOS PYTHON:")
    print(execute_cypher(query))

def view_cypher_commands():
    """Ver comandos Cypher"""
    query = """
    MATCH (cmd:CypherCommand)
    RETURN cmd.name as Comando, cmd.purpose as Propósito, cmd.category as Categoria
    ORDER BY cmd.category, cmd.name
    """
    print("\n⚡ COMANDOS CYPHER:")
    print(execute_cypher(query))

def view_modeling_patterns():
    """Ver padrões de modelagem"""
    query = """
    MATCH (p:ModelingPattern)
    RETURN p.name as Padrão, p.patterns as Exemplos
    """
    print("\n🔷 PADRÕES DE MODELAGEM:")
    result = execute_cypher(query)
    if result:
        print(result)

def view_statistics():
    """Estatísticas do grafo"""
    query = """
    MATCH (n)
    WITH labels(n)[0] as label, COUNT(n) as count
    RETURN label as Tipo, count as Quantidade
    ORDER BY count DESC
    LIMIT 20
    """
    print("\n📊 ESTATÍSTICAS DO GRAFO:")
    print(execute_cypher(query))
    
    # Total de nós e relacionamentos
    total_query = """
    MATCH (n)
    WITH COUNT(n) as nodes
    MATCH ()-[r]->()
    RETURN nodes as Total_Nós, COUNT(r) as Total_Relacionamentos
    """
    print("\n📈 TOTAIS:")
    print(execute_cypher(total_query))

def search_keyword(keyword):
    """Buscar por palavra-chave"""
    query = f"""
    MATCH (n)
    WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) CONTAINS '{keyword}')
    RETURN labels(n)[0] as Tipo, 
           COALESCE(n.name, n.type, toString(id(n))) as Nome,
           keys(n) as Propriedades
    LIMIT 20
    """
    print(f"\n🔍 RESULTADOS PARA '{keyword}':")
    result = execute_cypher(query)
    if result:
        print(result)
    else:
        print("Nenhum resultado encontrado.")

def view_mcp_config():
    """Ver configuração MCP"""
    query = """
    MATCH (c:MCP_Configuration)
    RETURN c.name as Config, c.status as Status, c.docker_container as Container
    """
    print("\n⚙️ CONFIGURAÇÃO MCP:")
    print(execute_cypher(query))

def custom_query():
    """Executar query customizada"""
    print("\n💡 Digite sua query Cypher (ou 'voltar' para cancelar):")
    query = input("> ")
    if query.lower() != 'voltar':
        print("\n📋 RESULTADO:")
        result = execute_cypher(query)
        if result:
            print(result)

# Loop principal
def main():
    while True:
        menu()
        choice = input("\n👉 Escolha uma opção: ")
        
        if choice == '1':
            view_documentation()
        elif choice == '2':
            view_python_examples()
        elif choice == '3':
            view_cypher_commands()
        elif choice == '4':
            view_modeling_patterns()
        elif choice == '5':
            view_statistics()
        elif choice == '6':
            keyword = input("\n🔍 Digite a palavra-chave: ")
            search_keyword(keyword)
        elif choice == '7':
            view_mcp_config()
        elif choice == '8':
            custom_query()
        elif choice == '0':
            print("\n👋 Até logo!")
            sys.exit(0)
        else:
            print("\n⚠️ Opção inválida!")
        
        input("\n[Enter para continuar...]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Saindo...")
        sys.exit(0)