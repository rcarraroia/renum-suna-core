#!/bin/bash

# Script para monitorar deployments em tempo real
# Execute este script NA VPS

echo "📊 Monitor de Deploy - Suna & Renum"
echo "Pressione Ctrl+C para sair"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função para mostrar status
show_status() {
    clear
    echo -e "${BLUE}=== Monitor de Deploy - $(date) ===${NC}"
    echo ""
    
    # Status dos serviços
    echo -e "${YELLOW}📋 Status dos Serviços:${NC}"
    
    for service in "suna-backend" "renum-backend"; do
        if systemctl is-active --quiet $service; then
            echo -e "  ${GREEN}✓${NC} $service: ATIVO"
        else
            echo -e "  ${RED}✗${NC} $service: INATIVO"
        fi
    done
    
    echo ""
    
    # Status das portas
    echo -e "${YELLOW}🌐 Status das Portas:${NC}"
    
    for port in "8000" "9000"; do
        if netstat -tlnp | grep -q ":$port "; then
            echo -e "  ${GREEN}✓${NC} Porta $port: ABERTA"
        else
            echo -e "  ${RED}✗${NC} Porta $port: FECHADA"
        fi
    done
    
    echo ""
    
    # Health checks
    echo -e "${YELLOW}🏥 Health Checks:${NC}"
    
    # Suna
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Suna Backend: OK"
    elif curl -f -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "  ${YELLOW}!${NC} Suna Backend: Respondendo (sem /health)"
    else
        echo -e "  ${RED}✗${NC} Suna Backend: FALHA"
    fi
    
    # Renum
    if curl -f -s http://localhost:9000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Renum Backend: OK"
    elif curl -f -s http://localhost:9000/ > /dev/null 2>&1; then
        echo -e "  ${YELLOW}!${NC} Renum Backend: Respondendo (sem /health)"
    else
        echo -e "  ${RED}✗${NC} Renum Backend: FALHA"
    fi
    
    echo ""
    
    # Uso de recursos
    echo -e "${YELLOW}💻 Uso de Recursos:${NC}"
    
    # CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "  CPU: ${cpu_usage}%"
    
    # Memória
    mem_info=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    echo -e "  Memória: ${mem_info}"
    
    # Disco
    disk_usage=$(df -h / | awk 'NR==2{print $5}')
    echo -e "  Disco: ${disk_usage}"
    
    echo ""
    
    # Últimos logs (últimas 5 linhas de cada serviço)
    echo -e "${YELLOW}📝 Últimos Logs:${NC}"
    
    echo -e "${BLUE}Suna Backend:${NC}"
    sudo journalctl -u suna-backend --no-pager -n 3 --since "5 minutes ago" | tail -3 | sed 's/^/  /'
    
    echo -e "${BLUE}Renum Backend:${NC}"
    sudo journalctl -u renum-backend --no-pager -n 3 --since "5 minutes ago" | tail -3 | sed 's/^/  /'
    
    echo ""
    echo -e "${YELLOW}Atualizando em 10 segundos... (Ctrl+C para sair)${NC}"
}

# Loop principal
while true; do
    show_status
    sleep 10
done