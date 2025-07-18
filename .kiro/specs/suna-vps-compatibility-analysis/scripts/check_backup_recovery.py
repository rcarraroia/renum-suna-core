#!/usr/bin/env python3
"""
Script para verificar a configuração de backup e recuperação dos serviços Renum e Suna.
Este script analisa a estratégia de backup existente, verifica procedimentos de recuperação e identifica melhorias necessárias.
"""

import os
import sys
import json
import argparse
import paramiko
import getpass
import re
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Check backup and recovery configuration')
    parser.add_argument('--host', default='157.180.39.41', help='VPS hostname or IP address')
    parser.add_argument('--port', type=int, default=22, help='SSH port')
    parser.add_argument('--user', default='root', help='SSH username')
    parser.add_argument('--key-file', help='Path to SSH private key file')
    parser.add_argument('--output-dir', default='./output', help='Directory to save output files')
    parser.add_argument('--containers-file', help='Path to containers JSON file (optional)')
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

def execute_command(client, command):
    """Execute a command on the remote server."""
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

def get_docker_containers(client):
    """Get list of Docker containers."""
    output = execute_command(client, "docker ps -a --format '{{.ID}},{{.Names}},{{.Status}},{{.Image}},{{.Ports}}'")
    containers = []
    
    if output:
        for line in output.strip().split('\n'):
            if line:
                parts = line.split(',', 4)
                if len(parts) >= 5:
                    container_id, name, status, image, ports = parts
                    containers.append({
                        'id': container_id,
                        'name': name,
                        'status': status,
                        'image': image,
                        'ports': ports,
                        'is_running': 'Up' in status
                    })
    
    # Categorize containers
    for container in containers:
        if 'renum' in container['name'].lower() or 'renum' in container['image'].lower():
            container['category'] = 'renum'
        elif 'suna' in container['name'].lower() or 'suna' in container['image'].lower():
            container['category'] = 'suna'
        elif 'postgres' in container['name'].lower() or 'postgres' in container['image'].lower():
            container['category'] = 'database'
        elif 'redis' in container['name'].lower() or 'redis' in container['image'].lower():
            container['category'] = 'cache'
        elif 'rabbitmq' in container['name'].lower() or 'rabbitmq' in container['image'].lower():
            container['category'] = 'message_queue'
        else:
            container['category'] = 'other'
    
    return containers

def get_container_volumes(client, container_id):
    """Get volumes for a Docker container."""
    output = execute_command(client, f"docker inspect -f '{{{{json .Mounts}}}}' {container_id}")
    
    if output:
        try:
            # Clean the output (remove extra quotes)
            output = output.strip().strip("'")
            return json.loads(output)
        except json.JSONDecodeError as e:
            print(f"Error parsing volumes: {str(e)}")
            return []
    
    return []

def check_cron_jobs(client):
    """Check for backup-related cron jobs."""
    # Check root's crontab
    root_crontab = execute_command(client, "crontab -l 2>/dev/null || echo 'No crontab for root'")
    
    # Check system crontabs
    system_crontabs = execute_command(client, "find /etc/cron.d -type f -exec cat {} \\; 2>/dev/null || echo 'No system crontabs'")
    
    # Check for backup scripts in common cron directories
    cron_dirs = execute_command(client, "ls -la /etc/cron.daily /etc/cron.weekly /etc/cron.monthly 2>/dev/null || echo 'No cron directories'")
    
    return {
        'root_crontab': root_crontab,
        'system_crontabs': system_crontabs,
        'cron_dirs': cron_dirs
    }

def find_backup_scripts(client):
    """Find backup scripts on the system."""
    # Look for backup scripts in common locations
    backup_scripts = execute_command(client, "find /root /home /opt /usr/local/bin -name '*backup*' -type f 2>/dev/null | grep -v 'Permission denied' || echo 'No backup scripts found'")
    
    # Look for backup directories
    backup_dirs = execute_command(client, "find /root /home /opt /var/backups -name '*backup*' -type d 2>/dev/null | grep -v 'Permission denied' || echo 'No backup directories found'")
    
    return {
        'backup_scripts': backup_scripts,
        'backup_dirs': backup_dirs
    }

