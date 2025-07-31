#!/bin/bash

# Script para configurar deploy automático na VPS
# Execute este script NA VPS como usuário não-root

set -e

echo "🚀 Configurando deploy automático na VPS..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log colorido
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se está rodando como root
if [ "$EUID" -eq 0 ]; then
    log_error "Não execute este script como root! Use um usuário não-root."
    exit 1
fi

# Criar usuário de deploy se não existir
DEPLOY_USER="deploy"
if ! id "$DEPLOY_USER" &>/dev/null; then
    log_info "Criando usuário de deploy..."
    sudo useradd -m -s /bin/bash $DEPLOY_USER
    sudo usermod -aG sudo $DEPLOY_USER
fi

# Configurar diretórios
log_info "Configurando diretórios..."
sudo mkdir -p /var/www/renum-suna-core
sudo chown -R $DEPLOY_USER:$DEPLOY_USER /var/www/renum-suna-core

# Gerar chave SSH para deploy
log_info "Gerando chave SSH para deploy..."
sudo -u $DEPLOY_USER ssh-keygen -t ed25519 -C "deploy@$(hostname)" -f /home/$DEPLOY_USER/.ssh/deploy_key -N ""

# Configurar authorized_keys
log_info "Configurando authorized_keys..."
sudo -u $DEPLOY_USER mkdir -p /home/$DEPLOY_USER/.ssh
sudo -u $DEPLOY_USER chmod 700 /home/$DEPLOY_USER/.ssh
sudo -u $DEPLOY_USER cp /home/$DEPLOY_USER/.ssh/deploy_key.pub /home/$DEPLOY_USER/.ssh/authorized_keys
sudo -u $DEPLOY_USER chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys

# Configurar SSH
log_info "Configurando SSH..."
sudo tee -a /etc/ssh/sshd_config > /dev/null <<EOF

# Deploy configuration
Match User $DEPLOY_USER
    PasswordAuthentication no
    PubkeyAuthentication yes
    AuthorizedKeysFile /home/$DEPLOY_USER/.ssh/authorized_keys
EOF

sudo systemctl restart sshd

# Instalar dependências necessárias
log_info "Instalando dependências..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl nginx

# Configurar firewall para GitHub Actions IPs (opcional)
log_info "Configurando firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Criar serviços systemd para os backends
log_info "Criando serviços systemd..."

# Suna Backend Service
sudo tee /etc/systemd/system/suna-backend.service > /dev/null <<EOF
[Unit]
Description=Suna Backend API
After=network.target

[Service]
Type=exec
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=/var/www/renum-suna-core/backend
Environment=PATH=/var/www/renum-suna-core/backend/venv/bin
ExecStart=/var/www/renum-suna-core/backend/venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Renum Backend Service
sudo tee /etc/systemd/system/renum-backend.service > /dev/null <<EOF
[Unit]
Description=Renum Backend API
After=network.target

[Service]
Type=exec
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=/var/www/renum-suna-core/renum-backend
Environment=PATH=/var/www/renum-suna-core/renum-backend/venv/bin
ExecStart=/var/www/renum-suna-core/renum-backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable suna-backend
sudo systemctl enable renum-backend

# Mostrar informações importantes
log_info "✅ Configuração concluída!"
echo ""
log_warn "IMPORTANTE: Adicione estas informações aos GitHub Secrets:"
echo ""
echo "VPS_HOST: $(curl -s ifconfig.me)"
echo "VPS_USER: $DEPLOY_USER"
echo "VPS_PORT: 22"
echo ""
echo "VPS_SSH_KEY: (conteúdo da chave privada abaixo)"
echo "----------------------------------------"
sudo -u $DEPLOY_USER cat /home/$DEPLOY_USER/.ssh/deploy_key
echo "----------------------------------------"
echo ""
log_warn "Próximos passos:"
echo "1. Clone o repositório em /var/www/renum-suna-core"
echo "   git clone https://github.com/rcarraroia/renum-suna-core.git /var/www/renum-suna-core"
echo "2. Configure os ambientes virtuais Python nos subdiretórios"
echo "3. Configure os arquivos .env"
echo "4. Adicione os secrets no GitHub"
echo "5. Teste o deploy manual primeiro"