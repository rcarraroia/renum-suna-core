#!/bin/bash

# Script para configurar a integração entre o backend Renum e o sistema Suna na VPS
# Autor: Kiro
# Data: 19/07/2025

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Script de Integração Renum-Suna ===${NC}"
echo -e "Este script configura a integração entre o backend Renum e o sistema Suna na VPS."

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Aviso: Este script deve ser executado como root para algumas operações.${NC}"
  echo -e "${YELLOW}Tentando continuar, mas algumas operações podem falhar.${NC}"
fi

# Definir diretórios
SUNA_DIR="/opt/suna"
RENUM_DIR="/opt/renum-backend"
BACKUP_DIR="/opt/backups/$(date +%Y%m%d_%H%M%S)"

# Criar diretório de backup
echo -e "${GREEN}Criando diretório de backup: $BACKUP_DIR${NC}"
mkdir -p $BACKUP_DIR

# Verificar se o diretório Suna existe
if [ ! -d "$SUNA_DIR" ]; then
  echo -e "${RED}Erro: Diretório Suna não encontrado em $SUNA_DIR${NC}"
  echo -e "${YELLOW}Por favor, especifique o diretório correto:${NC}"
  read -p "Diretório Suna: " SUNA_DIR
  
  if [ ! -d "$SUNA_DIR" ]; then
    echo -e "${RED}Erro: Diretório Suna não encontrado. Abortando.${NC}"
    exit 1
  fi
fi

# Backup do sistema Suna
echo -e "${GREEN}Fazendo backup do sistema Suna...${NC}"
cp -r $SUNA_DIR $BACKUP_DIR/suna
echo -e "${GREEN}Backup do Suna concluído em $BACKUP_DIR/suna${NC}"

# Criar diretório para o backend Renum se não existir
if [ ! -d "$RENUM_DIR" ]; then
  echo -e "${GREEN}Criando diretório para o backend Renum: $RENUM_DIR${NC}"
  mkdir -p $RENUM_DIR
