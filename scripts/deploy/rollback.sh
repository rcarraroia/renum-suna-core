#!/bin/bash

# Script de rollback para emergências
# Execute este script NA VPS quando precisar voltar para uma versão anterior

set -e

echo "🔄 Script de Rollback - Suna & Renum"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Função para listar backups
list_backups() {
    local project_dir=$1
    local service_name=$2
    
    echo -e "${BLUE}=== Backups disponíveis para $service_name ===${NC}"
    
    if [ -d "$project_dir" ]; then
        cd "$project_dir/.."
        backups=$(ls -dt ${service_name}_backup_* 2>/dev/null || echo "")
        
        if [ -z "$backups" ]; then
            log_warn "Nenhum backup encontrado para $service_name"
            return 1
        fi
        
        echo "Backups encontrados:"
        local i=1
        for backup in $backups; do
            backup_date=$(echo $backup | sed "s/${service_name}_backup_//")
            formatted_date=$(date -d "${backup_date:0:8} ${backup_date:9:2}:${backup_date:11:2}:${backup_date:13:2}" "+%d/%m/%Y %H:%M:%S" 2>/dev/null || echo "$backup_date")
            echo "  $i) $backup ($formatted_date)"
            i=$((i+1))
        done
        
        return 0
    else
        log_error "Diretório $project_dir não encontrado"
        return 1
    fi
}

# Função para fazer rollback
do_rollback() {
    local project_dir=$1
    local service_name=$2
    local backup_choice=$3
    
    cd "$project_dir/.."
    backups=($(ls -dt ${service_name}_backup_* 2>/dev/null))
    
    if [ -z "$backup_choice" ] || [ "$backup_choice" -lt 1 ] || [ "$backup_choice" -gt ${#backups[@]} ]; then
        log_error "Escolha inválida"
        return 1
    fi
    
    selected_backup=${backups[$((backup_choice-1))]}
    
    log_warn "Fazendo rollback para: $selected_backup"
    
    # Criar backup da versão atual antes do rollback
    current_backup="${service_name}_backup_before_rollback_$(date +%Y%m%d_%H%M%S)"
    log_info "Criando backup da versão atual: $current_backup"
    cp -r "$project_dir" "$current_backup"
    
    # Parar serviço
    log_info "Parando serviço $service_name..."
    sudo systemctl stop $service_name
    
    # Remover versão atual
    log_info "Removendo versão atual..."
    rm -rf "$project_dir"
    
    # Restaurar backup
    log_info "Restaurando backup..."
    cp -r "$selected_backup" "$project_dir"
    
    # Ajustar permissões
    sudo chown -R deploy:deploy "$project_dir"
    
    # Reinstalar dependências se necessário
    if [ -f "$project_dir/requirements.txt" ]; then
        log_info "Reinstalando dependências..."
        cd "$project_dir"
        source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Reiniciar serviço
    log_info "Reiniciando serviço $service_name..."
    sudo systemctl start $service_name
    
    # Verificar status
    sleep 5
    if systemctl is-active --quiet $service_name; then
        log_info "✅ Rollback concluído com sucesso!"
        sudo systemctl status $service_name --no-pager
    else
        log_error "❌ Falha no rollback!"
        sudo systemctl status $service_name --no-pager
        return 1
    fi
}

# Menu principal
echo "Escolha o serviço para rollback:"
echo "1) Suna Backend"
echo "2) Renum Backend"
echo "3) Ambos"
echo "0) Sair"
echo ""
read -p "Opção: " service_choice

case $service_choice in
    1)
        if list_backups "/var/www/renum-suna-core/backend" "backend"; then
            echo ""
            read -p "Escolha o backup (número): " backup_choice
            do_rollback "/var/www/renum-suna-core/backend" "suna-backend" "$backup_choice"
        fi
        ;;
    2)
        if list_backups "/var/www/renum-suna-core/renum-backend" "renum-backend"; then
            echo ""
            read -p "Escolha o backup (número): " backup_choice
            do_rollback "/var/www/renum-suna-core/renum-backend" "renum-backend" "$backup_choice"
        fi
        ;;
    3)
        echo -e "${YELLOW}Rollback de ambos os serviços:${NC}"
        echo ""
        
        # Suna
        if list_backups "/var/www/renum-suna-core/backend" "backend"; then
            echo ""
            read -p "Escolha o backup para Suna (número): " suna_backup
            do_rollback "/var/www/renum-suna-core/backend" "suna-backend" "$suna_backup"
        fi
        
        echo ""
        
        # Renum
        if list_backups "/var/www/renum-suna-core/renum-backend" "renum-backend"; then
            echo ""
            read -p "Escolha o backup para Renum (número): " renum_backup
            do_rollback "/var/www/renum-suna-core/renum-backend" "renum-backend" "$renum_backup"
        fi
        ;;
    0)
        echo "Saindo..."
        exit 0
        ;;
    *)
        log_error "Opção inválida"
        exit 1
        ;;
esac

echo ""
log_info "🎯 Rollback concluído!"
echo ""
echo "Para monitorar os serviços:"
echo "./monitor-deployment.sh"