def check_docker_compose_backup_services(client):
    """Check for backup services in Docker Compose files."""
    # Find Docker Compose files
    compose_files = execute_command(client, "find / -name 'docker-compose*.y*ml' -type f 2>/dev/null | grep -v 'Permission denied' || echo 'No Docker Compose files found'")
    
    backup_services = {}
    
    if compose_files and 'No Docker Compose files found' not in compose_files:
        for compose_file in compose_files.strip().split('\n'):
            # Check if file contains backup-related services
            file_content = execute_command(client, f"cat {compose_file} 2>/dev/null || echo 'Cannot read file'")
            
            if 'backup' in file_content.lower():
                backup_services[compose_file] = file_content
    
    return backup_services

def check_database_backup_config(client, containers):
    """Check for database backup configuration."""
    db_backup_config = {}
    
    # Find database containers
    db_containers = [c for c in containers if c['category'] == 'database' and c['is_running']]
    
    for container in db_containers:
        container_id = container['id']
        container_name = container['name']
        
        # Check for pg_dump in PostgreSQL containers
        if 'postgres' in container['image'].lower():
            # Check for pg_dump cron jobs inside container
            pg_cron = execute_command(client, f"docker exec {container_id} crontab -l 2>/dev/null || echo 'No crontab in container'")
            
            # Check for PostgreSQL backup scripts
            pg_scripts = execute_command(client, f"docker exec {container_id} find / -name '*backup*' -o -name '*pg_dump*' -type f 2>/dev/null | grep -v 'Permission denied' || echo 'No backup scripts in container'")
            
            db_backup_config[container_name] = {
                'type': 'postgres',
                'cron_jobs': pg_cron,
                'backup_scripts': pg_scripts
            }
    
    return db_backup_config

def check_supabase_backup_config(client, containers):
    """Check for Supabase backup configuration."""
    # Look for Supabase environment variables in containers
    supabase_containers = []
    
    for container in containers:
        if container['is_running']:
            container_id = container['id']
            env_vars = execute_command(client, f"docker exec {container_id} env | grep -i supabase || echo 'No Supabase env vars'")
            
            if 'No Supabase env vars' not in env_vars:
                supabase_containers.append(container['name'])
    
    # Check for Supabase backup scripts
    supabase_scripts = execute_command(client, "find / -name '*supabase*backup*' -type f 2>/dev/null | grep -v 'Permission denied' || echo 'No Supabase backup scripts found'")
    
    return {
        'supabase_containers': supabase_containers,
        'supabase_scripts': supabase_scripts
    }

def check_volume_backup_config(client, containers):
    """Check for Docker volume backup configuration."""
    volume_backup = {}
    
    # Get all Docker volumes
    volumes_output = execute_command(client, "docker volume ls --format '{{.Name}}'")
    volumes = volumes_output.strip().split('\n') if volumes_output else []
    
    # Check for volume backup scripts
    volume_scripts = execute_command(client, "find / -name '*volume*backup*' -o -name '*docker*backup*' -type f 2>/dev/null | grep -v 'Permission denied' || echo 'No volume backup scripts found'")
    
    # Get container volumes
    container_volumes = {}
    for container in containers:
        if container['is_running']:
            container_id = container['id']
            container_name = container['name']
            
            volumes = get_container_volumes(client, container_id)
            if volumes:
                container_volumes[container_name] = volumes
    
    return {
        'volumes': volumes,
        'volume_scripts': volume_scripts,
        'container_volumes': container_volumes
    }

