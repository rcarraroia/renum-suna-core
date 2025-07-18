#!/usr/bin/env python3
"""
Script para configurar uma solução básica de backup para os serviços Renum e Suna na VPS.
Este script cria scripts de backup e configura jobs de cron para executá-los regularmente.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Setup basic backup solution')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--backup-dir', default='/var/backups/renum-suna', help='Directory to store backups')
    parser.add_argument('--retention-days', type=int, default=7, help='Number of days to keep backups')
    parser.add_argument('--dry-run', action='store_true', help='Print commands without executing them')
    return parser.parse_args()

def create_ssh_client(host, port, user, key_file=None):
    """Create an SSH client connection."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if key_file:
            key_path = os.path.expanduser(key_file)
            if not os.path.exists(key_path):
                print(f"Error: Key file {key_path} does not exist.")
                sys.exit(1)
            
            try:
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(host, port=port, username=user, pkey=key)
            except paramiko.ssh_exception.PasswordRequiredException:
                passphrase = getpass.getpass("Enter passphrase for key: ")
                key = paramiko.RSAKey.from_private_key_file(key_path, password=passphrase)
                client.connect(host, port=port, username=user, pkey=key)
        else:
            password = getpass.getpass(f"Enter password for {user}@{host}: ")
            client.connect(host, port=port, username=user, password=password)
        
        return client
    except Exception as e:
        print(f"Error connecting to {host}: {str(e)}")
        sys.exit(1)

def execute_command(client, command, dry_run=False):
    """Execute a command on the remote server."""
    if dry_run:
        print(f"[DRY RUN] Would execute: {command}")
        return "dry-run-output"
    
    try:
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if error and not output:
            print(f"Error executing command: {error}")
        
        return output
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return None

def upload_file(client, local_path, remote_path, dry_run=False):
    """Upload a file to the remote server."""
    if dry_run:
        print(f"[DRY RUN] Would upload {local_path} to {remote_path}")
        return True
    
    try:
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False

def create_backup_directory(client, backup_dir, dry_run=False):
    """Create backup directory on the remote server."""
    print(f"Creating backup directory: {backup_dir}")
    execute_command(client, f"mkdir -p {backup_dir}", dry_run)
    execute_command(client, f"chmod 700 {backup_dir}", dry_run)
    return backup_dir

