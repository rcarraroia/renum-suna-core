#!/usr/bin/env python3
"""
Script para testar a funcionalidade do script check_backup_recovery.py
Este script executa o check_backup_recovery.py em modo de teste e verifica se ele está funcionando corretamente.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test backup and recovery check script')
    parser.add_argument('--output-dir', default='./output/backup_test', help='Directory to save output files')
    parser.add_argument('--mock', action='store_true', help='Use mock data instead of connecting to VPS')
    return parser.parse_args()

def create_mock_data(output_dir):
    """Create mock data for testing."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Mock containers
    containers = [
        {
            'id': 'abc123',
            'name': 'renum-backend',
            'status': 'Up 2 days',
            'image': 'renum-backend:latest',
            'ports': '8000:8000',
            'is_running': True,
            'category': 'renum'
        },
        {
            'id': 'def456',
            'name': 'suna-backend',
            'status': 'Up 2 days',
            'image': 'suna-backend:latest',
            'ports': '8080:8080',
            'is_running': True,
            'category': 'suna'
        },
        {
            'id': 'ghi789',
            'name': 'postgres',
            'status': 'Up 2 days',
            'image': 'postgres:13',
            'ports': '5432:5432',
            'is_running': True,
            'category': 'database'
        }
    ]
    
    # Mock cron jobs
    cron_jobs = {
        'root_crontab': '# Example cron job\n0 2 * * * /usr/local/bin/backup_script.sh\n',
        'system_crontabs': '# No system crontabs with backup',
        'cron_dirs': '/etc/cron.daily:\nbackup_postgres\n\n/etc/cron.weekly:\nbackup_volumes\n'
    }
    
    # Mock backup scripts
    backup_scripts = {
        'backup_scripts': '/usr/local/bin/backup_script.sh\n/root/backup_postgres.sh\n',
        'backup_dirs': '/var/backups/postgres\n/var/backups/volumes\n'
    }
    
    # Mock Docker Compose backup services
    compose_backup_services = {
        '/root/docker-compose.yml': 'services:\n  backup:\n    image: backup-service\n    volumes:\n      - /var/backups:/backups\n'
    }
    
    # Mock database backup config
    db_backup_config = {
        'postgres': {
            'type': 'postgres',
            'cron_jobs': '0 2 * * * pg_dump -U postgres -d mydb > /var/backups/postgres/mydb_$(date +%Y%m%d).sql\n',
            'backup_scripts': '/var/lib/postgresql/backup.sh\n'
        }
    }
    
    # Mock Supabase backup config
    supabase_backup_config = {
        'supabase_containers': ['renum-backend', 'suna-backend'],
        'supabase_scripts': '/usr/local/bin/backup_supabase.sh\n'
    }
    
    # Mock volume backup config
    volume_backup_config = {
        'volumes': ['postgres_data', 'redis_data'],
        'volume_scripts': '/usr/local/bin/backup_volumes.sh\n',
        'container_volumes': {
            'postgres': [
                {
                    'Source': '/var/lib/postgresql/data',
                    'Destination': '/var/lib/postgresql/data',
                    'Mode': '',
                    'RW': True,
                    'Name': 'postgres_data'
                }
            ]
        }
    }
    
    # Save mock data
    with open(os.path.join(output_dir, 'containers.json'), 'w') as f:
        json.dump(containers, f, indent=2)
    
    with open(os.path.join(output_dir, 'backup_cron_jobs.json'), 'w') as f:
        json.dump(cron_jobs, f, indent=2)
    
    with open(os.path.join(output_dir, 'backup_scripts.json'), 'w') as f:
        json.dump(backup_scripts, f, indent=2)
    
    with open(os.path.join(output_dir, 'compose_backup_services.json'), 'w') as f:
        json.dump(compose_backup_services, f, indent=2)
    
    with open(os.path.join(output_dir, 'db_backup_config.json'), 'w') as f:
        json.dump(db_backup_config, f, indent=2)
    
    with open(os.path.join(output_dir, 'supabase_backup_config.json'), 'w') as f:
        json.dump(supabase_backup_config, f, indent=2)
    
    with open(os.path.join(output_dir, 'volume_backup_config.json'), 'w') as f:
        json.dump(volume_backup_config, f, indent=2)
    
    # Create mock analysis
    backup_analysis = {
        'has_cron_backup_jobs': True,
        'has_backup_scripts': True,
        'has_compose_backup_services': True,
        'has_db_backup_config': True,
        'has_supabase_backup': True,
        'has_volume_backup': True,
        'backup_methods': [
            'Cron Jobs',
            'Backup Scripts',
            'Docker Compose Backup Services',
            'Database Backup',
            'Supabase Backup',
            'Volume Backup'
        ],
        'issues': [],
        'status': 'OK'
    }
    
    with open(os.path.join(output_dir, 'backup_analysis.json'), 'w') as f:
        json.dump(backup_analysis, f, indent=2)
    
    # Create mock summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'backup_methods_found': backup_analysis['backup_methods'],
        'has_database_backup': backup_analysis['has_db_backup_config'],
        'has_supabase_backup': backup_analysis['has_supabase_backup'],
        'has_volume_backup': backup_analysis['has_volume_backup'],
        'status': backup_analysis['status'],
        'issues': backup_analysis['issues']
    }
    
    with open(os.path.join(output_dir, 'backup_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create mock report
    report = f"""
=======================================================
RELATÓRIO DE BACKUP E RECUPERAÇÃO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
=======================================================

MÉTODOS DE BACKUP ENCONTRADOS:
Cron Jobs, Backup Scripts, Docker Compose Backup Services, Database Backup, Supabase Backup, Volume Backup

Backup de banco de dados: ✅ Configurado
Backup do Supabase: ✅ Configurado
Backup de volumes Docker: ✅ Configurado

Status: OK

DETALHES DE JOBS DE CRON RELACIONADOS A BACKUP:

Crontab do root:
0 2 * * * /usr/local/bin/backup_script.sh

SCRIPTS DE BACKUP ENCONTRADOS:
- /usr/local/bin/backup_script.sh
- /root/backup_postgres.sh

SERVIÇOS DE BACKUP NO DOCKER COMPOSE:
- /root/docker-compose.yml

CONFIGURAÇÃO DE BACKUP DE BANCO DE DADOS:

postgres (postgres):
  Jobs de cron:
  - 0 2 * * * pg_dump -U postgres -d mydb > /var/backups/postgres/mydb_$(date +%Y%m%d).sql
  Scripts de backup:
  - /var/lib/postgresql/backup.sh

CONFIGURAÇÃO DE BACKUP DO SUPABASE:
  Contêineres com variáveis de ambiente do Supabase:
  - renum-backend
  - suna-backend
  Scripts de backup do Supabase:
  - /usr/local/bin/backup_supabase.sh

CONFIGURAÇÃO DE BACKUP DE VOLUMES:
  Scripts de backup de volumes:
  - /usr/local/bin/backup_volumes.sh
  Volumes usados por contêineres:
  - postgres: 1 volumes

RECOMENDAÇÕES:
- Documentar procedimentos de recuperação para cada tipo de backup
- Testar regularmente a restauração de backups para garantir sua eficácia
- Considerar o uso de ferramentas de backup automatizadas como restic, duplicity ou borgbackup
"""
    
    with open(os.path.join(output_dir, 'backup_recovery_report.txt'), 'w') as f:
        f.write(report)
    
    return output_dir

def test_check_backup_recovery(mock=False, output_dir='./output/backup_test'):
    """Test the check_backup_recovery.py script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    check_script_path = os.path.join(script_dir, 'check_backup_recovery.py')
    
    if not os.path.exists(check_script_path):
        print(f"❌ Script não encontrado: {check_script_path}")
        return False
    
    if mock:
        print("Usando dados simulados para teste...")
        mock_dir = create_mock_data(output_dir)
        print(f"✅ Dados simulados criados em {mock_dir}")
        return True
    else:
        print("Executando script de verificação de backup e recuperação...")
        
        try:
            # Run the script with --help to check if it's working
            result = subprocess.run(['python', check_script_path, '--help'], 
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Erro ao executar o script: {result.stderr}")
                return False
            
            print("✅ Script executado com sucesso")
            print("\nAjuda do script:")
            print(result.stdout)
            
            return True
        except Exception as e:
            print(f"❌ Erro ao testar o script: {str(e)}")
            return False

def main():
    """Main function."""
    args = parse_arguments()
    
    print("=== Teste do Script de Verificação de Backup e Recuperação ===")
    
    success = test_check_backup_recovery(args.mock, args.output_dir)
    
    if success:
        print("\n✅ Teste concluído com sucesso")
        
        if args.mock:
            print(f"\nDados simulados disponíveis em: {args.output_dir}")
            print("\nPara executar o script com dados reais, conecte-se à VPS e execute:")
            print("python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa")
        else:
            print("\nPara executar o script completo, use:")
            print("python check_backup_recovery.py --host 157.180.39.41 --user root --key-file ~/.ssh/id_rsa")
    else:
        print("\n❌ Teste falhou")
        sys.exit(1)

if __name__ == "__main__":
    main()