def analyze_backup_configuration(cron_jobs, backup_scripts, compose_backup_services, db_backup_config, supabase_backup_config, volume_backup_config):
    """Analyze backup configuration."""
    analysis = {
        'has_cron_backup_jobs': False,
        'has_backup_scripts': False,
        'has_compose_backup_services': len(compose_backup_services) > 0,
        'has_db_backup_config': any(config.get('cron_jobs') != 'No crontab in container' or config.get('backup_scripts') != 'No backup scripts in container' for config in db_backup_config.values()),
        'has_supabase_backup': supabase_backup_config.get('supabase_scripts') != 'No Supabase backup scripts found',
        'has_volume_backup': volume_backup_config.get('volume_scripts') != 'No volume backup scripts found',
        'backup_methods': [],
        'issues': [],
        'status': 'OK'
    }
    
    # Check for cron backup jobs
    if 'backup' in cron_jobs.get('root_crontab', '').lower() or 'backup' in cron_jobs.get('system_crontabs', '').lower():
        analysis['has_cron_backup_jobs'] = True
        analysis['backup_methods'].append('Cron Jobs')
    
    # Check for backup scripts
    if backup_scripts.get('backup_scripts') and 'No backup scripts found' not in backup_scripts.get('backup_scripts', ''):
        analysis['has_backup_scripts'] = True
        analysis['backup_methods'].append('Backup Scripts')
    
    # Add other backup methods
    if analysis['has_compose_backup_services']:
        analysis['backup_methods'].append('Docker Compose Backup Services')
    
    if analysis['has_db_backup_config']:
        analysis['backup_methods'].append('Database Backup')
    
    if analysis['has_supabase_backup']:
        analysis['backup_methods'].append('Supabase Backup')
    
    if analysis['has_volume_backup']:
        analysis['backup_methods'].append('Volume Backup')
    
    # Check for issues
    if not analysis['backup_methods']:
        analysis['issues'].append("Nenhum método de backup encontrado")
        analysis['status'] = 'ERROR'
    else:
        # Check for specific backup types
        if not analysis['has_db_backup_config'] and db_backup_config:
            analysis['issues'].append("Bancos de dados sem configuração de backup")
            analysis['status'] = 'WARNING'
        
        if not analysis['has_supabase_backup'] and supabase_backup_config.get('supabase_containers'):
            analysis['issues'].append("Supabase sem configuração de backup")
            analysis['status'] = 'WARNING'
        
        if not analysis['has_volume_backup'] and volume_backup_config.get('container_volumes'):
            analysis['issues'].append("Volumes Docker sem configuração de backup")
            analysis['status'] = 'WARNING'
    
    return analysis

