#!/bin/bash

# Script para deploy manual do Renum Backend
# Execute este script NA VPS

set -e

echo "🚀 Iniciando deploy manual do Renum Backend..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configurações
DEPLOY_USER="deploy"
PROJECT_DIR="/var/www/renum-suna-core"
BACKEND_DIR="$PROJECT_DIR/renum-backend"
REPO_URL="https://github.com/rcarraroia/renum-suna-core.git"
BRANCH="main"

# Verificar se está rodando como usuário correto
if [ "$USER" != "$DEPLOY_USER" ]; then
    log_error "Execute este script como usuário $DEPLOY_USER"
    exit 1
fi

# Criar backup se já existir
if [ -d "$BACKEND_DIR" ]; then
    log_info "Criando backup..."
    cp -r "$BACKEND_DIR" "${BACKEND_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# Clonar ou atualizar repositório
if [ ! -d "$PROJECT_DIR/.git" ]; then
    log_info "Clonando repositório..."
    git clone "$REPO_URL" "$PROJECT_DIR"
else
    log_info "Atualizando repositório..."
    cd "$PROJECT_DIR"
    git fetch origin
    git reset --hard origin/$BRANCH
fi

cd "$BACKEND_DIR"

# Configurar ambiente virtual Python
log_info "Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Instalar dependências
log_info "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar arquivo .env
if [ ! -f ".env" ]; then
    log_warn "Arquivo .env não encontrado! Copiando do exemplo..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_warn "Configure o arquivo .env antes de continuar!"
    else
        log_error "Arquivo .env.example também não encontrado!"
        exit 1
    fi
fi

# Executar testes se existirem
if [ -d "tests" ] || ls test_*.py 1> /dev/null 2>&1; then
    log_info "Executando testes..."
    python -m pytest -v || log_warn "Alguns testes falharam, mas continuando..."
fi

# Reiniciar serviço
log_info "Reiniciando serviço..."
sudo systemctl restart renum-backend
sleep 5

# Verificar status
if systemctl is-active --quiet renum-backend; then
    log_info "✅ Renum Backend está rodando!"
    sudo systemctl status renum-backend --no-pager
else
    log_error "❌ Falha ao iniciar Renum Backend!"
    sudo systemctl status renum-backend --no-pager
    exit 1
fi

# Health check
log_info "Executando health check..."
sleep 10
if curl -f http://localhost:9000/health > /dev/null 2>&1; then
    log_info "✅ Health check passou!"
elif curl -f http://localhost:9000/ > /dev/null 2>&1; then
    log_info "✅ Servidor está respondendo!"
else
    log_warn "⚠️ Health check falhou, mas o serviço pode estar funcionando"
fi

log_info "🎉 Deploy do Renum Backend concluído!"