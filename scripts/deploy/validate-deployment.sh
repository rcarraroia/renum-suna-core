#!/bin/bash

# Script para validar se o deploy automático está funcionando
# Execute este script NA VPS

set -e

echo "🔍 Validando configuração de deploy automático..."

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Função para verificar serviço
check_service() {
    local service_name=$1
    local port=$2
    
    echo ""
    echo "Verificando $service_name..."
    
    # Verificar se o serviço existe
    if ! systemctl list-unit-files | grep -q "$service_name.service"; then
        log_error "Serviço $service_name não encontrado"
        return 1
    fi
    
    # Verificar se está ativo
    if systemctl is-active --quiet $service_name; then
        log_info "Serviço $service_name está ativo"
    else
        log_error "Serviço $service_name não está ativo"
        sudo systemctl status $service_name --no-pager
        return 1
    fi
    
    # Verificar se está habilitado
    if systemctl is-enabled --quiet $service_name; then
        log_info "Serviço $service_name está habilitado para inicialização"
    else
        log_warn "Serviço $service_name não está habilitado para inicialização"
    fi
    
    # Verificar porta
    if netstat -tlnp | grep -q ":$port "; then
        log_info "Porta $port está sendo usada"
    else
        log_error "Porta $port não está sendo usada"
        return 1
    fi
    
    # Health check
    if curl -f -s http://localhost:$port/health > /dev/null 2>&1; then
        log_info "Health check em localhost:$port/health passou"
    elif curl -f -s http://localhost:$port/ > /dev/null 2>&1; then
        log_info "Servidor em localhost:$port está respondendo"
    else
        log_warn "Health check em localhost:$port falhou"
    fi
}

# Verificar usuário deploy
echo "Verificando usuário deploy..."
if id "deploy" &>/dev/null; then
    log_info "Usuário deploy existe"
else
    log_error "Usuário deploy não existe"
    exit 1
fi

# Verificar chaves SSH
echo ""
echo "Verificando chaves SSH..."
if [ -f "/home/deploy/.ssh/deploy_key" ]; then
    log_info "Chave SSH privada existe"
else
    log_error "Chave SSH privada não encontrada"
fi

if [ -f "/home/deploy/.ssh/deploy_key.pub" ]; then
    log_info "Chave SSH pública existe"
else
    log_error "Chave SSH pública não encontrada"
fi

if [ -f "/home/deploy/.ssh/authorized_keys" ]; then
    log_info "Arquivo authorized_keys existe"
else
    log_error "Arquivo authorized_keys não encontrado"
fi

# Verificar diretórios
echo ""
echo "Verificando diretórios..."
for dir in "/var/www/renum-suna-core"; do
    if [ -d "$dir" ]; then
        log_info "Diretório $dir existe"
        if [ -O "$dir" ] || [ -G "$dir" ]; then
            log_info "Permissões corretas em $dir"
        else
            log_warn "Verifique permissões em $dir"
        fi
        
        # Verificar subdiretórios
        for subdir in "$dir/backend" "$dir/renum-backend"; do
            if [ -d "$subdir" ]; then
                log_info "Subdiretório $subdir existe"
            else
                log_error "Subdiretório $subdir não existe"
            fi
        done
    else
        log_error "Diretório $dir não existe"
    fi
done

# Verificar repositório Git
echo ""
echo "Verificando repositório Git..."
repo="/var/www/renum-suna-core"
if [ -d "$repo/.git" ]; then
    log_info "Repositório Git em $repo está configurado"
    cd "$repo"
    current_branch=$(git branch --show-current)
    log_info "Branch atual: $current_branch"
    
    # Verificar se pode fazer pull
    if git fetch --dry-run > /dev/null 2>&1; then
        log_info "Conexão com repositório remoto OK"
    else
        log_warn "Problema na conexão com repositório remoto"
    fi
else
    log_error "Repositório Git não encontrado em $repo"
fi

# Verificar serviços
check_service "suna-backend" "8000"
check_service "renum-backend" "9000"

# Verificar Nginx
echo ""
echo "Verificando Nginx..."
if systemctl is-active --quiet nginx; then
    log_info "Nginx está ativo"
    
    # Verificar configurações
    if [ -f "/etc/nginx/sites-enabled/suna-backend" ]; then
        log_info "Configuração Nginx para Suna está ativa"
    else
        log_warn "Configuração Nginx para Suna não encontrada"
    fi
    
    if [ -f "/etc/nginx/sites-enabled/renum-backend" ]; then
        log_info "Configuração Nginx para Renum está ativa"
    else
        log_warn "Configuração Nginx para Renum não encontrada"
    fi
else
    log_error "Nginx não está ativo"
fi

# Verificar firewall
echo ""
echo "Verificando firewall..."
if command -v ufw > /dev/null; then
    if ufw status | grep -q "Status: active"; then
        log_info "UFW está ativo"
        if ufw status | grep -q "22/tcp"; then
            log_info "Porta SSH (22) está aberta"
        else
            log_warn "Porta SSH (22) pode não estar aberta"
        fi
    else
        log_warn "UFW não está ativo"
    fi
else
    log_warn "UFW não está instalado"
fi

# Verificar Python e dependências
echo ""
echo "Verificando ambientes Python..."
for backend in "/var/www/renum-suna-core/backend" "/var/www/renum-suna-core/renum-backend"; do
    if [ -d "$backend/venv" ]; then
        log_info "Ambiente virtual existe em $backend"
        
        # Verificar se pode ativar
        if source "$backend/venv/bin/activate" 2>/dev/null; then
            log_info "Ambiente virtual pode ser ativado"
            
            # Verificar dependências principais
            if python -c "import fastapi" 2>/dev/null; then
                log_info "FastAPI está instalado"
            else
                log_error "FastAPI não está instalado"
            fi
            
            deactivate 2>/dev/null || true
        else
            log_error "Não foi possível ativar ambiente virtual"
        fi
    else
        log_error "Ambiente virtual não encontrado em $backend"
    fi
done

echo ""
echo "🎯 Validação concluída!"
echo ""
echo "Para testar o deploy automático:"
echo "1. Faça um commit nos repositórios"
echo "2. Verifique os logs do GitHub Actions"
echo "3. Monitore os logs dos serviços: sudo journalctl -u suna-backend -f"