def save_to_file(data, filename):
    """Save data to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if isinstance(data, (dict, list)):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    else:
        with open(filename, 'w') as f:
            f.write(data if isinstance(data, str) else '\n'.join(data))

def main():
    """Main function."""
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load containers from file if provided
    containers = None
    if args.containers_file and os.path.exists(args.containers_file):
        try:
            with open(args.containers_file, 'r') as f:
                containers = json.load(f)
            print(f"Carregados {len(containers)} contêineres do arquivo {args.containers_file}")
        except Exception as e:
            print(f"Erro ao carregar contêineres do arquivo: {str(e)}")
            containers = None
    
    # Connect to SSH
    print(f"Conectando a {args.user}@{args.host}:{args.port}...")
    client = create_ssh_client(args.host, args.port, args.user, args.key_file)
    
    if not client:
        print("❌ Falha ao estabelecer conexão SSH")
        sys.exit(1)
    
    print("✅ Conexão SSH estabelecida")
    
    # Get containers if not loaded from file
    if not containers:
        containers = get_docker_containers(client)
        save_to_file(containers, os.path.join(args.output_dir, 'containers.json'))
    
    # Check cron jobs
    print("Verificando jobs de cron relacionados a backup...")
    cron_jobs = check_cron_jobs(client)
    save_to_file(cron_jobs, os.path.join(args.output_dir, 'backup_cron_jobs.json'))
    
    # Find backup scripts
    print("Procurando scripts de backup...")
    backup_scripts = find_backup_scripts(client)
    save_to_file(backup_scripts, os.path.join(args.output_dir, 'backup_scripts.json'))
    
    # Check Docker Compose backup services
    print("Verificando serviços de backup no Docker Compose...")
    compose_backup_services = check_docker_compose_backup_services(client)
    save_to_file(compose_backup_services, os.path.join(args.output_dir, 'compose_backup_services.json'))
    
    # Check database backup configuration
    print("Verificando configuração de backup de banco de dados...")
    db_backup_config = check_database_backup_config(client, containers)
    save_to_file(db_backup_config, os.path.join(args.output_dir, 'db_backup_config.json'))
    
    # Check Supabase backup configuration
    print("Verificando configuração de backup do Supabase...")
    supabase_backup_config = check_supabase_backup_config(client, containers)
    save_to_file(supabase_backup_config, os.path.join(args.output_dir, 'supabase_backup_config.json'))
    
    # Check volume backup configuration
    print("Verificando configuração de backup de volumes...")
    volume_backup_config = check_volume_backup_config(client, containers)
    save_to_file(volume_backup_config, os.path.join(args.output_dir, 'volume_backup_config.json'))
    
    # Analyze backup configuration
    backup_analysis = analyze_backup_configuration(
        cron_jobs, 
        backup_scripts, 
        compose_backup_services, 
        db_backup_config, 
        supabase_backup_config, 
        volume_backup_config
    )
    save_to_file(backup_analysis, os.path.join(args.output_dir, 'backup_analysis.json'))
    
    # Generate summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'backup_methods_found': backup_analysis['backup_methods'],
        'has_database_backup': backup_analysis['has_db_backup_config'],
        'has_supabase_backup': backup_analysis['has_supabase_backup'],
        'has_volume_backup': backup_analysis['has_volume_backup'],
        'status': backup_analysis['status'],
        'issues': backup_analysis['issues']
    }
    
    save_to_file(summary, os.path.join(args.output_dir, 'backup_summary.json'))
    
    # Generate text report
    report = f"""
=======================================================
RELATÓRIO DE BACKUP E RECUPERAÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

MÉTODOS DE BACKUP ENCONTRADOS:
{', '.join(backup_analysis['backup_methods']) if backup_analysis['backup_methods'] else 'Nenhum método de backup encontrado'}

Backup de banco de dados: {'✅ Configurado' if backup_analysis['has_db_backup_config'] else '❌ Não configurado'}
Backup do Supabase: {'✅ Configurado' if backup_analysis['has_supabase_backup'] else '❌ Não configurado'}
Backup de volumes Docker: {'✅ Configurado' if backup_analysis['has_volume_backup'] else '❌ Não configurado'}

Status: {backup_analysis['status']}