else
  echo -e "${GREEN}Fazendo backup do backend Renum existente...${NC}"
  cp -r $RENUM_DIR $BACKUP_DIR/renum-backend
  echo -e "${GREEN}Backup do Renum concluído em $BACKUP_DIR/renum-backend${NC}"
  
  echo -e "${GREEN}Limpando diretório do backend Renum...${NC}"
  rm -rf $RENUM_DIR/*
fi

# Copiar arquivos do backend Renum para o diretório de destino
echo -e "${GREEN}Copiando arquivos do backend Renum para $RENUM_DIR...${NC}"
# Verificar se o diretório de origem foi especificado
if [ -z "$1" ]; then
  echo -e "${YELLOW}Diretório de origem não especificado. Por favor, forneça o caminho para os arquivos do backend Renum:${NC}"
  read -p "Diretório de origem: " SOURCE_DIR
else
  SOURCE_DIR=$1
fi

# Verificar se o diretório de origem existe
if [ ! -d "$SOURCE_DIR" ]; then
  echo -e "${RED}Erro: Diretório de origem não encontrado: $SOURCE_DIR${NC}"
  echo -e "${YELLOW}Por favor, copie manualmente os arquivos do backend Renum para $RENUM_DIR${NC}"
else
  echo -e "${GREEN}Copiando arquivos de $SOURCE_DIR para $RENUM_DIR...${NC}"
  cp -r $SOURCE_DIR/* $RENUM_DIR/
  echo -e "${GREEN}Arquivos copiados com sucesso!${NC}"
fi

# Configurar ambiente virtual Python
echo -e "${GREEN}Configurando ambiente virtual Python...${NC}"
cd $RENUM_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
echo -e "${GREEN}Configurando variáveis de ambiente...${NC}"
if [ ! -f "$RENUM_DIR/.env" ]; then
  echo -e "${YELLOW}Arquivo .env não encontrado. Criando a partir de .env.example...${NC}"
  if [ -f "$RENUM_DIR/.env.example" ]; then
    cp $RENUM_DIR/.env.example $RENUM_DIR/.env
    echo -e "${YELLOW}Por favor, edite o arquivo $RENUM_DIR/.env com as configurações corretas.${NC}"
  else
    echo -e "${RED}Arquivo .env.example não encontrado. Por favor, crie o arquivo .env manualmente.${NC}"
  fi
fi

# Aplicar esquema do banco de dados
echo -e "${GREEN}Aplicando esquema do banco de dados...${NC}"
cd $RENUM_DIR

# Instalar dependências necessárias para o script SQL
pip install supabase python-dotenv

# Executar o script SQL
echo -e "${GREEN}Executando script SQL para criar tabelas Renum...${NC}"
python scripts/execute_sql_direct.py scripts/create_renum_tables.sql

# Verificar resultado
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Esquema do banco de dados aplicado com sucesso!${NC}"
else
  echo -e "${RED}Erro ao aplicar esquema do banco de dados. Verifique os logs acima.${NC}"
  echo -e "${YELLOW}Você pode tentar aplicar o esquema manualmente usando o SQL Editor do Supabase.${NC}"
fi

# Configurar serviço systemd
echo -e "${GREEN}Configurando serviço systemd...${NC}"
cat > /etc/systemd/system/renum-backend.service << EOF
[Unit]
Description=Renum Backend Service
After=network.target

[Service]
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$RENUM_DIR
Environment="PATH=$RENUM_DIR/venv/bin"
ExecStart=$RENUM_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd
echo -e "${GREEN}Recarregando systemd...${NC}"
systemctl daemon-reload

# Habilitar e iniciar o serviço
echo -e "${GREEN}Habilitando e iniciando o serviço renum-backend...${NC}"
systemctl enable renum-backend
systemctl start renum-backend

# Configurar Nginx como proxy reverso
echo -e "${GREEN}Configurando Nginx como proxy reverso...${NC}"
if [ -d "/etc/nginx" ]; then
  cat > /etc/nginx/sites-available/renum-backend << EOF
server {
    listen 80;
    server_name api.renum.com.br; # Substitua pelo domínio real

    location / {
        proxy_pass http://localhost:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

  # Criar link simbólico
  ln -sf /etc/nginx/sites-available/renum-backend /etc/nginx/sites-enabled/

  # Testar configuração do Nginx
  nginx -t

  # Reiniciar Nginx
  systemctl restart nginx
else
  echo -e "${YELLOW}Nginx não encontrado. Pulando configuração do proxy reverso.${NC}"
fi

# Verificar status do serviço
echo -e "${GREEN}Verificando status do serviço renum-backend...${NC}"
systemctl status renum-backend

# Testar comunicação entre backends
echo -e "${GREEN}Testando comunicação com o backend Suna...${NC}"
SUNA_URL=$(grep SUNA_API_URL $RENUM_DIR/.env | cut -d '=' -f2)
if [ -z "$SUNA_URL" ]; then
  SUNA_URL="http://localhost:8000"
  echo -e "${YELLOW}SUNA_API_URL não encontrado no arquivo .env. Usando $SUNA_URL${NC}"
fi

echo -e "${GREEN}Testando conexão com $SUNA_URL/health...${NC}"
curl -s $SUNA_URL/health
if [ $? -eq 0 ]; then
  echo -e "${GREEN}Conexão com o backend Suna estabelecida com sucesso!${NC}"
else
  echo -e "${RED}Erro ao conectar com o backend Suna. Verifique se o serviço está em execução e se a URL está correta.${NC}"
fi

# Testar conexão com o Supabase
echo -e "${GREEN}Testando conexão com o Supabase...${NC}"
cd $RENUM_DIR
python -c "
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    print('Erro: SUPABASE_URL ou SUPABASE_KEY não encontrados no arquivo .env')
    exit(1)

try:
    supabase = create_client(supabase_url, supabase_key)
    result = supabase.table('renum_settings').select('*').limit(1).execute()
    print('Conexão com o Supabase estabelecida com sucesso!')
except Exception as e:
    print(f'Erro ao conectar com o Supabase: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}Conexão com o Supabase estabelecida com sucesso!${NC}"
else
  echo -e "${RED}Erro ao conectar com o Supabase. Verifique as credenciais no arquivo .env.${NC}"
fi

echo -e "${GREEN}=== Integração concluída! ===${NC}"
echo -e "O backend Renum está configurado e integrado com o sistema Suna."
echo -e "Backup do sistema original está disponível em: $BACKUP_DIR"
echo -e "Para verificar os logs do serviço: journalctl -u renum-backend -f"
echo -e ""
echo -e "${GREEN}=== Próximos Passos ===${NC}"
echo -e "1. Verifique se todas as tabelas com prefixo renum_ foram criadas no Supabase"
echo -e "2. Teste os endpoints da API Renum"
echo -e "3. Configure o frontend Renum para apontar para o backend Renum"