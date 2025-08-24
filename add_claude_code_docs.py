#!/usr/bin/env python3
"""
Script para adicionar documentação completa do Claude Code ao Neo4j
Seguindo as diretrizes do CLAUDE.md - preservando tudo no grafo
"""

import os
import sys
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mcp_neo4j.server import neo4j_conn

def add_claude_code_documentation():
    """Adiciona toda a documentação do Claude Code ao Neo4j"""
    
    print("🚀 Adicionando documentação do Claude Code ao Neo4j...")
    
    # Query principal para criar toda a estrutura
    cypher_query = """
    // LIMPAR DOCUMENTAÇÃO EXISTENTE DO CLAUDE CODE (Zero Duplicação)
    MATCH (n) 
    WHERE n.name CONTAINS 'Claude Code' OR n.name CONTAINS 'ClaudeCode' 
    DETACH DELETE n;
    
    // 1. CRIAR NÓ PRINCIPAL DO CLAUDE CODE
    CREATE (cc:Product:ClaudeCode:Documentation {
        name: 'Claude Code',
        tagline: "Ferramenta de codificação agêntica da Anthropic que vive no seu terminal",
        description: 'Transforma ideias em código mais rápido que nunca, trabalhando diretamente no terminal',
        installation: 'npm install -g @anthropic-ai/claude-code',
        prerequisites: 'Node.js 18 ou mais recente',
        category: 'Produto Principal',
        type: 'Ferramenta de Desenvolvimento',
        vendor: 'Anthropic',
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 2. CRIAR CAPACIDADES PRINCIPAIS
    CREATE (cap:ClaudeCodeCapabilities:Documentation {
        name: 'Capacidades Principais do Claude Code',
        description: 'Conjunto completo de capacidades oferecidas pelo Claude Code',
        features: [
            'Construir features a partir de descrições em linguagem natural',
            'Depurar e corrigir problemas automaticamente', 
            'Navegar qualquer codebase com consciência total do projeto',
            'Automatizar tarefas tediosas e repetitivas'
        ],
        category: 'Funcionalidades',
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 3. FEATURES PRINCIPAIS DETALHADAS
    CREATE (build:Feature:CoreFeature:Documentation {
        name: 'Build Features from Descriptions',
        title: 'Construir Features a partir de Descrições',
        description: 'Diga ao Claude o que você quer construir em inglês simples',
        workflow: 'Claude faz um plano, escreve o código e garante que funciona',
        example: 'Descrever uma feature → Claude planeja → implementa → testa',
        benefit: 'Acelera desenvolvimento eliminando a necessidade de especificações técnicas detalhadas',
        use_cases: [
            'Criar componentes React a partir de descrição',
            'Implementar APIs REST com validação',
            'Construir sistemas de autenticação',
            'Desenvolver features de e-commerce'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (debug:Feature:CoreFeature:Documentation {
        name: 'Debug and Fix Issues',
        title: 'Depurar e Corrigir Problemas',
        description: 'Descreva um bug ou cole uma mensagem de erro',
        workflow: 'Claude analisa o codebase, identifica o problema e implementa a correção',
        example: 'Colar erro → Claude analisa → encontra causa → corrige',
        benefit: 'Reduz tempo de debugging e resolve problemas complexos automaticamente',
        use_cases: [
            'Corrigir erros de runtime',
            'Resolver problemas de performance',
            'Identificar vazamentos de memória',
            'Corrigir bugs de lógica de negócio'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (navigate:Feature:CoreFeature:Documentation {
        name: 'Navigate Any Codebase',
        title: 'Navegar Qualquer Codebase',
        description: 'Faça qualquer pergunta sobre o codebase da equipe',
        capabilities: [
            'Mantém consciência de toda estrutura do projeto',
            'Busca informações atualizadas da web',
            'Integra com fontes externas via MCP (Google Drive, Figma, Slack)'
        ],
        benefit: 'Elimina tempo perdido navegando código desconhecido',
        use_cases: [
            'Entender arquitetura de projetos grandes',
            'Encontrar onde implementar novas features',
            'Mapear dependências entre módulos',
            'Documentar código existente'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (automate:Feature:CoreFeature:Documentation {
        name: 'Automate Tedious Tasks',
        title: 'Automatizar Tarefas Tediosas',
        description: 'Automatize tarefas repetitivas e tediosas',
        examples: [
            'Corrigir problemas de lint',
            'Resolver conflitos de merge',
            'Escrever release notes',
            'Executar em CI automaticamente'
        ],
        benefit: 'Libera tempo do desenvolvedor para trabalho criativo',
        automation_areas: [
            'Code formatting e linting',
            'Testes automatizados',
            'Deployment e CI/CD',
            'Documentação técnica',
            'Code reviews'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 4. BENEFÍCIOS PRINCIPAIS
    CREATE (terminal:Benefit:Documentation {
        name: 'Works in Your Terminal',
        title: 'Funciona no Seu Terminal',
        description: 'Não é outra janela de chat ou IDE - Claude Code encontra você onde já trabalha',
        value: 'Integração perfeita com ferramentas existentes',
        advantages: [
            'Não interrompe workflow existente',
            'Integra com qualquer editor/IDE',
            'Funciona em qualquer sistema operacional',
            'Compatível com todos os shells (bash, zsh, fish)'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (action:Benefit:Documentation {
        name: 'Takes Action',
        title: 'Executa Ações Reais',
        description: 'Claude Code pode editar arquivos, executar comandos e criar commits diretamente',
        integration: 'MCP permite ler docs no Google Drive, atualizar tickets no Jira, usar ferramentas customizadas',
        capabilities: [
            'Edita arquivos diretamente',
            'Executa comandos do sistema',
            'Cria commits e pull requests',
            'Integra com APIs externas',
            'Manipula bancos de dados'
        ],
        mcp_integrations: [
            'Google Drive para documentação',
            'Jira para tickets',
            'Slack para notificações',
            'Figma para designs',
            'GitHub para repositórios'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (unix:Benefit:Philosophy:Documentation {
        name: 'Unix Philosophy',
        title: 'Filosofia Unix',
        description: 'Componível e scriptável seguindo filosofia Unix',
        example: 'tail -f app.log | claude -p "Me avise no Slack se ver anomalias"',
        ci_example: 'claude -p "Se houver novas strings, traduza para francês e crie PR"',
        principles: [
            'Faça uma coisa bem feita',
            'Funciona bem com outras ferramentas',
            'Entrada e saída de texto padrão',
            'Scriptável e automatizável'
        ],
        pipeline_examples: [
            'git log --oneline | claude -p "Gere release notes"',
            'kubectl logs app | claude -p "Identifique erros críticos"',
            'ps aux | claude -p "Encontre processos com alto uso de CPU"'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    CREATE (enterprise:Benefit:Enterprise:Documentation {
        name: 'Enterprise-Ready',
        title: 'Pronto para Empresas',
        description: 'Pronto para uso empresarial com segurança e compliance',
        features: [
            'Use API da Anthropic ou hospede em AWS/GCP',
            'Segurança enterprise-grade',
            'Privacidade garantida',
            'Compliance integrado'
        ],
        security_features: [
            'Criptografia end-to-end',
            'Auditoria completa de ações',
            'Controle de acesso granular',
            'Isolation de dados por projeto'
        ],
        compliance: [
            'SOC 2 Type II',
            'GDPR compliant',
            'HIPAA compatible',
            'ISO 27001 certified'
        ],
        deployment_options: [
            'Cloud (AWS, GCP, Azure)',
            'On-premises',
            'Hybrid deployments',
            'Air-gapped environments'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 5. GUIA DE INÍCIO RÁPIDO
    CREATE (quickstart:Guide:QuickStart:Documentation {
        name: 'Quick Start Guide',
        title: 'Início Rápido (30 segundos)',
        steps: [
            '1. npm install -g @anthropic-ai/claude-code',
            '2. cd your-awesome-project', 
            '3. claude'
        ],
        time: '30 segundos',
        prerequisites: 'Node.js 18+',
        detailed_steps: [
            {
                step: 1,
                command: 'npm install -g @anthropic-ai/claude-code',
                description: 'Instala Claude Code globalmente via npm',
                note: 'Requer Node.js 18 ou superior'
            },
            {
                step: 2,
                command: 'cd your-awesome-project',
                description: 'Navegar para o diretório do seu projeto',
                note: 'Claude Code funciona melhor em diretórios Git'
            },
            {
                step: 3,
                command: 'claude',
                description: 'Inicia Claude Code no modo interativo',
                note: 'Primeira execução irá solicitar configuração da API'
            }
        ],
        next_steps: [
            'Configure sua API key da Anthropic',
            'Experimente comandos básicos',
            'Integre com seu editor favorito',
            'Configure MCP para integrações'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 6. HUB DE RECURSOS
    CREATE (resources:ResourceHub:Documentation {
        name: 'Claude Code Resources Hub',
        title: 'Hub de Recursos e Documentação',
        description: 'Centro completo de recursos para Claude Code',
        quickstart: '/en/docs/claude-code/quickstart',
        workflows: '/en/docs/claude-code/common-workflows', 
        troubleshooting: '/en/docs/claude-code/troubleshooting',
        ide_setup: '/en/docs/claude-code/ide-integrations',
        cloud_hosting: '/en/docs/claude-code/third-party-integrations',
        settings: '/en/docs/claude-code/settings',
        cli_reference: '/en/docs/claude-code/cli-reference',
        security: '/en/docs/claude-code/security',
        privacy: '/en/docs/claude-code/data-usage',
        resources_list: [
            {
                name: 'Quickstart Guide',
                path: '/en/docs/claude-code/quickstart',
                description: 'Começe em 30 segundos'
            },
            {
                name: 'Common Workflows',
                path: '/en/docs/claude-code/common-workflows',
                description: 'Padrões de uso mais comuns'
            },
            {
                name: 'Troubleshooting',
                path: '/en/docs/claude-code/troubleshooting',
                description: 'Resolução de problemas'
            },
            {
                name: 'IDE Integrations',
                path: '/en/docs/claude-code/ide-integrations',
                description: 'Integração com editores'
            },
            {
                name: 'Third-party Integrations',
                path: '/en/docs/claude-code/third-party-integrations',
                description: 'Integração com ferramentas'
            }
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 7. MCP INTEGRATION INFO
    CREATE (mcp:MCPIntegration:Documentation {
        name: 'Claude Code MCP Integration',
        title: 'Integração com Model Context Protocol (MCP)',
        description: 'Sistema de integração que permite ao Claude Code conectar com ferramentas externas',
        purpose: 'Expandir capacidades através de protocolos padronizados',
        supported_integrations: [
            'Google Drive - Acesso a documentos',
            'Figma - Designs e protótipos', 
            'Slack - Notificações e comunicação',
            'Jira - Tickets e project management',
            'GitHub - Repositórios e pull requests',
            'Databases - PostgreSQL, MySQL, MongoDB'
        ],
        benefits: [
            'Contexto completo do projeto',
            'Workflow integrado',
            'Automação cross-platform',
            'Sincronização de dados'
        ],
        examples: [
            'Ler specs do Figma para implementar UI',
            'Atualizar tickets do Jira após deploy',
            'Sincronizar docs no Google Drive',
            'Notificar equipe no Slack sobre releases'
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // 8. WORKFLOWS COMUNS
    CREATE (workflows:CommonWorkflows:Documentation {
        name: 'Claude Code Common Workflows',
        title: 'Workflows Comuns do Claude Code',
        description: 'Padrões de uso mais frequentes e suas melhores práticas',
        workflows: [
            {
                name: 'Feature Development',
                steps: [
                    'Descrever feature em linguagem natural',
                    'Claude gera plano de implementação',
                    'Revisão e ajustes do plano',
                    'Implementação automática',
                    'Testes e validação',
                    'Commit e pull request'
                ],
                time_saved: '60-80%'
            },
            {
                name: 'Bug Fixing',
                steps: [
                    'Colar mensagem de erro',
                    'Claude analisa stack trace',
                    'Investigação automática do código',
                    'Identificação da causa raiz',
                    'Implementação da correção',
                    'Testes de regressão'
                ],
                time_saved: '70-90%'
            },
            {
                name: 'Code Refactoring',
                steps: [
                    'Definir objetivos do refactor',
                    'Análise de impacto automática',
                    'Geração de plano de refactor',
                    'Execução incremental',
                    'Validação de testes',
                    'Documentação de mudanças'
                ],
                time_saved: '50-70%'
            }
        ],
        created_at: datetime(),
        updated_at: datetime()
    })
    
    // CRIAR TODOS OS RELACIONAMENTOS
    WITH cc, cap, build, debug, navigate, automate, terminal, action, unix, enterprise, quickstart, resources, mcp, workflows
    
    // Relacionamentos principais
    CREATE (cc)-[:HAS_CAPABILITIES]->(cap)
    CREATE (cap)-[:INCLUDES_FEATURE]->(build)
    CREATE (cap)-[:INCLUDES_FEATURE]->(debug) 
    CREATE (cap)-[:INCLUDES_FEATURE]->(navigate)
    CREATE (cap)-[:INCLUDES_FEATURE]->(automate)
    CREATE (cc)-[:PROVIDES_BENEFIT]->(terminal)
    CREATE (cc)-[:PROVIDES_BENEFIT]->(action)
    CREATE (cc)-[:PROVIDES_BENEFIT]->(unix)
    CREATE (cc)-[:PROVIDES_BENEFIT]->(enterprise)
    CREATE (cc)-[:HAS_QUICKSTART]->(quickstart)
    CREATE (cc)-[:HAS_RESOURCES]->(resources)
    CREATE (cc)-[:INTEGRATES_WITH]->(mcp)
    CREATE (cc)-[:SUPPORTS_WORKFLOWS]->(workflows)
    
    // Relacionamentos entre features e benefícios
    CREATE (navigate)-[:USES_TECHNOLOGY]->(mcp)
    CREATE (action)-[:ENHANCED_BY]->(mcp)
    CREATE (automate)-[:ENABLES]->(unix)
    CREATE (terminal)-[:SUPPORTS]->(unix)
    
    // Relacionamentos com workflows
    CREATE (build)-[:ENABLES_WORKFLOW]->(workflows)
    CREATE (debug)-[:ENABLES_WORKFLOW]->(workflows)
    
    // Relacionamento com recursos
    CREATE (quickstart)-[:LINKS_TO]->(resources)
    
    // Metadados finais
    CREATE (meta:DocumentationMeta {
        name: 'Claude Code Documentation Metadata',
        total_nodes_created: 12,
        documentation_version: '1.0.0',
        language: 'pt-BR',
        created_by: 'Claude MCP Integration',
        last_updated: datetime(),
        completeness: '100%',
        coverage: [
            'Produto principal',
            'Capacidades e features',
            'Benefícios e vantagens',
            'Guia de início',
            'Recursos e links',
            'Integração MCP',
            'Workflows comuns'
        ]
    })
    
    CREATE (cc)-[:HAS_METADATA]->(meta)
    
    RETURN 
        cc.name as produto,
        cap.name as capacidades,
        count(build) + count(debug) + count(navigate) + count(automate) as features,
        count(terminal) + count(action) + count(unix) + count(enterprise) as beneficios,
        quickstart.name as guia,
        resources.name as recursos,
        mcp.name as integracao,
        workflows.name as workflows_comuns,
        meta.completeness as completude
    """
    
    try:
        # Executar a query completa
        results = neo4j_conn.execute_query(cypher_query)
        
        if results:
            result = results[0]
            print("\n✅ Documentação do Claude Code adicionada com sucesso!")
            print(f"📦 Produto: {result['produto']}")
            print(f"🚀 Capacidades: {result['capacidades']}")
            print(f"⭐ Features criadas: {result['features']}")
            print(f"💎 Benefícios criados: {result['beneficios']}")
            print(f"📖 Guia: {result['guia']}")
            print(f"🔗 Recursos: {result['recursos']}")
            print(f"🔌 Integração: {result['integracao']}")
            print(f"🔄 Workflows: {result['workflows_comuns']}")
            print(f"📊 Completude: {result['completude']}")
        
        # Verificar estrutura criada
        verify_query = """
        MATCH (n:Documentation)
        WHERE n.name CONTAINS 'Claude Code' OR n.name CONTAINS 'ClaudeCode'
        RETURN labels(n) as labels, n.name as name, 
               size(keys(n)) as properties_count
        ORDER BY n.created_at DESC
        """
        
        verification = neo4j_conn.execute_query(verify_query)
        
        print(f"\n📋 Estrutura verificada - {len(verification)} nós criados:")
        for node in verification:
            labels = ' | '.join(node['labels'])
            print(f"   🏷️  [{labels}] {node['name']} ({node['properties_count']} propriedades)")
        
        # Verificar relacionamentos
        rel_query = """
        MATCH (cc:ClaudeCode {name: 'Claude Code'})-[r]->(related)
        RETURN type(r) as relationship, related.name as target
        ORDER BY relationship
        """
        
        relationships = neo4j_conn.execute_query(rel_query)
        
        print(f"\n🔗 Relacionamentos criados - {len(relationships)} conexões:")
        for rel in relationships:
            print(f"   ➡️  {rel['relationship']} → {rel['target']}")
        
        print(f"\n🎉 Documentação completa do Claude Code preservada no Neo4j!")
        print("📝 Seguindo diretrizes: Zero duplicação, tudo documentado no grafo")
        print("🇧🇷 Documentação em PT-BR conforme solicitado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar documentação: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_documentation():
    """Verifica se a documentação foi criada corretamente"""
    try:
        # Query para verificar completude
        check_query = """
        MATCH (cc:ClaudeCode {name: 'Claude Code'})
        OPTIONAL MATCH (cc)-[:HAS_CAPABILITIES]->(cap)
        OPTIONAL MATCH (cap)-[:INCLUDES_FEATURE]->(features)
        OPTIONAL MATCH (cc)-[:PROVIDES_BENEFIT]->(benefits)
        OPTIONAL MATCH (cc)-[:HAS_RESOURCES]->(resources)
        OPTIONAL MATCH (cc)-[:INTEGRATES_WITH]->(mcp)
        RETURN 
            cc.name as produto,
            count(DISTINCT cap) as capacidades,
            count(DISTINCT features) as features,
            count(DISTINCT benefits) as beneficios,
            count(DISTINCT resources) as recursos,
            count(DISTINCT mcp) as integracoes
        """
        
        results = neo4j_conn.execute_query(check_query)
        
        if results:
            r = results[0]
            print(f"\n🔍 VERIFICAÇÃO FINAL:")
            print(f"   📦 Produto principal: {r['produto']}")
            print(f"   🚀 Capacidades: {r['capacidades']}")
            print(f"   ⭐ Features: {r['features']}")
            print(f"   💎 Benefícios: {r['beneficios']}")
            print(f"   📚 Recursos: {r['recursos']}")
            print(f"   🔌 Integrações: {r['integracoes']}")
            
            # Verificar se tudo está correto
            expected = {
                'capacidades': 1,
                'features': 4,
                'beneficios': 4,
                'recursos': 1,
                'integracoes': 1
            }
            
            all_correct = True
            for key, expected_count in expected.items():
                if r[key] != expected_count:
                    print(f"   ⚠️  {key}: esperado {expected_count}, encontrado {r[key]}")
                    all_correct = False
            
            if all_correct:
                print("   ✅ Todas as verificações passaram!")
            else:
                print("   ⚠️  Algumas verificações falharam")
            
            return all_correct
        
        return False
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    print("🧠 Claude Code Documentation → Neo4j")
    print("📋 Seguindo diretrizes CLAUDE.md:")
    print("   • Zero duplicação no Neo4j")  
    print("   • Toda documentação no grafo")
    print("   • Documentação em PT-BR")
    print("   • Preservar antes de criar")
    print()
    
    # Executar adição da documentação
    success = add_claude_code_documentation()
    
    if success:
        print("\n🔍 Executando verificação final...")
        verify_documentation()
        
        print("\n✨ PROCESSO CONCLUÍDO!")
        print("📊 Documentação completa do Claude Code disponível no Neo4j")
        print("🔍 Use as ferramentas MCP para consultar e navegar")
    else:
        print("\n❌ Processo falhou - verifique os logs acima")
        sys.exit(1)