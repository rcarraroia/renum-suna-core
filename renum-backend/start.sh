#!/bin/bash

# Script de inicialização do backend Renum
# Autor: Kiro
# Data: 19/07/2025

# Configurações
PORT=9000
HOST="0.0.0.0"
WORKERS=4
LOG_LEVEL="info"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando Backend Renum ===${NC}"

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${RED}Erro: Arquivo .env não encontrado!${NC}"
    echo -e "${YELLOW}Copie o arquivo .env.example para .env e configure as variáveis de ambiente.${NC}"
    exit 1
fi

# Verificar se o ambiente virtual está ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Aviso: Ambiente virtual não detectado.${NC}"
    echo -e "${YELLOW}Recomenda-se usar um ambiente virtual para execução.${NC}"
    
    # Verificar se existe um ambiente virtual
    if [ -d "venv" ]; then
        echo -e "${GREEN}Ativando ambiente virtual existente...${NC}"
        source venv/bin/activate
    fi
fi

# Limpar arquivos __pycache__
echo -e "${GREEN}Limpando arquivos de cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} +

# Iniciar o servidor
echo -e "${GREEN}Iniciando servidor na porta $PORT...${NC}"
echo -e "${GREEN}Acesse: http://$HOST:$PORT/docs para a documentação da API${NC}"
echo -e "${GREEN}Pressione Ctrl+C para encerrar o servidor${NC}"

# Executar com uvicorn
uvicorn app.main:app --host $HOST --port $PORT --workers $WORKERS --log-level $LOG_LEVEL