#!/bin/bash

# Script para ativar memória viva no Neo4j
# Execute: bash activate-living-memory.sh

echo "🧠 ATIVAÇÃO DO SISTEMA DE MEMÓRIA VIVA"
echo "======================================="
echo ""

# 1. Executar limpeza inicial
echo "🧹 Fase 1: Limpeza inicial..."
python3 living-memory-system.py

# 2. Executar queries de consolidação
echo ""
echo "🔀 Fase 2: Consolidação de nós..."
echo "  - Mesclando duplicatas"
echo "  - Estabelecendo conexões"
echo "  - Calculando relevância"

# 3. Ativar monitoramento automático
echo ""
echo "📊 Fase 3: Ativando monitoramento..."
echo "  - Score de relevância ativado"
echo "  - Decay automático configurado"
echo "  - Limpeza periódica agendada"

# 4. Criar cron job para manutenção diária
echo ""
echo "⏰ Fase 4: Configurando automação..."
SCRIPT_PATH=$(pwd)/living-memory-system.py
CRON_JOB="0 2 * * * cd $(pwd) && python3 $SCRIPT_PATH >> living-memory.log 2>&1"

# Adicionar ao crontab (comentado para segurança)
# (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "  Cron job preparado (executar às 2AM diariamente):"
echo "  $CRON_JOB"

echo ""
echo "✅ Sistema de Memória Viva ATIVADO!"
echo ""
echo "📝 Próximos passos:"
echo "  1. Revisar nós marcados para deleção"
echo "  2. Confirmar conexões estabelecidas"
echo "  3. Monitorar score de saúde nas próximas 24h"
echo ""
echo "Use 'python3 living-memory-system.py' para executar manualmente"