def create_postgres_backup_script(client, backup_dir, retention_days, dry_run=False):
    """Create PostgreSQL backup script."""
    script_path = "/usr/local/bin/backup_postgres.sh"
    script_content = f"""#!/bin/bash
# Script para backup do PostgreSQL
# Criado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

# Configurações
BACKUP_DIR="{backup_dir}/postgres"
RETENTION_DAYS={retention_days}
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup_$DATE.log"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Função para log
log() {{
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$LOG_FILE"
}}

log "Iniciando backup do PostgreSQL"

# Encontrar contêineres PostgreSQL
POSTGRES_CONTAINERS=$(docker ps --format '{{{{.Names}}}}' | grep -E 'postgres|supabase')

if [ -z "$POSTGRES_CONTAINERS" ]; then
    log "Nenhum contêiner PostgreSQL encontrado"
    exit 1
fi

log "Contêineres PostgreSQL encontrados: $POSTGRES_CONTAINERS"

# Realizar backup de cada contêiner
for CONTAINER in $POSTGRES_CONTAINERS; do
    log "Processando contêiner: $CONTAINER"
    
    # Obter variáveis de ambiente do contêiner
    DB_USER=$(docker exec $CONTAINER bash -c 'echo $POSTGRES_USER' 2>/dev/null || echo "postgres")
    DB_NAME=$(docker exec $CONTAINER bash -c 'echo $POSTGRES_DB' 2>/dev/null || echo "postgres")
    
    log "Usuário: $DB_USER, Banco: $DB_NAME"
    
    # Criar diretório para este contêiner
    CONTAINER_BACKUP_DIR="$BACKUP_DIR/$CONTAINER"
    mkdir -p "$CONTAINER_BACKUP_DIR"
    
    # Backup do banco de dados
    BACKUP_FILE="$CONTAINER_BACKUP_DIR/${{DB_NAME}}_${{DATE}}.sql"
    log "Criando backup em $BACKUP_FILE"
    
    docker exec $CONTAINER pg_dump -U $DB_USER -d $DB_NAME -f /tmp/backup.sql
    docker cp $CONTAINER:/tmp/backup.sql $BACKUP_FILE
    docker exec $CONTAINER rm /tmp/backup.sql
    
    # Comprimir backup
    log "Comprimindo backup"
    gzip -f $BACKUP_FILE
    
    log "Backup do contêiner $CONTAINER concluído"
done

# Remover backups antigos
log "Removendo backups com mais de $RETENTION_DAYS dias"
find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

log "Backup do PostgreSQL concluído com sucesso"
"""
    
    print(f"Creating PostgreSQL backup script: {script_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create script: {script_path}")
        print("Script content:")
        print(script_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_postgres.sh"
        with open(temp_path, "w") as f:
            f.write(script_content)
        
        # Upload to server
        upload_file(client, temp_path, script_path, dry_run)
        os.remove(temp_path)
        
        # Make executable
        execute_command(client, f"chmod +x {script_path}", dry_run)
    
    return script_path

def create_docker_volumes_backup_script(client, backup_dir, retention_days, dry_run=False):
    """Create Docker volumes backup script."""
    script_path = "/usr/local/bin/backup_volumes.sh"
    script_content = f"""#!/bin/bash
# Script para backup de volumes Docker
# Criado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

# Configurações
BACKUP_DIR="{backup_dir}/volumes"
RETENTION_DAYS={retention_days}
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup_$DATE.log"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Função para log
log() {{
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$LOG_FILE"
}}

log "Iniciando backup de volumes Docker"

# Listar volumes
VOLUMES=$(docker volume ls --format '{{{{.Name}}}}')

if [ -z "$VOLUMES" ]; then
    log "Nenhum volume Docker encontrado"
    exit 1
fi

log "Volumes encontrados: $VOLUMES"

# Criar diretório temporário
TEMP_DIR="/tmp/volume_backup_$DATE"
mkdir -p "$TEMP_DIR"

# Backup de cada volume
for VOLUME in $VOLUMES; do
    log "Processando volume: $VOLUME"
    
    # Criar diretório para este volume
    VOLUME_BACKUP_DIR="$BACKUP_DIR/$VOLUME"
    mkdir -p "$VOLUME_BACKUP_DIR"
    
    # Nome do arquivo de backup
    BACKUP_FILE="$VOLUME_BACKUP_DIR/${{VOLUME}}_${{DATE}}.tar.gz"
    log "Criando backup em $BACKUP_FILE"
    
    # Criar contêiner temporário para backup
    log "Criando contêiner temporário para backup"
    docker run --rm -v $VOLUME:/volume -v $TEMP_DIR:/backup alpine tar -czf /backup/$VOLUME.tar.gz -C /volume ./
    
    # Mover arquivo de backup
    mv "$TEMP_DIR/$VOLUME.tar.gz" "$BACKUP_FILE"
    
    log "Backup do volume $VOLUME concluído"
done

# Remover diretório temporário
rm -rf "$TEMP_DIR"

# Remover backups antigos
log "Removendo backups com mais de $RETENTION_DAYS dias"
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

log "Backup de volumes Docker concluído com sucesso"
"""
    
    print(f"Creating Docker volumes backup script: {script_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create script: {script_path}")
        print("Script content:")
        print(script_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_volumes.sh"
        with open(temp_path, "w") as f:
            f.write(script_content)
        
        # Upload to server
        upload_file(client, temp_path, script_path, dry_run)
        os.remove(temp_path)
        
        # Make executable
        execute_command(client, f"chmod +x {script_path}", dry_run)
    
    return script_path

def create_supabase_backup_script(client, backup_dir, retention_days, dry_run=False):
    """Create Supabase backup script."""
    script_path = "/usr/local/bin/backup_supabase.sh"
    script_content = f"""#!/bin/bash
# Script para backup do Supabase
# Criado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

# Configurações
BACKUP_DIR="{backup_dir}/supabase"
RETENTION_DAYS={retention_days}
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup_$DATE.log"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Função para log
log() {{
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$LOG_FILE"
}}

log "Iniciando backup do Supabase"

# Encontrar contêineres com variáveis de ambiente do Supabase
CONTAINERS=$(docker ps -a --format '{{{{.Names}}}}')

for CONTAINER in $CONTAINERS; do
    # Verificar se o contêiner tem variáveis de ambiente do Supabase
    SUPABASE_ENV=$(docker exec $CONTAINER env 2>/dev/null | grep -i supabase || echo "")
    
    if [ -n "$SUPABASE_ENV" ]; then
        log "Contêiner com variáveis do Supabase encontrado: $CONTAINER"
        
        # Extrair URL e chave do Supabase
        SUPABASE_URL=$(docker exec $CONTAINER env | grep SUPABASE_URL | cut -d= -f2 || echo "")
        SUPABASE_KEY=$(docker exec $CONTAINER env | grep SUPABASE_KEY | cut -d= -f2 || echo "")
        
        if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_KEY" ]; then
            log "URL do Supabase: $SUPABASE_URL"
            log "Chave do Supabase encontrada (não exibida por segurança)"
            
            # Criar diretório para este contêiner
            CONTAINER_BACKUP_DIR="$BACKUP_DIR/$CONTAINER"
            mkdir -p "$CONTAINER_BACKUP_DIR"
            
            # Salvar variáveis de ambiente
            ENV_FILE="$CONTAINER_BACKUP_DIR/supabase_env_$DATE.txt"
            log "Salvando variáveis de ambiente em $ENV_FILE"
            docker exec $CONTAINER env | grep -i supabase > "$ENV_FILE"
            
            # Tentar fazer backup usando API do Supabase (simulado)
            log "Nota: Este script não realiza backup real do Supabase."
            log "Para implementar backup real, é necessário usar a API do Supabase ou ferramentas específicas."
            log "Consulte a documentação do Supabase para mais informações."
        else
            log "URL ou chave do Supabase não encontrada no contêiner $CONTAINER"
        fi
    fi
done

# Remover backups antigos
log "Removendo backups com mais de $RETENTION_DAYS dias"
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

log "Backup do Supabase concluído"
"""
    
    print(f"Creating Supabase backup script: {script_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create script: {script_path}")
        print("Script content:")
        print(script_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_supabase.sh"
        with open(temp_path, "w") as f:
            f.write(script_content)
        
        # Upload to server
        upload_file(client, temp_path, script_path, dry_run)
        os.remove(temp_path)
        
        # Make executable
        execute_command(client, f"chmod +x {script_path}", dry_run)
    
    return script_path

def create_master_backup_script(client, backup_dir, dry_run=False):
    """Create master backup script that runs all backup scripts."""
    script_path = "/usr/local/bin/backup_all.sh"
    script_content = f"""#!/bin/bash
# Script mestre para executar todos os backups
# Criado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

# Configurações
BACKUP_DIR="{backup_dir}"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/backup_master_$DATE.log"

# Função para log
log() {{
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$LOG_FILE"
}}

log "Iniciando processo de backup completo"

# Executar backup do PostgreSQL
log "Executando backup do PostgreSQL"
/usr/local/bin/backup_postgres.sh
if [ $? -eq 0 ]; then
    log "Backup do PostgreSQL concluído com sucesso"
else
    log "Erro no backup do PostgreSQL"
fi

# Executar backup de volumes Docker
log "Executando backup de volumes Docker"
/usr/local/bin/backup_volumes.sh
if [ $? -eq 0 ]; then
    log "Backup de volumes Docker concluído com sucesso"
else
    log "Erro no backup de volumes Docker"
fi

# Executar backup do Supabase
log "Executando backup do Supabase"
/usr/local/bin/backup_supabase.sh
if [ $? -eq 0 ]; then
    log "Backup do Supabase concluído com sucesso"
else
    log "Erro no backup do Supabase"
fi

log "Processo de backup completo finalizado"

# Enviar notificação (opcional)
# mail -s "Backup Renum-Suna concluído" admin@example.com < "$LOG_FILE"
"""
    
    print(f"Creating master backup script: {script_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create script: {script_path}")
        print("Script content:")
        print(script_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_all.sh"
        with open(temp_path, "w") as f:
            f.write(script_content)
        
        # Upload to server
        upload_file(client, temp_path, script_path, dry_run)
        os.remove(temp_path)
        
        # Make executable
        execute_command(client, f"chmod +x {script_path}", dry_run)
    
    return script_path

def create_recovery_script(client, backup_dir, dry_run=False):
    """Create recovery script."""
    script_path = "/usr/local/bin/recover.sh"
    script_content = f"""#!/bin/bash
# Script para recuperação de backups
# Criado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

# Configurações
BACKUP_DIR="{backup_dir}"

# Função para exibir ajuda
show_help() {{
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --list-backups         Listar backups disponíveis"
    echo "  --recover-postgres     Recuperar backup do PostgreSQL"
    echo "  --recover-volume       Recuperar backup de volume Docker"
    echo "  --recover-all          Recuperar todos os backups"
    echo "  --help                 Exibir esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 --list-backups"
    echo "  $0 --recover-postgres postgres_20250717_120000.sql.gz"
    echo "  $0 --recover-volume my_volume_20250717_120000.tar.gz"
}}

# Função para listar backups
list_backups() {{
    echo "=== Backups do PostgreSQL ==="
    find "$BACKUP_DIR/postgres" -name "*.sql.gz" -type f | sort
    
    echo ""
    echo "=== Backups de Volumes Docker ==="
    find "$BACKUP_DIR/volumes" -name "*.tar.gz" -type f | sort
    
    echo ""
    echo "=== Backups do Supabase ==="
    find "$BACKUP_DIR/supabase" -type f | sort
}}

# Função para recuperar backup do PostgreSQL
recover_postgres() {{
    if [ -z "$1" ]; then
        echo "Erro: Especifique o arquivo de backup do PostgreSQL"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Erro: Arquivo de backup não encontrado: $BACKUP_FILE"
        exit 1
    fi
    
    echo "Recuperando backup do PostgreSQL: $BACKUP_FILE"
    
    # Extrair nome do banco e contêiner do nome do arquivo
    FILENAME=$(basename "$BACKUP_FILE")
    DB_NAME=$(echo "$FILENAME" | cut -d_ -f1)
    CONTAINER=$(dirname "$BACKUP_FILE" | xargs basename)
    
    echo "Banco de dados: $DB_NAME"
    echo "Contêiner: $CONTAINER"
    
    # Descomprimir arquivo
    echo "Descomprimindo arquivo..."
    gunzip -c "$BACKUP_FILE" > /tmp/recovery.sql
    
    # Recuperar no contêiner
    echo "Recuperando no contêiner..."
    docker cp /tmp/recovery.sql $CONTAINER:/tmp/recovery.sql
    docker exec $CONTAINER psql -U postgres -d $DB_NAME -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
    docker exec $CONTAINER psql -U postgres -d $DB_NAME -f /tmp/recovery.sql
    docker exec $CONTAINER rm /tmp/recovery.sql
    rm /tmp/recovery.sql
    
    echo "Recuperação concluída com sucesso"
}}

# Função para recuperar backup de volume Docker
recover_volume() {{
    if [ -z "$1" ]; then
        echo "Erro: Especifique o arquivo de backup do volume"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Erro: Arquivo de backup não encontrado: $BACKUP_FILE"
        exit 1
    fi
    
    echo "Recuperando backup de volume: $BACKUP_FILE"
    
    # Extrair nome do volume do nome do arquivo
    FILENAME=$(basename "$BACKUP_FILE")
    VOLUME=$(echo "$FILENAME" | cut -d_ -f1)
    
    echo "Volume: $VOLUME"
    
    # Verificar se o volume existe
    if ! docker volume inspect $VOLUME > /dev/null 2>&1; then
        echo "Erro: Volume não encontrado: $VOLUME"
        exit 1
    fi
    
    # Parar contêineres que usam o volume
    CONTAINERS=$(docker ps -a --filter volume=$VOLUME --format '{{{{.Names}}}}')
    
    if [ -n "$CONTAINERS" ]; then
        echo "Parando contêineres que usam o volume:"
        for CONTAINER in $CONTAINERS; do
            echo "  - $CONTAINER"
            docker stop $CONTAINER
        done
    fi
    
    # Criar diretório temporário
    TEMP_DIR="/tmp/volume_recovery_$(date +%s)"
    mkdir -p "$TEMP_DIR"
    
    # Extrair backup
    echo "Extraindo backup..."
    tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
    
    # Limpar volume
    echo "Limpando volume..."
    docker run --rm -v $VOLUME:/volume alpine sh -c "rm -rf /volume/*"
    
    # Restaurar dados
    echo "Restaurando dados..."
    docker run --rm -v $VOLUME:/volume -v $TEMP_DIR:/backup alpine sh -c "cp -a /backup/. /volume/"
    
    # Remover diretório temporário
    rm -rf "$TEMP_DIR"
    
    # Iniciar contêineres
    if [ -n "$CONTAINERS" ]; then
        echo "Iniciando contêineres:"
        for CONTAINER in $CONTAINERS; do
            echo "  - $CONTAINER"
            docker start $CONTAINER
        done
    fi
    
    echo "Recuperação concluída com sucesso"
}}

# Verificar argumentos
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    --list-backups)
        list_backups
        ;;
    --recover-postgres)
        recover_postgres "$2"
        ;;
    --recover-volume)
        recover_volume "$2"
        ;;
    --recover-all)
        echo "Recuperação completa não implementada"
        echo "Use as opções individuais para recuperar componentes específicos"
        ;;
    --help)
        show_help
        ;;
    *)
        echo "Opção desconhecida: $1"
        show_help
        exit 1
        ;;
esac
"""
    
    print(f"Creating recovery script: {script_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create script: {script_path}")
        print("Script content:")
        print(script_content)
    else:
        # Create temporary file
        temp_path = "/tmp/recover.sh"
        with open(temp_path, "w") as f:
            f.write(script_content)
        
        # Upload to server
        upload_file(client, temp_path, script_path, dry_run)
        os.remove(temp_path)
        
        # Make executable
        execute_command(client, f"chmod +x {script_path}", dry_run)
    
    return script_path

def setup_cron_jobs(client, dry_run=False):
    """Setup cron jobs for backup scripts."""
    print("Setting up cron jobs")
    
    # Create crontab entries
    crontab_content = """# Backup cron jobs
# Added on {date}

# PostgreSQL backup - daily at 2:00 AM
0 2 * * * /usr/local/bin/backup_postgres.sh

# Docker volumes backup - weekly on Sunday at 3:00 AM
0 3 * * 0 /usr/local/bin/backup_volumes.sh

# Supabase backup - daily at 4:00 AM
0 4 * * * /usr/local/bin/backup_supabase.sh

# Master backup - daily at 1:00 AM
0 1 * * * /usr/local/bin/backup_all.sh
""".format(date=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
    if dry_run:
        print(f"[DRY RUN] Would add to crontab:")
        print(crontab_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_crontab"
        with open(temp_path, "w") as f:
            f.write(crontab_content)
        
        # Upload to server
        upload_file(client, temp_path, "/tmp/backup_crontab", dry_run)
        os.remove(temp_path)
        
        # Get existing crontab
        existing_crontab = execute_command(client, "crontab -l 2>/dev/null || echo ''", dry_run)
        
        # Check if backup jobs already exist
        if "backup_postgres.sh" in existing_crontab:
            print("Backup cron jobs already exist. Skipping.")
        else:
            # Append new crontab entries
            execute_command(client, "cat /tmp/backup_crontab >> /tmp/full_crontab", dry_run)
            execute_command(client, "echo \"$(" + ("cat /dev/null" if dry_run else "crontab -l 2>/dev/null || echo ''") + ")\" >> /tmp/full_crontab", dry_run)
            execute_command(client, "crontab /tmp/full_crontab", dry_run)
            execute_command(client, "rm /tmp/backup_crontab /tmp/full_crontab", dry_run)
    
    return True

def create_documentation(client, backup_dir, dry_run=False):
    """Create backup and recovery documentation."""
    doc_path = f"{backup_dir}/README.md"
    doc_content = f"""# Backup e Recuperação - Renum e Suna

Este documento descreve a configuração de backup e recuperação para os serviços Renum e Suna.

## Visão Geral

Os seguintes componentes são incluídos no backup:

1. **Bancos de dados PostgreSQL**
   - Backup diário às 2:00 AM
   - Retenção de 7 dias

2. **Volumes Docker**
   - Backup semanal aos domingos às 3:00 AM
   - Retenção de 7 dias

3. **Configuração do Supabase**
   - Backup diário às 4:00 AM
   - Retenção de 7 dias

## Localização dos Backups

Todos os backups são armazenados em `{backup_dir}` com a seguinte estrutura:

- `{backup_dir}/postgres/` - Backups de bancos de dados PostgreSQL
- `{backup_dir}/volumes/` - Backups de volumes Docker
- `{backup_dir}/supabase/` - Backups de configuração do Supabase

## Scripts de Backup

Os seguintes scripts estão disponíveis:

- `/usr/local/bin/backup_postgres.sh` - Backup de bancos de dados PostgreSQL
- `/usr/local/bin/backup_volumes.sh` - Backup de volumes Docker
- `/usr/local/bin/backup_supabase.sh` - Backup de configuração do Supabase
- `/usr/local/bin/backup_all.sh` - Script mestre que executa todos os backups
- `/usr/local/bin/recover.sh` - Script para recuperação de backups

## Procedimentos de Recuperação

### Listar Backups Disponíveis

```bash
/usr/local/bin/recover.sh --list-backups
```

### Recuperar Banco de Dados PostgreSQL

```bash
/usr/local/bin/recover.sh --recover-postgres /caminho/para/backup.sql.gz
```

### Recuperar Volume Docker

```bash
/usr/local/bin/recover.sh --recover-volume /caminho/para/backup.tar.gz
```

## Recomendações

1. **Backup Externo**
   - Considere copiar os backups para um local externo ao servidor
   - Use ferramentas como rsync, rclone ou AWS S3 para armazenamento externo

2. **Monitoramento**
   - Verifique regularmente os logs de backup em `{backup_dir}/*/backup_*.log`
   - Configure alertas para falhas de backup

3. **Testes de Recuperação**
   - Teste regularmente a recuperação de backups em um ambiente de teste
   - Documente o processo de recuperação completa

## Melhorias Futuras

1. Implementar backup incremental para reduzir o tamanho dos backups
2. Configurar backup automático para o Supabase usando a API oficial
3. Implementar verificação automática da integridade dos backups
4. Configurar notificações por e-mail para falhas de backup
"""
    
    print(f"Creating backup documentation: {doc_path}")
    
    if dry_run:
        print(f"[DRY RUN] Would create documentation: {doc_path}")
        print("Documentation content:")
        print(doc_content)
    else:
        # Create temporary file
        temp_path = "/tmp/backup_readme.md"
        with open(temp_path, "w") as f:
            f.write(doc_content)
        
        # Upload to server
        upload_file(client, temp_path, doc_path, dry_run)
        os.remove(temp_path)
    
    return doc_path

def main():
    """Main function."""
    args = parse_arguments()
    
    print("=== Configuração de Solução Básica de Backup ===")
    
    if args.dry_run:
        print("MODO DE SIMULAÇÃO: Nenhuma alteração será feita no servidor")
    
    # Connect to SSH
    print(f"Conectando a {args.user}@{args.host}:{args.port}...")
    
    if not args.dry_run:
        client = create_ssh_client(args.host, args.port, args.user, args.key_file)
        
        if not client:
            print("❌ Falha ao estabelecer conexão SSH")
            sys.exit(1)
        
        print("✅ Conexão SSH estabelecida")
    else:
        client = None
        print("[DRY RUN] Simulando conexão SSH")
    
    # Create backup directory
    backup_dir = create_backup_directory(client, args.backup_dir, args.dry_run)
    
    # Create backup scripts
    create_postgres_backup_script(client, backup_dir, args.retention_days, args.dry_run)
    create_docker_volumes_backup_script(client, backup_dir, args.retention_days, args.dry_run)
    create_supabase_backup_script(client, backup_dir, args.retention_days, args.dry_run)
    create_master_backup_script(client, backup_dir, args.dry_run)
    create_recovery_script(client, backup_dir, args.dry_run)
    
    # Setup cron jobs
    setup_cron_jobs(client, args.dry_run)
    
    # Create documentation
    create_documentation(client, backup_dir, args.dry_run)
    
    if not args.dry_run and client:
        client.close()
        print("Conexão SSH encerrada")
    
    print("\n=== Configuração de Backup Concluída ===")
    print(f"Diretório de backup: {backup_dir}")
    print("Scripts de backup criados:")
    print("  - /usr/local/bin/backup_postgres.sh")
    print("  - /usr/local/bin/backup_volumes.sh")
    print("  - /usr/local/bin/backup_supabase.sh")
    print("  - /usr/local/bin/backup_all.sh")
    print("  - /usr/local/bin/recover.sh")
    print("Documentação criada:")
    print(f"  - {backup_dir}/README.md")
    
    if args.dry_run:
        print("\nEste foi um teste de simulação. Para aplicar as alterações, execute sem a opção --dry-run")

if __name__ == "__main__":
    main()