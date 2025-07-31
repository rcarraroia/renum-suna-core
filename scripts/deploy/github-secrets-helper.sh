#!/bin/bash

# Script helper para configurar GitHub Secrets
# Execute este script NA VPS após executar setup-vps-deploy.sh

echo "🔐 GitHub Secrets Helper"
echo "Este script te ajudará a configurar os secrets necessários no GitHub"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Obter informações da VPS
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "ERRO_AO_OBTER_IP")
VPS_USER="deploy"
VPS_PORT="22"

echo -e "${BLUE}=== Informações para GitHub Secrets ===${NC}"
echo ""

echo -e "${YELLOW}1. VPS_HOST:${NC}"
echo "$VPS_IP"
echo ""

echo -e "${YELLOW}2. VPS_USER:${NC}"
echo "$VPS_USER"
echo ""

echo -e "${YELLOW}3. VPS_PORT:${NC}"
echo "$VPS_PORT"
echo ""

echo -e "${YELLOW}4. VPS_SSH_KEY:${NC}"
echo "Copie TODO o conteúdo abaixo (incluindo as linhas BEGIN e END):"
echo ""
echo "----------------------------------------"
if [ -f "/home/deploy/.ssh/deploy_key" ]; then
    cat /home/deploy/.ssh/deploy_key
else
    echo "ERRO: Chave SSH não encontrada!"
    echo "Execute primeiro: ./setup-vps-deploy.sh"
fi
echo "----------------------------------------"
echo ""

echo -e "${GREEN}=== Como configurar no GitHub ===${NC}"
echo ""
echo "Para CADA repositório (Suna e Renum):"
echo "1. Vá para: Settings → Secrets and variables → Actions"
echo "2. Clique em 'New repository secret'"
echo "3. Adicione os 4 secrets acima"
echo ""

echo -e "${YELLOW}=== Teste de Conectividade ===${NC}"
echo ""
echo "Para testar se o GitHub Actions conseguirá conectar:"
echo ""
echo "ssh -i /home/deploy/.ssh/deploy_key deploy@$VPS_IP"
echo ""

echo -e "${GREEN}=== URLs dos Repositórios ===${NC}"
echo ""
echo "Configure os workflows nos repositórios:"
echo ""
echo "Suna: https://github.com/SEU_USUARIO/suna/settings/secrets/actions"
echo "Renum: https://github.com/SEU_USUARIO/renum/settings/secrets/actions"
echo ""

echo -e "${BLUE}=== Próximos Passos ===${NC}"
echo ""
echo "1. ✅ Configure os secrets no GitHub"
echo "2. ✅ Teste o deploy manual primeiro:"
echo "   ./manual-deploy-suna.sh"
echo "   ./manual-deploy-renum.sh"
echo "3. ✅ Faça um commit para testar o deploy automático"
echo "4. ✅ Monitore com: ./monitor-deployment.sh"
echo ""

# Verificar se pode conectar via SSH
echo -e "${YELLOW}=== Teste de SSH Local ===${NC}"
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i /home/deploy/.ssh/deploy_key deploy@localhost "echo 'SSH OK'" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} SSH local funcionando"
else
    echo -e "${RED}✗${NC} Problema com SSH local"
fi

echo ""
echo "🎯 Configuração de secrets pronta!"