"""
    
    # Add details about cron jobs
    if 'Cron Jobs' in backup_analysis['backup_methods']:
        report += "\nDETALHES DE JOBS DE CRON RELACIONADOS A BACKUP:\n"
        
        if 'backup' in cron_jobs.get('root_crontab', '').lower():
            report += "\nCrontab do root:\n"
            for line in cron_jobs['root_crontab'].split('\n'):
                if 'backup' in line.lower():
                    report += f"{line}\n"
        
        if 'backup' in cron_jobs.get('system_crontabs', '').lower():
            report += "\nCrontabs do sistema:\n"
            for line in cron_jobs['system_crontabs'].split('\n'):
                if 'backup' in line.lower():
                    report += f"{line}\n"
    
    # Add details about backup scripts
    if 'Backup Scripts' in backup_analysis['backup_methods']:
        report += "\nSCRIPTS DE BACKUP ENCONTRADOS:\n"
        for script in backup_scripts['backup_scripts'].split('\n'):
            if script and 'No backup scripts found' not in script:
                report += f"- {script}\n"
    
    # Add details about Docker Compose backup services
    if 'Docker Compose Backup Services' in backup_analysis['backup_methods']:
        report += "\nSERVIÇOS DE BACKUP NO DOCKER COMPOSE:\n"
        for file_path in compose_backup_services.keys():
            report += f"- {file_path}\n"
    
    # Add details about database backup
    if 'Database Backup' in backup_analysis['backup_methods']:
        report += "\nCONFIGURAÇÃO DE BACKUP DE BANCO DE DADOS:\n"
        for container_name, config in db_backup_config.items():
            report += f"\n{container_name} ({config['type']}):\n"
            
            if config['cron_jobs'] and 'No crontab in container' not in config['cron_jobs']:
                report += "  Jobs de cron:\n"
                for line in config['cron_jobs'].split('\n'):
                    if line.strip():
                        report += f"  - {line}\n"
            
            if config['backup_scripts'] and 'No backup scripts in container' not in config['backup_scripts']:
                report += "  Scripts de backup:\n"
                for line in config['backup_scripts'].split('\n'):
                    if line.strip():
                        report += f"  - {line}\n"
    
    # Add details about Supabase backup
    if 'Supabase Backup' in backup_analysis['backup_methods']:
        report += "\nCONFIGURAÇÃO DE BACKUP DO SUPABASE:\n"
        
        if supabase_backup_config['supabase_containers']:
            report += "  Contêineres com variáveis de ambiente do Supabase:\n"
            for container in supabase_backup_config['supabase_containers']:
                report += f"  - {container}\n"
        
        if supabase_backup_config['supabase_scripts'] and 'No Supabase backup scripts found' not in supabase_backup_config['supabase_scripts']:
            report += "  Scripts de backup do Supabase:\n"
            for line in supabase_backup_config['supabase_scripts'].split('\n'):
                if line.strip():
                    report += f"  - {line}\n"
    
    # Add details about volume backup
    if 'Volume Backup' in backup_analysis['backup_methods']:
        report += "\nCONFIGURAÇÃO DE BACKUP DE VOLUMES:\n"
        
        if volume_backup_config['volume_scripts'] and 'No volume backup scripts found' not in volume_backup_config['volume_scripts']:
            report += "  Scripts de backup de volumes:\n"
            for line in volume_backup_config['volume_scripts'].split('\n'):
                if line.strip():
                    report += f"  - {line}\n"
        
        if volume_backup_config['container_volumes']:
            report += "  Volumes usados por contêineres:\n"
            for container_name, volumes in volume_backup_config['container_volumes'].items():
                report += f"  - {container_name}: {len(volumes)} volumes\n"
    
    # Add issues
    if backup_analysis['issues']:
        report += "\nPROBLEMAS DETECTADOS:\n"
        for issue in backup_analysis['issues']:
            report += f"- {issue}\n"
    
    # Add recommendations
    report += "\nRECOMENDAÇÕES:\n"
    
    if not backup_analysis['backup_methods']:
        report += "- Implementar uma estratégia de backup abrangente para todos os dados críticos\n"
        report += "- Configurar jobs de cron para executar backups regularmente\n"
        report += "- Armazenar backups em local seguro, preferencialmente fora do servidor\n"
    else:
        if not backup_analysis['has_db_backup_config'] and db_backup_config:
            report += "- Configurar backup automático para bancos de dados\n"
        
        if not backup_analysis['has_supabase_backup'] and supabase_backup_config.get('supabase_containers'):
            report += "- Implementar backup regular do Supabase\n"
        
        if not backup_analysis['has_volume_backup'] and volume_backup_config.get('container_volumes'):
            report += "- Configurar backup de volumes Docker para preservar dados persistentes\n"
        
        report += "- Documentar procedimentos de recuperação para cada tipo de backup\n"
        report += "- Testar regularmente a restauração de backups para garantir sua eficácia\n"
        report += "- Considerar o uso de ferramentas de backup automatizadas como restic, duplicity ou borgbackup\n"
    
    save_to_file(report, os.path.join(args.output_dir, 'backup_recovery_report.txt'))
    print(report)
    
    client.close()
    print("Conexão SSH encerrada")
    print(f"Verificação de backup e recuperação concluída. Resultados salvos em {args.output_dir}")

if __name__ == "__main__":
    main()